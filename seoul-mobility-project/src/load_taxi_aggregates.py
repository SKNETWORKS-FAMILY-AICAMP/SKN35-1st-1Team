from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Iterable

import pandas as pd
import pymysql
from dotenv import load_dotenv
from pymysql.connections import Connection


SEOUL_DISTRICTS = {
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구",
}

METRIC_COLUMNS = [
    "trip_count",
    "fare_sum",
    "fare_count",
    "distance_m_sum",
    "distance_count",
    "request_to_dispatch_min_sum",
    "request_to_dispatch_count",
    "scheduled_to_pickup_min_sum",
    "scheduled_to_pickup_count",
    "ride_min_sum",
    "ride_min_count",
    "avg_fare",
    "avg_distance_m",
    "avg_distance_km",
    "avg_request_to_dispatch_min",
    "avg_scheduled_to_pickup_min",
    "avg_ride_min",
]

# DB에서 NOT NULL이고, 값이 없을 때 0이 의미상 맞는 합계/건수 컬럼
ZERO_FILL_METRIC_COLUMNS = [
    "trip_count",
    "fare_sum",
    "fare_count",
    "distance_m_sum",
    "distance_count",
    "request_to_dispatch_min_sum",
    "request_to_dispatch_count",
    "scheduled_to_pickup_min_sum",
    "scheduled_to_pickup_count",
    "ride_min_sum",
    "ride_min_count",
]

ZERO_FILL_STATUS_COLUMNS = [
    "total_record_count",
    "completed_count",
    "cancelled_count",
]

FILE_NAMES = {
    "district_daily": "district_daily_stat.csv",
    "weekday_hour": "weekday_hour_stat.csv",
    "od_flow": "od_flow_stat.csv",
    "purpose": "purpose_stat.csv",
    "disability_vehicle": "disability_vehicle_stat.csv",
}


def infer_area_type(name: str) -> str:
    if name.endswith("구"):
        return "구"
    if name.endswith("시"):
        return "시"
    if name.endswith("군"):
        return "군"
    return "기타"


def normalize_area_series(series: pd.Series) -> pd.Series:
    """공백·결측 지역명을 '미상'으로 통일합니다."""
    return (
        series.astype("string")
        .str.strip()
        .replace("", pd.NA)
        .fillna("미상")
    )


def fill_required_numeric_zeros(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """합계·건수 컬럼의 결측값을 0으로 변환합니다."""
    dataframe = dataframe.copy()
    existing = [column for column in columns if column in dataframe.columns]
    for column in existing:
        dataframe[column] = pd.to_numeric(
            dataframe[column],
            errors="coerce",
        ).fillna(0)
    return dataframe


def python_value(value: Any) -> Any:
    """numpy/pandas 값을 PyMySQL이 처리할 수 있는 기본 Python 값으로 변환합니다."""
    if pd.isna(value):
        return None

    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()

    if hasattr(value, "item"):
        try:
            return value.item()
        except (ValueError, AttributeError):
            pass

    return value


def dataframe_rows(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> Iterable[tuple[Any, ...]]:
    for row in dataframe[columns].itertuples(index=False, name=None):
        yield tuple(python_value(value) for value in row)


def connect_database() -> Connection:
    load_dotenv()

    required = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
    ]
    missing = [name for name in required if not os.getenv(name)]
    if missing:
        raise RuntimeError(
            ".env 파일에서 다음 설정을 찾지 못했습니다: "
            + ", ".join(missing)
        )

    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.environ["DB_PORT"]),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.DictCursor,
    )


def validate_files(input_dir: Path) -> dict[str, Path]:
    paths = {
        key: input_dir / filename
        for key, filename in FILE_NAMES.items()
    }
    missing = [str(path) for path in paths.values() if not path.exists()]
    if missing:
        raise FileNotFoundError(
            "다음 집계 파일을 찾을 수 없습니다:\n- "
            + "\n- ".join(missing)
        )
    return paths


def load_csv(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig", low_memory=False)


def collect_area_names(paths: dict[str, Path]) -> set[str]:
    daily = pd.read_csv(
        paths["district_daily"],
        encoding="utf-8-sig",
        usecols=["출발구"],
        dtype="string",
    )
    od = pd.read_csv(
        paths["od_flow"],
        encoding="utf-8-sig",
        usecols=["출발구", "목적구"],
        dtype="string",
    )

    names: set[str] = set()
    for column in [daily["출발구"], od["출발구"], od["목적구"]]:
        values = normalize_area_series(column)
        names.update(values.tolist())

    return names


def upsert_areas(
    connection: Connection,
    area_names: set[str],
) -> dict[str, int]:
    sql = """
        INSERT INTO district (
            district_name,
            is_seoul,
            area_type
        )
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE
            is_seoul = VALUES(is_seoul),
            area_type = VALUES(area_type)
    """

    values = [
        (
            name,
            1 if name in SEOUL_DISTRICTS else 0,
            infer_area_type(name),
        )
        for name in sorted(area_names)
    ]

    with connection.cursor() as cursor:
        cursor.executemany(sql, values)
        cursor.execute(
            "SELECT district_id, district_name FROM district"
        )
        rows = cursor.fetchall()

    mapping = {
        row["district_name"]: row["district_id"]
        for row in rows
    }

    unmapped = sorted(area_names - set(mapping))
    if unmapped:
        raise RuntimeError(f"지역 ID 생성 실패: {unmapped}")

    print(
        f"지역 기준정보 준비 완료: "
        f"CSV 내 고유 지역 {len(area_names):,}개"
    )
    return mapping


def clear_stat_tables(connection: Connection) -> None:
    tables = [
        "district_daily_stat",
        "weekday_hour_stat",
        "od_flow_stat",
        "purpose_stat",
        "disability_vehicle_stat",
    ]
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"DELETE FROM {table}")
    print("기존 집계 테이블 데이터 삭제 완료")


def upsert_dataframe(
    connection: Connection,
    table: str,
    dataframe: pd.DataFrame,
    columns: list[str],
    primary_key_columns: set[str],
    batch_size: int = 1_000,
) -> None:
    update_columns = [
        column
        for column in columns
        if column not in primary_key_columns
    ]

    placeholders = ", ".join(["%s"] * len(columns))
    column_sql = ", ".join(f"`{column}`" for column in columns)
    update_sql = ", ".join(
        f"`{column}` = VALUES(`{column}`)"
        for column in update_columns
    )

    sql = (
        f"INSERT INTO `{table}` ({column_sql}) "
        f"VALUES ({placeholders}) "
        f"ON DUPLICATE KEY UPDATE {update_sql}"
    )

    rows = list(dataframe_rows(dataframe, columns))

    with connection.cursor() as cursor:
        for start in range(0, len(rows), batch_size):
            batch = rows[start : start + batch_size]
            cursor.executemany(sql, batch)

    print(f"{table}: {len(rows):,}행 적재 완료")


def prepare_district_daily(
    path: Path,
    area_map: dict[str, int],
) -> pd.DataFrame:
    df = load_csv(path)
    df = df.rename(
        columns={
            "기준일": "stat_date",
            "출발구": "origin_district_name",
        }
    )
    df["stat_date"] = pd.to_datetime(
        df["stat_date"],
        errors="raise",
    ).dt.date
    df["origin_district_name"] = normalize_area_series(
        df["origin_district_name"]
    )
    df["origin_district_id"] = df[
        "origin_district_name"
    ].map(area_map)

    if df["origin_district_id"].isna().any():
        names = sorted(
            df.loc[
                df["origin_district_id"].isna(),
                "origin_district_name",
            ].dropna().unique()
        )
        raise ValueError(f"매핑되지 않은 출발지역: {names}")

    # 취소만 있고 완료 운행이 없는 날짜·지역은 trip_count 등이 NaN일 수 있습니다.
    # 합계/건수는 0으로, 평균값은 계산 불가이므로 NULL 상태를 유지합니다.
    df = fill_required_numeric_zeros(
        df,
        ZERO_FILL_METRIC_COLUMNS + ZERO_FILL_STATUS_COLUMNS,
    )

    columns = [
        "stat_date",
        "origin_district_id",
        *METRIC_COLUMNS,
        "total_record_count",
        "completed_count",
        "cancelled_count",
        "completion_rate",
        "cancellation_rate",
    ]
    return df[columns]


def prepare_weekday_hour(path: Path) -> pd.DataFrame:
    df = load_csv(path)
    df = df.rename(
        columns={
            "요일번호": "weekday_number",
            "요일명": "weekday_name",
            "시간대": "hour_of_day",
        }
    )
    df = fill_required_numeric_zeros(
        df,
        ZERO_FILL_METRIC_COLUMNS,
    )
    columns = [
        "weekday_number",
        "weekday_name",
        "hour_of_day",
        *METRIC_COLUMNS,
    ]
    return df[columns]


def prepare_od_flow(
    path: Path,
    area_map: dict[str, int],
) -> pd.DataFrame:
    df = load_csv(path)
    df = df.rename(
        columns={
            "출발구": "origin_district_name",
            "목적구": "destination_name",
        }
    )
    df["origin_district_name"] = normalize_area_series(
        df["origin_district_name"]
    )
    df["destination_name"] = normalize_area_series(
        df["destination_name"]
    )
    df["origin_district_id"] = df[
        "origin_district_name"
    ].map(area_map)

    if df["origin_district_id"].isna().any():
        names = sorted(
            df.loc[
                df["origin_district_id"].isna(),
                "origin_district_name",
            ].dropna().unique()
        )
        raise ValueError(f"매핑되지 않은 출발지역: {names}")

    df = fill_required_numeric_zeros(
        df,
        ZERO_FILL_METRIC_COLUMNS,
    )
    columns = [
        "origin_district_id",
        "destination_name",
        *METRIC_COLUMNS,
    ]
    return df[columns]


def prepare_purpose(path: Path) -> pd.DataFrame:
    df = load_csv(path)
    df = df.rename(columns={"이용목적": "purpose_name"})
    df["purpose_name"] = (
        df["purpose_name"]
        .astype("string")
        .fillna("미상")
        .str.strip()
    )
    df = fill_required_numeric_zeros(
        df,
        ZERO_FILL_METRIC_COLUMNS,
    )
    return df[["purpose_name", *METRIC_COLUMNS]]


def prepare_disability_vehicle(path: Path) -> pd.DataFrame:
    df = load_csv(path)
    df = df.rename(
        columns={
            "장애유형": "disability_type",
            "차량구분": "vehicle_type",
        }
    )
    df["disability_type"] = (
        df["disability_type"]
        .astype("string")
        .fillna("미상")
        .str.strip()
    )
    df["vehicle_type"] = (
        df["vehicle_type"]
        .astype("string")
        .fillna("미상")
        .str.strip()
    )
    df = fill_required_numeric_zeros(
        df,
        ZERO_FILL_METRIC_COLUMNS,
    )
    return df[
        ["disability_type", "vehicle_type", *METRIC_COLUMNS]
    ]


def verify_counts(connection: Connection) -> None:
    tables = [
        "district",
        "district_daily_stat",
        "weekday_hour_stat",
        "od_flow_stat",
        "purpose_stat",
        "disability_vehicle_stat",
    ]
    print("\n[DB 적재 결과]")
    with connection.cursor() as cursor:
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) AS count FROM `{table}`")
            count = cursor.fetchone()["count"]
            print(f"- {table}: {count:,}행")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="전처리된 장애인콜택시 집계 CSV를 MySQL에 적재합니다."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("taxi_processed"),
        help="집계 CSV가 들어 있는 폴더",
    )
    parser.add_argument(
        "--keep-existing",
        action="store_true",
        help="기존 통계 데이터를 삭제하지 않고 upsert합니다.",
    )
    args = parser.parse_args()

    paths = validate_files(args.input_dir)
    connection = connect_database()

    try:
        area_names = collect_area_names(paths)
        area_map = upsert_areas(connection, area_names)

        if not args.keep_existing:
            clear_stat_tables(connection)

        district_daily = prepare_district_daily(
            paths["district_daily"],
            area_map,
        )
        weekday_hour = prepare_weekday_hour(
            paths["weekday_hour"]
        )
        od_flow = prepare_od_flow(
            paths["od_flow"],
            area_map,
        )
        purpose = prepare_purpose(paths["purpose"])
        disability_vehicle = prepare_disability_vehicle(
            paths["disability_vehicle"]
        )

        upsert_dataframe(
            connection,
            "district_daily_stat",
            district_daily,
            list(district_daily.columns),
            {"stat_date", "origin_district_id"},
        )
        upsert_dataframe(
            connection,
            "weekday_hour_stat",
            weekday_hour,
            list(weekday_hour.columns),
            {"weekday_number", "hour_of_day"},
        )
        upsert_dataframe(
            connection,
            "od_flow_stat",
            od_flow,
            list(od_flow.columns),
            {"origin_district_id", "destination_name"},
        )
        upsert_dataframe(
            connection,
            "purpose_stat",
            purpose,
            list(purpose.columns),
            {"purpose_name"},
        )
        upsert_dataframe(
            connection,
            "disability_vehicle_stat",
            disability_vehicle,
            list(disability_vehicle.columns),
            {"disability_type", "vehicle_type"},
        )

        connection.commit()
        verify_counts(connection)
        print("\n모든 집계 데이터가 정상적으로 적재됐습니다.")

    except Exception:
        connection.rollback()
        print("\n오류가 발생해 이번 작업을 롤백했습니다.")
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    main()
