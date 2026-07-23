from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

DATETIME_COLUMNS = [
    "접수일시",
    "예정일시",
    "배차일시",
    "승차일시",
    "하차일시",
    "취소일시",
]
TEXT_COLUMNS = [
    "출발구",
    "출발동",
    "목적구",
    "목적동",
    "이용목적",
    "차량구분",
    "장애유형",
]
REQUIRED_COLUMNS = DATETIME_COLUMNS + TEXT_COLUMNS + ["요금", "승차거리"]

WEEKDAY_NAMES = {
    0: "월요일",
    1: "화요일",
    2: "수요일",
    3: "목요일",
    4: "금요일",
    5: "토요일",
    6: "일요일",
}


def clean_text(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().replace({"": pd.NA})


def parse_datetime(series: pd.Series) -> pd.Series:
    # 공공데이터 원본 형식 예: 2025-01-01 00:01:26.127
    return pd.to_datetime(
        series,
        format="%Y-%m-%d %H:%M:%S.%f",
        errors="coerce",
    )


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    return numerator / denominator.replace(0, np.nan)


def aggregate_metrics(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=keys)

    return (
        df.groupby(keys, dropna=False)
        .agg(
            trip_count=("완료여부", "size"),
            fare_sum=("요금_num", "sum"),
            fare_count=("요금_num", "count"),
            distance_m_sum=("승차거리_m", "sum"),
            distance_count=("승차거리_m", "count"),
            request_to_dispatch_min_sum=("접수후배차_분", "sum"),
            request_to_dispatch_count=("접수후배차_분", "count"),
            scheduled_to_pickup_min_sum=("예정대비승차_분", "sum"),
            scheduled_to_pickup_count=("예정대비승차_분", "count"),
            ride_min_sum=("승차시간_분", "sum"),
            ride_min_count=("승차시간_분", "count"),
        )
        .reset_index()
    )


def aggregate_status(df: pd.DataFrame, keys: list[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=keys)

    return (
        df.groupby(keys, dropna=False)
        .agg(
            total_record_count=("완료여부", "size"),
            completed_count=("완료여부", "sum"),
            cancelled_count=("취소여부", "sum"),
        )
        .reset_index()
    )


def combine_sums(frames: Iterable[pd.DataFrame], keys: list[str]) -> pd.DataFrame:
    usable = [frame for frame in frames if not frame.empty]
    if not usable:
        return pd.DataFrame(columns=keys)

    return (
        pd.concat(usable, ignore_index=True)
        .groupby(keys, dropna=False, as_index=False)
        .sum(numeric_only=True)
    )


def finalize_metrics(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    df = df.copy()
    df["avg_fare"] = safe_divide(df["fare_sum"], df["fare_count"])
    df["avg_distance_m"] = safe_divide(
        df["distance_m_sum"], df["distance_count"]
    )
    df["avg_distance_km"] = df["avg_distance_m"] / 1000
    df["avg_request_to_dispatch_min"] = safe_divide(
        df["request_to_dispatch_min_sum"],
        df["request_to_dispatch_count"],
    )
    df["avg_scheduled_to_pickup_min"] = safe_divide(
        df["scheduled_to_pickup_min_sum"],
        df["scheduled_to_pickup_count"],
    )
    df["avg_ride_min"] = safe_divide(
        df["ride_min_sum"], df["ride_min_count"]
    )
    return df


def process_file(
    file_path: Path,
    output_dir: Path,
    chunk_size: int,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    district_daily_parts: list[pd.DataFrame] = []
    hourly_parts: list[pd.DataFrame] = []
    od_parts: list[pd.DataFrame] = []
    purpose_parts: list[pd.DataFrame] = []
    disability_vehicle_parts: list[pd.DataFrame] = []
    status_parts: list[pd.DataFrame] = []

    totals = {
        "total_records": 0,
        "completed_records": 0,
        "cancelled_records": 0,
        "completed_and_cancelled_records": 0,
        "missing_scheduled_datetime": 0,
        "invalid_negative_ride_time": 0,
        "invalid_negative_request_to_dispatch": 0,
    }

    reader = pd.read_csv(
        file_path,
        encoding="utf-8-sig",
        dtype="string",
        chunksize=chunk_size,
        usecols=REQUIRED_COLUMNS,
        on_bad_lines="warn",
    )

    for chunk_number, chunk in enumerate(reader, start=1):
        missing = sorted(set(REQUIRED_COLUMNS) - set(chunk.columns))
        if missing:
            raise ValueError(f"필수 컬럼이 없습니다: {missing}")

        for column in TEXT_COLUMNS:
            chunk[column] = clean_text(chunk[column])

        for column in DATETIME_COLUMNS:
            chunk[column] = parse_datetime(chunk[column])

        chunk["요금_num"] = pd.to_numeric(chunk["요금"], errors="coerce")
        chunk["승차거리_m"] = pd.to_numeric(
            chunk["승차거리"], errors="coerce"
        )

        # 원본은 예정일시 기준 연간 자료이므로 분석 기준일도 예정일시를 사용합니다.
        chunk["기준일"] = chunk["예정일시"].dt.normalize()
        chunk["요일번호"] = chunk["예정일시"].dt.dayofweek.astype("Int64")
        chunk["시간대"] = chunk["예정일시"].dt.hour.astype("Int64")

        chunk["완료여부"] = (
            chunk["승차일시"].notna() & chunk["하차일시"].notna()
        )
        chunk["취소여부"] = chunk["취소일시"].notna()

        chunk["접수후배차_분"] = (
            chunk["배차일시"] - chunk["접수일시"]
        ).dt.total_seconds() / 60
        chunk["예정대비승차_분"] = (
            chunk["승차일시"] - chunk["예정일시"]
        ).dt.total_seconds() / 60
        chunk["승차시간_분"] = (
            chunk["하차일시"] - chunk["승차일시"]
        ).dt.total_seconds() / 60

        totals["total_records"] += len(chunk)
        totals["completed_records"] += int(chunk["완료여부"].sum())
        totals["cancelled_records"] += int(chunk["취소여부"].sum())
        totals["completed_and_cancelled_records"] += int(
            (chunk["완료여부"] & chunk["취소여부"]).sum()
        )
        totals["missing_scheduled_datetime"] += int(
            chunk["예정일시"].isna().sum()
        )
        totals["invalid_negative_ride_time"] += int(
            (chunk["승차시간_분"] < 0).sum()
        )
        totals["invalid_negative_request_to_dispatch"] += int(
            (chunk["접수후배차_분"] < 0).sum()
        )

        # 완료 운행 통계: 승차일시와 하차일시가 모두 있는 레코드
        completed = chunk.loc[chunk["완료여부"]].copy()

        district_daily_parts.append(
            aggregate_metrics(completed, ["기준일", "출발구"])
        )
        hourly_parts.append(
            aggregate_metrics(completed, ["요일번호", "시간대"])
        )
        od_parts.append(
            aggregate_metrics(completed, ["출발구", "목적구"])
        )
        purpose_parts.append(
            aggregate_metrics(completed, ["이용목적"])
        )
        disability_vehicle_parts.append(
            aggregate_metrics(completed, ["장애유형", "차량구분"])
        )
        status_parts.append(
            aggregate_status(chunk, ["기준일", "출발구"])
        )

        print(
            f"[{chunk_number:02d}] "
            f"누적 {totals['total_records']:,}건 처리 완료"
        )

    district_daily = finalize_metrics(
        combine_sums(district_daily_parts, ["기준일", "출발구"])
    )
    hourly = finalize_metrics(
        combine_sums(hourly_parts, ["요일번호", "시간대"])
    )
    od_flow = finalize_metrics(
        combine_sums(od_parts, ["출발구", "목적구"])
    )
    purpose = finalize_metrics(
        combine_sums(purpose_parts, ["이용목적"])
    )
    disability_vehicle = finalize_metrics(
        combine_sums(
            disability_vehicle_parts,
            ["장애유형", "차량구분"],
        )
    )
    status = combine_sums(status_parts, ["기준일", "출발구"])

    if not hourly.empty:
        hourly["요일명"] = hourly["요일번호"].map(WEEKDAY_NAMES)

    if not district_daily.empty and not status.empty:
        district_daily = district_daily.merge(
            status,
            on=["기준일", "출발구"],
            how="outer",
        )
        district_daily["completion_rate"] = safe_divide(
            district_daily["completed_count"],
            district_daily["total_record_count"],
        )
        district_daily["cancellation_rate"] = safe_divide(
            district_daily["cancelled_count"],
            district_daily["total_record_count"],
        )

    outputs = {
        "district_daily_stat.csv": district_daily,
        "weekday_hour_stat.csv": hourly,
        "od_flow_stat.csv": od_flow,
        "purpose_stat.csv": purpose,
        "disability_vehicle_stat.csv": disability_vehicle,
    }

    for filename, dataframe in outputs.items():
        path = output_dir / filename
        dataframe.to_csv(path, index=False, encoding="utf-8-sig")
        print(f"저장: {path} ({len(dataframe):,}행)")

    profile_path = output_dir / "processing_summary.json"
    profile_path.write_text(
        json.dumps(totals, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"저장: {profile_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="서울 장애인콜택시 대용량 CSV를 청크 단위로 집계합니다."
    )
    parser.add_argument("file", type=Path, help="원본 CSV 경로")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("taxi_processed"),
        help="결과 저장 폴더",
    )
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=100_000,
        help="한 번에 읽을 행 수",
    )
    args = parser.parse_args()

    if not args.file.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {args.file}")

    process_file(args.file, args.output_dir, args.chunk_size)


if __name__ == "__main__":
    main()
