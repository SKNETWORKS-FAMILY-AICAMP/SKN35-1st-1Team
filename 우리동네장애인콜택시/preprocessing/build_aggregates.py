"""정제된 Parquet(taxi_processed.parquet)으로부터 분석용 집계 테이블을 생성한다.

생성되는 집계(각각 data/processed/aggregates/*.parquet 로 저장, 이후
scripts/load_aggregates.py 가 MySQL로 적재):
  district_daily_stat, district_hourly_stat, weekday_hour_stat,
  monthly_stat, od_flow_stat, purpose_stat, disability_vehicle_stat

사용 예:
    uv run python preprocessing/build_aggregates.py
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from congestion import congestion_level_from_percentile, percentile_rank
from preprocessing.config import PROCESSED_DIR, SMALL_SAMPLE_THRESHOLD

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

RIDE_STATUSES = ["boarded", "completed"]


def _round(value, digits=2):
    return None if value is None or pd.isna(value) else round(float(value), digits)


def _base_counts(g: pd.DataFrame) -> dict:
    status_counts = g["status"].value_counts()
    request_count = len(g)
    dispatch_count = int(status_counts.reindex(["dispatched", "boarded", "completed"], fill_value=0).sum())
    ride_count = int(status_counts.reindex(RIDE_STATUSES, fill_value=0).sum())
    completed_count = int(status_counts.get("completed", 0))
    cancel_count = int(status_counts.get("cancelled", 0))

    valid = g[g["is_valid_row"]]
    dispatch_wait = valid["dispatch_wait_min"].dropna()
    pickup_wait = valid["pickup_wait_min"].dropna()
    distance = valid["distance"].dropna()
    fare = valid["fare"].dropna()

    return {
        "request_count": request_count,
        "dispatch_count": dispatch_count,
        "ride_count": ride_count,
        "completed_count": completed_count,
        "cancel_count": cancel_count,
        "cancel_rate": _round(cancel_count / request_count * 100) if request_count else None,
        "avg_dispatch_wait_min": _round(dispatch_wait.mean()) if len(dispatch_wait) else None,
        "median_dispatch_wait_min": _round(dispatch_wait.median()) if len(dispatch_wait) else None,
        "p75_dispatch_wait_min": _round(dispatch_wait.quantile(0.75)) if len(dispatch_wait) else None,
        "p90_dispatch_wait_min": _round(dispatch_wait.quantile(0.90)) if len(dispatch_wait) else None,
        "avg_pickup_wait_min": _round(pickup_wait.mean()) if len(pickup_wait) else None,
        "median_pickup_wait_min": _round(pickup_wait.median()) if len(pickup_wait) else None,
        "avg_distance": _round(distance.mean()) if len(distance) else None,
        "avg_fare": _round(fare.mean()) if len(fare) else None,
        "valid_wait_count": int(len(dispatch_wait)),
    }


def build_district_daily_stat(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["request_date"].notna() & df["origin_district"].notna()]
    rows = []
    for (stat_date, district_id), g in base.groupby(["request_date", "origin_district"]):
        row = {"stat_date": stat_date, "district_id": district_id}
        row.update(_base_counts(g))
        rows.append(row)
    return pd.DataFrame(rows)


def build_district_hourly_stat(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["origin_district"].notna() & df["weekday_num"].notna() & df["request_hour"].notna()]
    rows = []
    for (district_id, weekday_num, request_hour), g in base.groupby(["origin_district", "weekday_num", "request_hour"]):
        row = {"district_id": district_id, "weekday_num": int(weekday_num), "request_hour": int(request_hour)}
        row.update(_base_counts(g))
        rows.append(row)
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # 혼잡도는 "같은 자치구 내에서 이 요일x시간이 상대적으로 얼마나 바쁜가"를 기준으로 산정한다.
    out["congestion_percentile"] = out.groupby("district_id")["request_count"].transform(percentile_rank).round(2)
    out["congestion_level"] = out["congestion_percentile"].map(congestion_level_from_percentile)
    return out


def build_weekday_hour_stat(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["weekday_num"].notna() & df["request_hour"].notna()]
    rows = []
    for (weekday_num, request_hour), g in base.groupby(["weekday_num", "request_hour"]):
        counts = _base_counts(g)
        rows.append({
            "weekday_num": int(weekday_num),
            "request_hour": int(request_hour),
            "request_count": counts["request_count"],
            "ride_count": counts["ride_count"],
            "cancel_count": counts["cancel_count"],
            "avg_dispatch_wait_min": counts["avg_dispatch_wait_min"],
            "median_dispatch_wait_min": counts["median_dispatch_wait_min"],
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    # 전체(자치구 무관) 기준 분위수: 혼잡도 대체조회의 마지막 단계(요일+시간)에서 사용.
    out["congestion_percentile"] = percentile_rank(out["request_count"]).round(2)
    out["congestion_level"] = out["congestion_percentile"].map(congestion_level_from_percentile)
    return out


def build_monthly_stat(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["request_year"].notna() & df["request_month"].notna()]
    rows = []
    for (year, month), g in base.groupby(["request_year", "request_month"]):
        counts = _base_counts(g)
        rows.append({
            "year": int(year),
            "month": int(month),
            "request_count": counts["request_count"],
            "ride_count": counts["ride_count"],
            "completed_count": counts["completed_count"],
            "cancel_count": counts["cancel_count"],
            "cancel_rate": counts["cancel_rate"],
            "avg_dispatch_wait_min": counts["avg_dispatch_wait_min"],
            "median_dispatch_wait_min": counts["median_dispatch_wait_min"],
            "avg_pickup_wait_min": counts["avg_pickup_wait_min"],
        })
    return pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)


def build_od_flow_stat(df: pd.DataFrame) -> pd.DataFrame:
    base = df[df["origin_district"].notna() & df["destination_district"].notna()]
    rows = []
    for (origin, destination), g in base.groupby(["origin_district", "destination_district"]):
        status_counts = g["status"].value_counts()
        valid = g[g["is_valid_row"]]
        trip_duration = valid["trip_duration_min"].dropna()
        rows.append({
            "origin_district_id": origin,
            "destination_district_id": destination,
            "request_count": len(g),
            "ride_count": int(status_counts.reindex(RIDE_STATUSES, fill_value=0).sum()),
            "avg_distance": _round(valid["distance"].dropna().mean()) if not valid["distance"].dropna().empty else None,
            "avg_fare": _round(valid["fare"].dropna().mean()) if not valid["fare"].dropna().empty else None,
            "avg_trip_duration_min": _round(trip_duration.mean()) if len(trip_duration) else None,
        })
    return pd.DataFrame(rows)


def _purpose_rows(g: pd.DataFrame, district_id: str, total: int) -> list[dict]:
    rows = []
    for purpose_group, gg in g.groupby("purpose_group"):
        status_counts = gg["status"].value_counts()
        valid = gg[gg["is_valid_row"]]
        rows.append({
            "district_id": district_id,
            "purpose_group": purpose_group,
            "request_count": len(gg),
            "ride_count": int(status_counts.reindex(RIDE_STATUSES, fill_value=0).sum()),
            "percentage": _round(len(gg) / total * 100) if total else None,
            "avg_distance": _round(valid["distance"].dropna().mean()) if not valid["distance"].dropna().empty else None,
            "avg_fare": _round(valid["fare"].dropna().mean()) if not valid["fare"].dropna().empty else None,
        })
    return rows


def build_purpose_stat(df: pd.DataFrame) -> pd.DataFrame:
    """district_id='ALL'(서울 전체) 행과, 자치구 상세정보 화면에서 쓰는
    자치구별 행(district_id=출발구)을 함께 생성한다."""
    rows = _purpose_rows(df, "ALL", len(df))

    with_origin = df[df["origin_district"].notna()]
    for district_id, g in with_origin.groupby("origin_district"):
        rows.extend(_purpose_rows(g, district_id, len(g)))

    return pd.DataFrame(rows)


def build_disability_vehicle_stat(df: pd.DataFrame, small_sample_threshold: int = SMALL_SAMPLE_THRESHOLD) -> pd.DataFrame:
    """표본이 SMALL_SAMPLE_THRESHOLD 미만인 (장애유형,차량구분) 조합은 '기타(소규모)'로 묶어
    화면에서 개별 식별이 되지 않도록 한다."""
    ridden = df[df["status"].isin(RIDE_STATUSES)]
    if ridden.empty:
        return pd.DataFrame(columns=["disability_type", "vehicle_type", "ride_count", "percentage"])

    raw = ridden.groupby(["disability_type_group", "vehicle_type_group"]).size().reset_index(name="ride_count")
    small_mask = raw["ride_count"] < small_sample_threshold
    raw.loc[small_mask, "disability_type_group"] = "기타(소규모)"
    merged = raw.groupby(["disability_type_group", "vehicle_type_group"], as_index=False)["ride_count"].sum()
    total = merged["ride_count"].sum()
    merged["percentage"] = merged["ride_count"].apply(lambda v: _round(v / total * 100) if total else None)
    return merged.rename(columns={"disability_type_group": "disability_type", "vehicle_type_group": "vehicle_type"})


AGGREGATE_BUILDERS = {
    "district_daily_stat": build_district_daily_stat,
    "district_hourly_stat": build_district_hourly_stat,
    "weekday_hour_stat": build_weekday_hour_stat,
    "monthly_stat": build_monthly_stat,
    "od_flow_stat": build_od_flow_stat,
    "purpose_stat": build_purpose_stat,
    "disability_vehicle_stat": build_disability_vehicle_stat,
}


def build_all(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    return {name: builder(df) for name, builder in AGGREGATE_BUILDERS.items()}


def save_aggregates(aggregates: dict[str, pd.DataFrame], out_dir: str) -> None:
    out_path = Path(out_dir) / "aggregates"
    out_path.mkdir(parents=True, exist_ok=True)
    for name, agg_df in aggregates.items():
        path = out_path / f"{name}.parquet"
        agg_df.to_parquet(path, index=False)
        logger.info("집계 저장: %s (%d행)", path, len(agg_df))


def main() -> None:
    parser = argparse.ArgumentParser(description="정제 데이터로부터 분석 집계 테이블 생성")
    parser.add_argument("--processed-dir", type=str, default=PROCESSED_DIR)
    args = parser.parse_args()

    parquet_path = Path(args.processed_dir) / "taxi_processed.parquet"
    if not parquet_path.exists():
        logger.error("정제 데이터가 없습니다. 먼저 clean_taxi_data.py 를 실행하세요: %s", parquet_path)
        raise SystemExit(1)

    df = pd.read_parquet(parquet_path)
    aggregates = build_all(df)
    save_aggregates(aggregates, args.processed_dir)


if __name__ == "__main__":
    main()
