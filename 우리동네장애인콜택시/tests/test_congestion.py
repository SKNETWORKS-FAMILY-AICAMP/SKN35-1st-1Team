"""혼잡도 등급 산정 및 대체조회 순서 테스트."""
from __future__ import annotations

import pandas as pd
import pytest

from congestion import congestion_level_from_percentile
from services import congestion_service


@pytest.fixture(autouse=True)
def _clear_congestion_cache():
    # get_congestion_info는 st.cache_data로 캐시되므로, 동일한 인자(자치구/요일/시간)로
    # 여러 테스트가 서로 다른 monkeypatch 결과를 기대할 때 이전 테스트의 캐시가
    # 섞여 들어오지 않도록 매 테스트 전에 캐시를 비운다.
    congestion_service.get_congestion_info.clear()
    yield


# ---------------------------------------------------------------------
# 7) 혼잡도 등급 테스트
# ---------------------------------------------------------------------
def test_congestion_level_boundaries():
    assert congestion_level_from_percentile(0) == "비교적 여유"
    assert congestion_level_from_percentile(29.9) == "비교적 여유"
    assert congestion_level_from_percentile(30) == "보통"
    assert congestion_level_from_percentile(69.9) == "보통"
    assert congestion_level_from_percentile(70) == "다소 혼잡"
    assert congestion_level_from_percentile(89.9) == "다소 혼잡"
    assert congestion_level_from_percentile(90) == "혼잡"
    assert congestion_level_from_percentile(100) == "혼잡"


def test_congestion_level_handles_missing_value():
    assert congestion_level_from_percentile(None) == "정보없음"
    assert congestion_level_from_percentile(float("nan")) == "정보없음"


# ---------------------------------------------------------------------
# 8) 혼잡도 대체 조회 순서 테스트
# ---------------------------------------------------------------------
def _row(**kwargs) -> pd.DataFrame:
    return pd.DataFrame([kwargs])


def test_congestion_fallback_uses_tier1_when_sample_sufficient(monkeypatch):
    monkeypatch.setattr(
        congestion_service.repo, "get_district_hourly_row",
        lambda *a, **k: _row(request_count=20, avg_dispatch_wait_min=15.0, median_dispatch_wait_min=14.0,
                             congestion_percentile=80.0, congestion_level="다소 혼잡"),
    )
    result = congestion_service.get_congestion_info("강남구", 0, 9)
    assert result["tier"] == "origin_weekday_hour"
    assert result["congestion_level"] == "다소 혼잡"


def test_congestion_fallback_skips_to_tier3_when_tier1_and_tier2_insufficient(monkeypatch):
    empty = pd.DataFrame()
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_row", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_stats", lambda *a, **k: empty)
    monkeypatch.setattr(
        congestion_service.repo, "get_weekday_hour_row",
        lambda *a, **k: _row(request_count=50, avg_dispatch_wait_min=20.0, median_dispatch_wait_min=18.0,
                             congestion_percentile=40.0, congestion_level="보통"),
    )
    result = congestion_service.get_congestion_info("강남구", 0, 9)
    assert result["tier"] == "weekday_hour"


def test_congestion_fallback_reaches_overall_when_all_else_missing(monkeypatch):
    empty = pd.DataFrame()
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_row", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_stats", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_weekday_hour_row", lambda *a, **k: empty)
    monkeypatch.setattr(
        congestion_service.repo, "get_all_weekday_hour_stats",
        lambda *a, **k: pd.DataFrame({"request_count": [100, 200], "avg_dispatch_wait_min": [10.0, 20.0],
                                       "median_dispatch_wait_min": [9.0, 18.0]}),
    )
    result = congestion_service.get_congestion_info("강남구", 0, 9)
    assert result["tier"] == "overall"


def test_congestion_fallback_no_data_when_nothing_available(monkeypatch):
    empty = pd.DataFrame()
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_row", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_district_hourly_stats", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_weekday_hour_row", lambda *a, **k: empty)
    monkeypatch.setattr(congestion_service.repo, "get_all_weekday_hour_stats", lambda *a, **k: empty)
    result = congestion_service.get_congestion_info("강남구", 0, 9)
    assert result["tier"] == "no_data"
