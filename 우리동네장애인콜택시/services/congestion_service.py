"""예약 준비 도우미의 혼잡도 계산 로직.

과거 통계 기반의 참고 정보이며, 실제 배차/대기시간을 예측하거나 보장하지 않는다.
정확히 일치하는 조건(출발구+요일+시간)의 표본이 부족하면 아래 순서로 범위를 넓힌다.
  1) 출발구 + 요일 + 시간
  2) 출발구 + 시간 (요일 무관)
  3) 요일 + 시간 (자치구 무관)
  4) 전체 시간 (가장 넓은 범위)
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from congestion import congestion_icon, congestion_level_from_percentile, percentile_rank
from config import SMALL_SAMPLE_THRESHOLD
from districts import WEEKDAY_NAMES_KO
from repositories import taxi_repository as repo

CACHE_TTL_SECONDS = 600

TIER_LABELS = {
    "origin_weekday_hour": "출발 자치구 + 요일 + 시간대 기준 과거 통계",
    "origin_hour": "출발 자치구 + 시간대 기준 과거 통계 (요일 무관으로 범위 확대)",
    "weekday_hour": "요일 + 시간대 기준 서울 전체 과거 통계 (자치구 무관으로 범위 확대)",
    "overall": "전체 시간대 기준 서울 전체 과거 통계 (가장 넓은 범위로 확대)",
    "no_data": "과거 통계 없음",
}


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float | None:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


def _aggregate_rows(df: pd.DataFrame) -> dict:
    weight_col = "valid_wait_count" if "valid_wait_count" in df.columns else "request_count"
    weights = df[weight_col]
    return {
        "request_count": int(df["request_count"].sum()),
        "avg_dispatch_wait_min": _weighted_mean(df["avg_dispatch_wait_min"], weights),
        "median_dispatch_wait_min": _weighted_mean(df["median_dispatch_wait_min"], weights),
    }


def _format_hour(hour: int) -> str:
    period = "오전" if hour < 12 else "오후"
    display_hour = hour if hour in (0, 12) else hour % 12
    display_hour = 12 if display_hour == 0 else display_hour
    return f"{period} {display_hour}시"


def _build_guidance(weekday_num: int, request_hour: int, level: str, median_wait: float | None) -> str:
    weekday_name = WEEKDAY_NAMES_KO[weekday_num]
    time_label = _format_hour(request_hour)
    lines = []
    if level in ("다소 혼잡", "혼잡"):
        lines.append(f"선택하신 {weekday_name} {time_label}는 과거 이용 요청이 많았던 시간대입니다.")
    elif level == "비교적 여유":
        lines.append(f"선택하신 {weekday_name} {time_label}는 과거 기준으로 비교적 여유로웠던 시간대입니다.")
    elif level == "보통":
        lines.append(f"선택하신 {weekday_name} {time_label}는 과거 기준으로 보통 수준의 이용량을 보인 시간대입니다.")
    else:
        lines.append("해당 조건의 과거 통계가 충분하지 않아 혼잡도를 판단하기 어렵습니다.")

    if median_wait is not None:
        lines.append(
            f"과거 동일 조건의 중앙값 배차 대기시간은 약 {median_wait:.0f}분이었습니다. "
            "실제 대기시간은 당일 차량 운영 상황에 따라 달라질 수 있습니다."
        )
    return " ".join(lines)


def _build_result(tier: str, data: dict, weekday_num: int, request_hour: int) -> dict:
    percentile = data.get("congestion_percentile")
    level = data.get("congestion_level") or congestion_level_from_percentile(percentile)
    return {
        "tier": tier,
        "tier_label": TIER_LABELS[tier],
        "request_count": data.get("request_count"),
        "avg_dispatch_wait_min": data.get("avg_dispatch_wait_min"),
        "median_dispatch_wait_min": data.get("median_dispatch_wait_min"),
        "congestion_percentile": percentile,
        "congestion_level": level,
        "congestion_icon": congestion_icon(level),
        "guidance_text": _build_guidance(weekday_num, request_hour, level, data.get("median_dispatch_wait_min")),
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_congestion_info(district_id: str, weekday_num: int, request_hour: int) -> dict:
    # 1) 출발구 + 요일 + 시간
    row = repo.get_district_hourly_row(district_id, weekday_num, request_hour)
    if not row.empty and int(row.iloc[0]["request_count"]) >= SMALL_SAMPLE_THRESHOLD:
        r = row.iloc[0]
        return _build_result("origin_weekday_hour", {
            "request_count": int(r["request_count"]),
            "avg_dispatch_wait_min": r["avg_dispatch_wait_min"],
            "median_dispatch_wait_min": r["median_dispatch_wait_min"],
            "congestion_percentile": r["congestion_percentile"],
            "congestion_level": r["congestion_level"],
        }, weekday_num, request_hour)

    # 2) 출발구 + 시간 (요일 무관) - 같은 자치구의 시간대별 합산 분포에서 상대 위치를 재계산
    district_all = repo.get_district_hourly_stats(district_id)
    if not district_all.empty:
        by_hour = district_all.groupby("request_hour", as_index=False).apply(
            lambda g: pd.Series(_aggregate_rows(g))
        )
        if not by_hour.empty:
            by_hour["congestion_percentile"] = percentile_rank(by_hour["request_count"]).round(2)
            by_hour["congestion_level"] = by_hour["congestion_percentile"].map(congestion_level_from_percentile)
            target = by_hour[by_hour["request_hour"] == request_hour]
            if not target.empty and int(target.iloc[0]["request_count"]) >= SMALL_SAMPLE_THRESHOLD:
                r = target.iloc[0]
                return _build_result("origin_hour", {
                    "request_count": int(r["request_count"]),
                    "avg_dispatch_wait_min": r["avg_dispatch_wait_min"],
                    "median_dispatch_wait_min": r["median_dispatch_wait_min"],
                    "congestion_percentile": r["congestion_percentile"],
                    "congestion_level": r["congestion_level"],
                }, weekday_num, request_hour)

    # 3) 요일 + 시간 (자치구 무관)
    row = repo.get_weekday_hour_row(weekday_num, request_hour)
    if not row.empty and int(row.iloc[0]["request_count"]) >= SMALL_SAMPLE_THRESHOLD:
        r = row.iloc[0]
        return _build_result("weekday_hour", {
            "request_count": int(r["request_count"]),
            "avg_dispatch_wait_min": r["avg_dispatch_wait_min"],
            "median_dispatch_wait_min": r["median_dispatch_wait_min"],
            "congestion_percentile": r["congestion_percentile"],
            "congestion_level": r["congestion_level"],
        }, weekday_num, request_hour)

    # 4) 전체 시간 (가장 넓은 범위)
    overall_df = repo.get_all_weekday_hour_stats()
    if not overall_df.empty:
        agg = _aggregate_rows(overall_df)
        agg["congestion_percentile"] = None
        agg["congestion_level"] = "정보없음"
        return _build_result("overall", agg, weekday_num, request_hour)

    return _build_result("no_data", {
        "request_count": 0, "avg_dispatch_wait_min": None, "median_dispatch_wait_min": None,
        "congestion_percentile": None, "congestion_level": "정보없음",
    }, weekday_num, request_hour)
