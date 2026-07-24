"""이용현황/예약 준비 도우미 화면이 사용하는 집계 테이블 조회 전담 계층.

Streamlit 페이지는 이 모듈의 함수만 호출하고 직접 SQL을 작성하지 않는다.
모든 함수는 DB 장애/데이터 없음 상황에서도 예외를 던지지 않고 빈 DataFrame을 반환한다.
"""
from __future__ import annotations

import pandas as pd

from repositories.base import safe_read_sql


def get_area_list() -> pd.DataFrame:
    return safe_read_sql(
        "SELECT district_id, district_name, latitude, longitude FROM area ORDER BY district_id"
    )


def get_daily_stats(start_date, end_date, district_id: str | None = None) -> pd.DataFrame:
    query = """
        SELECT * FROM district_daily_stat
        WHERE stat_date BETWEEN :start_date AND :end_date
          AND (:district_id IS NULL OR district_id = :district_id)
    """
    return safe_read_sql(query, {"start_date": start_date, "end_date": end_date, "district_id": district_id})


def get_district_totals(start_date, end_date) -> pd.DataFrame:
    query = """
        SELECT district_id,
               SUM(request_count) AS request_count,
               SUM(dispatch_count) AS dispatch_count,
               SUM(ride_count) AS ride_count,
               SUM(completed_count) AS completed_count,
               SUM(cancel_count) AS cancel_count
        FROM district_daily_stat
        WHERE stat_date BETWEEN :start_date AND :end_date
        GROUP BY district_id
    """
    return safe_read_sql(query, {"start_date": start_date, "end_date": end_date})


def get_monthly_stats() -> pd.DataFrame:
    return safe_read_sql("SELECT * FROM monthly_stat ORDER BY year, month")


def get_district_hourly_stats(district_id: str | None = None) -> pd.DataFrame:
    """자치구 선택 시 district_hourly_stat, 미선택(전체) 시 weekday_hour_stat을 반환한다."""
    if district_id:
        return safe_read_sql(
            "SELECT * FROM district_hourly_stat WHERE district_id = :district_id",
            {"district_id": district_id},
        )
    return safe_read_sql("SELECT * FROM weekday_hour_stat")


def get_od_flows(
    origin_district_id: str | None = None,
    destination_district_id: str | None = None,
    top_n: int = 15,
) -> pd.DataFrame:
    query = """
        SELECT * FROM od_flow_stat
        WHERE (:origin_district_id IS NULL OR origin_district_id = :origin_district_id)
          AND (:destination_district_id IS NULL OR destination_district_id = :destination_district_id)
        ORDER BY ride_count DESC
        LIMIT :top_n
    """
    return safe_read_sql(
        query,
        {
            "origin_district_id": origin_district_id,
            "destination_district_id": destination_district_id,
            "top_n": top_n,
        },
    )


def get_purpose_stats(purpose_group: str | None = None, district_id: str | None = None) -> pd.DataFrame:
    query = """
        SELECT * FROM purpose_stat
        WHERE district_id = :district_id
          AND (:purpose_group IS NULL OR purpose_group = :purpose_group)
    """
    return safe_read_sql(query, {"purpose_group": purpose_group, "district_id": district_id or "ALL"})


def get_disability_vehicle_stats(vehicle_type: str | None = None) -> pd.DataFrame:
    query = "SELECT * FROM disability_vehicle_stat WHERE (:vehicle_type IS NULL OR vehicle_type = :vehicle_type)"
    return safe_read_sql(query, {"vehicle_type": vehicle_type})


def get_district_hourly_row(district_id: str, weekday_num: int, request_hour: int) -> pd.DataFrame:
    """혼잡도 대체조회 1단계: 출발구 + 요일 + 시간."""
    query = """
        SELECT * FROM district_hourly_stat
        WHERE district_id = :district_id AND weekday_num = :weekday_num AND request_hour = :request_hour
    """
    return safe_read_sql(query, {"district_id": district_id, "weekday_num": weekday_num, "request_hour": request_hour})


def get_district_hour_rows(district_id: str, request_hour: int) -> pd.DataFrame:
    """혼잡도 대체조회 2단계 재료: 출발구 + 시간(요일 무관, 요일별 행을 모두 반환해 서비스 계층에서 합산)."""
    query = "SELECT * FROM district_hourly_stat WHERE district_id = :district_id AND request_hour = :request_hour"
    return safe_read_sql(query, {"district_id": district_id, "request_hour": request_hour})


def get_weekday_hour_row(weekday_num: int, request_hour: int) -> pd.DataFrame:
    """혼잡도 대체조회 3단계: 요일 + 시간(자치구 무관)."""
    query = "SELECT * FROM weekday_hour_stat WHERE weekday_num = :weekday_num AND request_hour = :request_hour"
    return safe_read_sql(query, {"weekday_num": weekday_num, "request_hour": request_hour})


def get_all_weekday_hour_stats() -> pd.DataFrame:
    """혼잡도 대체조회 4단계(전체) 재료: weekday_hour_stat 전체."""
    return safe_read_sql("SELECT * FROM weekday_hour_stat")
