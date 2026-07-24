"""이용현황 페이지의 비즈니스 로직: 필터 적용, KPI/차트용 데이터 가공.

공개 집계 데이터만 다루므로 st.cache_data를 사용한다(개인정보 없음).
"""
from __future__ import annotations

import datetime

import pandas as pd
import streamlit as st

from repositories import taxi_repository as repo

CACHE_TTL_SECONDS = 600


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_area_options() -> list[str]:
    df = repo.get_area_list()
    return df["district_id"].tolist() if not df.empty else []


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_purpose_options() -> list[str]:
    df = repo.get_purpose_stats(district_id="ALL")
    return sorted(df["purpose_group"].dropna().unique().tolist()) if not df.empty else []


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_vehicle_type_options() -> list[str]:
    df = repo.get_disability_vehicle_stats()
    return sorted(df["vehicle_type"].dropna().unique().tolist()) if not df.empty else []


def _weighted_mean(values: pd.Series, weights: pd.Series) -> float | None:
    mask = values.notna() & weights.notna() & (weights > 0)
    if not mask.any():
        return None
    return float((values[mask] * weights[mask]).sum() / weights[mask].sum())


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_kpi_summary(start_date: datetime.date, end_date: datetime.date, district_id: str | None) -> dict:
    """이용현황 페이지 KPI 카드에 표시할 지표를 계산한다.

    평균값은 (일자 x 자치구) 단위로 이미 평균낸 avg_* 컬럼을 valid_wait_count로
    가중평균하여 재조합한다(단순 평균의 평균이 아니다).
    """
    df = repo.get_daily_stats(start_date, end_date, district_id)
    empty = {
        "request_count": 0, "ride_count": 0, "completed_count": 0, "cancel_count": 0,
        "cancel_rate": None, "avg_dispatch_wait_min": None, "median_dispatch_wait_min": None,
        "avg_pickup_wait_min": None, "median_pickup_wait_min": None, "avg_distance": None, "avg_fare": None,
        "has_data": False,
    }
    if df.empty:
        return empty

    request_count = int(df["request_count"].sum())
    ride_count = int(df["ride_count"].sum())
    completed_count = int(df["completed_count"].sum())
    cancel_count = int(df["cancel_count"].sum())

    return {
        "request_count": request_count,
        "ride_count": ride_count,
        "completed_count": completed_count,
        "cancel_count": cancel_count,
        "cancel_rate": round(cancel_count / request_count * 100, 1) if request_count else None,
        "avg_dispatch_wait_min": _weighted_mean(df["avg_dispatch_wait_min"], df["valid_wait_count"]),
        "median_dispatch_wait_min": _weighted_mean(df["median_dispatch_wait_min"], df["valid_wait_count"]),
        "avg_pickup_wait_min": _weighted_mean(df["avg_pickup_wait_min"], df["valid_wait_count"]),
        "median_pickup_wait_min": _weighted_mean(df["median_pickup_wait_min"], df["valid_wait_count"]),
        "avg_distance": _weighted_mean(df["avg_distance"], df["ride_count"]),
        "avg_fare": _weighted_mean(df["avg_fare"], df["ride_count"]),
        "has_data": True,
    }


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_district_map_data(start_date: datetime.date, end_date: datetime.date) -> pd.DataFrame:
    totals = repo.get_district_totals(start_date, end_date)
    areas = repo.get_area_list()
    if totals.empty or areas.empty:
        return pd.DataFrame()
    return areas.merge(totals, on="district_id", how="left").fillna({
        "request_count": 0, "dispatch_count": 0, "ride_count": 0, "completed_count": 0, "cancel_count": 0,
    })


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_monthly_trend() -> pd.DataFrame:
    df = repo.get_monthly_stats()
    if df.empty:
        return df
    df = df.copy()
    df["year_month"] = df["year"].astype(str) + "-" + df["month"].astype(int).astype(str).str.zfill(2)
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_heatmap_data(district_id: str | None) -> pd.DataFrame:
    return repo.get_district_hourly_stats(district_id)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_od_flows(origin_district_id: str | None, destination_district_id: str | None, top_n: int = 15) -> pd.DataFrame:
    return repo.get_od_flows(origin_district_id, destination_district_id, top_n)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_purpose_distribution(district_id: str | None = None) -> pd.DataFrame:
    return repo.get_purpose_stats(district_id=district_id)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_vehicle_disability_distribution(vehicle_type: str | None = None) -> pd.DataFrame:
    return repo.get_disability_vehicle_stats(vehicle_type)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_district_detail(district_id: str, start_date: datetime.date, end_date: datetime.date) -> dict:
    """자치구 선택 상세정보: 출발/도착 건수, 대기시간, 혼잡 요일/시간, 주요 목적지, 주요 이용목적."""
    daily = repo.get_daily_stats(start_date, end_date, district_id)
    od_out = repo.get_od_flows(origin_district_id=district_id, top_n=1)
    od_in_all = repo.get_od_flows(destination_district_id=None, top_n=10_000)
    hourly = repo.get_district_hourly_stats(district_id)
    purpose = repo.get_purpose_stats(district_id=district_id)

    detail = {
        "origin_request_count": int(daily["request_count"].sum()) if not daily.empty else 0,
        "destination_request_count": (
            int(od_in_all.loc[od_in_all["destination_district_id"] == district_id, "request_count"].sum())
            if not od_in_all.empty else 0
        ),
        "avg_dispatch_wait_min": _weighted_mean(daily["avg_dispatch_wait_min"], daily["valid_wait_count"]) if not daily.empty else None,
        "median_dispatch_wait_min": _weighted_mean(daily["median_dispatch_wait_min"], daily["valid_wait_count"]) if not daily.empty else None,
        "avg_pickup_wait_min": _weighted_mean(daily["avg_pickup_wait_min"], daily["valid_wait_count"]) if not daily.empty else None,
        "busiest_weekday_name": None,
        "busiest_hour": None,
        "top_destination_district": od_out.iloc[0]["destination_district_id"] if not od_out.empty else None,
        "top_purpose": None,
    }

    if not hourly.empty:
        from districts import WEEKDAY_NAMES_KO
        busiest = hourly.loc[hourly["request_count"].idxmax()]
        detail["busiest_weekday_name"] = WEEKDAY_NAMES_KO[int(busiest["weekday_num"])]
        detail["busiest_hour"] = int(busiest["request_hour"])

    if not purpose.empty:
        top_row = purpose.loc[purpose["request_count"].idxmax()]
        detail["top_purpose"] = top_row["purpose_group"]

    return detail
