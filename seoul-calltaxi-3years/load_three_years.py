from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path

import pymysql
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = BASE_DIR / "data" / "processed"

load_dotenv(BASE_DIR / ".env")

YEARS = (2023, 2024, 2025)

COLUMN_NAMES = [
    "source_year",
    "source_row_no",
    "request_at",
    "scheduled_at",
    "dispatch_at",
    "pickup_at",
    "dropoff_at",
    "cancel_at",
    "origin_district_raw",
    "origin_dong_raw",
    "destination_district_raw",
    "destination_dong_raw",
    "purpose_raw",
    "purpose_group",
    "reservation_type",
    "is_reserved",
    "fare",
    "distance_meter",
    "distance_km",
    "vehicle_type",
    "disability_type_raw",
    "disability_type_group",
    "trip_status",
    "origin_is_seoul",
    "destination_is_seoul",
    "route_type",
    "request_date",
    "request_year",
    "request_month",
    "request_hour",
    "request_weekday_num",
    "scheduled_date",
    "scheduled_hour",
    "scheduled_weekday_num",
    "dispatch_wait_min",
    "pickup_wait_from_request_min",
    "pickup_delay_from_schedule_min",
    "dispatch_to_pickup_min",
    "trip_duration_min",
    "time_order_error_flag",
    "extreme_dispatch_wait_flag",
    "extreme_pickup_wait_flag",
    "extreme_dispatch_to_pickup_flag",
    "extreme_trip_duration_flag",
    "completed_missing_fare_flag",
    "completed_zero_distance_flag",
    "extreme_fare_flag",
    "extreme_distance_flag",
    "valid_dispatch_wait_flag",
    "valid_schedule_delay_flag",
    "valid_trip_duration_flag",
    "valid_fare_flag",
    "valid_distance_flag",
]


def require_environment() -> None:
    required = [
        "DB_HOST",
        "DB_USER",
        "DB_PASSWORD",
        "DB_NAME",
    ]
    missing = [
        name
        for name in required
        if not os.getenv(name)
    ]
    if missing:
        raise RuntimeError(
            f".env에 필요한 값이 없습니다: {missing}"
        )

    if os.environ["DB_NAME"] != "seoul_calltaxi_3yr":
        raise RuntimeError(
            "안전 중단: DB_NAME은 "
            "'seoul_calltaxi_3yr'이어야 합니다. "
            f"현재 값: {os.environ['DB_NAME']}"
        )


def get_connection():
    return pymysql.connect(
        host=os.environ["DB_HOST"],
        port=int(os.getenv("DB_PORT", "3306")),
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
        database=os.environ["DB_NAME"],
        charset="utf8mb4",
        autocommit=False,
        local_infile=True,
        connect_timeout=30,
        read_timeout=7200,
        write_timeout=7200,
    )


def validate_csv_header(csv_path: Path) -> None:
    with csv_path.open(
        "r",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        reader = csv.reader(file)
        header = next(reader, None)

    if header != COLUMN_NAMES:
        raise ValueError(
            f"CSV 컬럼이 DB 적재 구조와 다릅니다.\n"
            f"파일: {csv_path}\n"
            f"예상: {COLUMN_NAMES}\n"
            f"실제: {header}"
        )


def validate_database(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT DATABASE()"
        )
        selected_database = cursor.fetchone()[0]

        if selected_database != "seoul_calltaxi_3yr":
            raise RuntimeError(
                "안전 중단: 연결된 DB가 다릅니다. "
                f"현재 DB: {selected_database}"
            )

        cursor.execute(
            "SHOW GLOBAL VARIABLES LIKE 'local_infile'"
        )
        local_infile = cursor.fetchone()

        if (
            local_infile is None
            or str(local_infile[1]).upper() != "ON"
        ):
            raise RuntimeError(
                "MySQL local_infile이 ON이 아닙니다."
            )

        cursor.execute("SHOW COLUMNS FROM taxi_trip")
        actual_columns = {
            row[0]
            for row in cursor.fetchall()
        }
        missing_columns = [
            column
            for column in COLUMN_NAMES
            if column not in actual_columns
        ]

        if missing_columns:
            raise RuntimeError(
                "taxi_trip 테이블에 필요한 컬럼이 없습니다: "
                f"{missing_columns}"
            )


def build_load_sql() -> str:
    input_variables = ",\n".join(
        f"@v_{column}"
        for column in COLUMN_NAMES
    )
    assignments = ",\n".join(
        f"`{column}` = "
        f"NULLIF(@v_{column}, '\\\\N')"
        for column in COLUMN_NAMES
    )

    return f"""
        LOAD DATA LOCAL INFILE %s
        INTO TABLE taxi_trip
        CHARACTER SET utf8mb4
        FIELDS TERMINATED BY ','
        OPTIONALLY ENCLOSED BY '"'
        ESCAPED BY '"'
        LINES TERMINATED BY '\\n'
        IGNORE 1 LINES
        (
            {input_variables}
        )
        SET
            {assignments}
    """


def start_load_log(
    connection,
    year: int,
    csv_path: Path,
) -> int:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO data_load_log (
                source_year,
                source_file,
                load_status,
                started_at
            )
            VALUES (%s, %s, 'RUNNING', %s)
            """,
            (
                year,
                str(csv_path),
                datetime.now(),
            ),
        )
        load_id = cursor.lastrowid

    connection.commit()
    return load_id


def mark_load_failed(
    connection,
    load_id: int,
    error: Exception,
) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE data_load_log
            SET load_status = 'FAILED',
                finished_at = %s,
                error_message = %s
            WHERE load_id = %s
            """,
            (
                datetime.now(),
                str(error)[:65000],
                load_id,
            ),
        )
    connection.commit()


def load_year(connection, year: int) -> None:
    csv_path = (
        PROCESSED_DIR
        / f"taxi_trip_cleaned_{year}.csv"
    ).resolve()

    if not csv_path.exists():
        raise FileNotFoundError(csv_path)

    validate_csv_header(csv_path)
    load_id = start_load_log(
        connection,
        year,
        csv_path,
    )
    load_sql = build_load_sql()

    print("=" * 70)
    print(f"{year}년 적재 시작")
    print(f"파일: {csv_path}")
    print(
        "대용량 적재 중에는 출력이 잠시 멈출 수 있습니다. "
        "터미널을 닫지 마세요."
    )

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM taxi_trip
                WHERE source_year = %s
                """,
                (year,),
            )

            cursor.execute(load_sql, (str(csv_path),))

            cursor.execute(
                """
                SELECT
                    COUNT(*) AS loaded_count,
                    MIN(source_row_no) AS min_row_no,
                    MAX(source_row_no) AS max_row_no
                FROM taxi_trip
                WHERE source_year = %s
                """,
                (year,),
            )
            loaded_count, min_row_no, max_row_no = (
                cursor.fetchone()
            )

            if loaded_count == 0:
                raise RuntimeError(
                    f"{year}년 적재 결과가 0행입니다."
                )

            if min_row_no != 1:
                raise RuntimeError(
                    f"{year}년 source_row_no가 1부터 "
                    f"시작하지 않습니다: {min_row_no}"
                )

            if loaded_count != max_row_no:
                raise RuntimeError(
                    f"{year}년 행 번호가 연속적이지 않습니다. "
                    f"행 수={loaded_count:,}, "
                    f"최대 번호={max_row_no:,}"
                )

            cursor.execute(
                """
                UPDATE data_load_log
                SET expected_row_count = %s,
                    loaded_row_count = %s,
                    load_status = 'SUCCESS',
                    finished_at = %s,
                    error_message = NULL
                WHERE load_id = %s
                """,
                (
                    max_row_no,
                    loaded_count,
                    datetime.now(),
                    load_id,
                ),
            )

        connection.commit()
        print(
            f"{year}년 적재 완료: "
            f"{loaded_count:,}행"
        )

    except Exception as error:
        connection.rollback()
        mark_load_failed(connection, load_id, error)
        print(f"{year}년 적재 실패: {error}")
        raise


def print_final_summary(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                source_year,
                COUNT(*) AS total_count,
                MIN(request_at) AS min_request_at,
                MAX(request_at) AS max_request_at
            FROM taxi_trip
            GROUP BY source_year
            ORDER BY source_year
            """
        )
        rows = cursor.fetchall()

    print("=" * 70)
    print("최종 적재 결과")
    for (
        year,
        total_count,
        min_request_at,
        max_request_at,
    ) in rows:
        print(
            f"{year}: {total_count:,}행 "
            f"| {min_request_at} ~ {max_request_at}"
        )


def main() -> None:
    require_environment()
    connection = get_connection()

    try:
        validate_database(connection)
        print(
            "연결 확인 완료: seoul_calltaxi_3yr"
        )

        for year in YEARS:
            load_year(connection, year)

        print_final_summary(connection)
        print("3개년 MySQL 적재가 완료되었습니다.")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
