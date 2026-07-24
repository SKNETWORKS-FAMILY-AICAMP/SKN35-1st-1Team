"""전처리 파이프라인(preprocessing/transforms.py) 단위 테스트."""
from __future__ import annotations

import pandas as pd

from districts import normalize_district_name
from preprocessing.transforms import (
    classify_status,
    compute_wait_minutes,
    flag_outliers,
    parse_datetime_columns,
    rename_columns,
)

# ---------------------------------------------------------------------
# 1) 날짜 파싱 테스트
# ---------------------------------------------------------------------
def test_parse_datetime_columns_handles_invalid_values():
    df = pd.DataFrame({
        "request_at": ["2025-01-01 09:00:00", "0000-00-00", None],
        "dispatch_at": ["2025-01-01 09:10:00.123456", "2025-01-02 10:00:00", ""],
    })
    out = parse_datetime_columns(df)
    assert pd.notna(out["request_at"].iloc[0])
    assert pd.isna(out["request_at"].iloc[1])  # 잘못된 날짜는 예외 대신 NaT
    assert pd.isna(out["request_at"].iloc[2])


def test_parse_datetime_columns_handles_mixed_microsecond_formats():
    """마이크로초 유무가 섞인 컬럼도 값별로 올바르게 파싱되어야 한다(회귀 테스트)."""
    df = pd.DataFrame({
        "request_at": ["2025-06-06 17:46:38", "2025-06-06 17:00:00.500000"],
    })
    out = parse_datetime_columns(df)
    assert out["request_at"].notna().all()


# ---------------------------------------------------------------------
# 2) 컬럼명 변환 테스트
# ---------------------------------------------------------------------
def test_rename_columns_maps_korean_headers_to_english():
    df = pd.DataFrame({"접수일시": ["x"], "출발구": ["강남구"], "이용목적": ["병원 진료"]})
    out = rename_columns(df)
    assert "request_at" in out.columns
    assert "origin_district_raw" in out.columns
    assert "purpose_raw" in out.columns
    assert "접수일시" not in out.columns


# ---------------------------------------------------------------------
# 3) 상태값 분류 테스트
# ---------------------------------------------------------------------
def test_classify_status_priority_order():
    now = pd.Timestamp("2025-01-01 09:00:00")
    df = pd.DataFrame({
        "cancel_at": [now, pd.NaT, pd.NaT, pd.NaT],
        "dropoff_at": [pd.NaT, now, pd.NaT, pd.NaT],
        "pickup_at": [pd.NaT, now, now, pd.NaT],
        "dispatch_at": [pd.NaT, now, now, now],
    })
    out = classify_status(df)
    assert list(out["status"]) == ["cancelled", "completed", "boarded", "dispatched"]


def test_classify_status_defaults_to_requested():
    df = pd.DataFrame({
        "cancel_at": [pd.NaT], "dropoff_at": [pd.NaT], "pickup_at": [pd.NaT], "dispatch_at": [pd.NaT],
    })
    out = classify_status(df)
    assert out["status"].iloc[0] == "requested"


# ---------------------------------------------------------------------
# 4) 음수 대기시간 플래그 테스트
# ---------------------------------------------------------------------
def test_flag_negative_wait_time_and_over_24h():
    df = pd.DataFrame({
        "request_at": pd.to_datetime(["2025-01-01 09:00:00", "2025-01-01 09:00:00"]),
        "dispatch_at": pd.to_datetime(["2025-01-01 08:50:00", "2025-01-03 09:00:00"]),  # 음수 / 48시간 초과
        "pickup_at": pd.to_datetime([pd.NaT, pd.NaT]),
        "dropoff_at": pd.to_datetime([pd.NaT, pd.NaT]),
        "fare": [1500, 1500],
        "distance": [3.0, 3.0],
        "origin_district": ["강남구", "강남구"],
        "destination_district": ["서초구", "서초구"],
    })
    df = compute_wait_minutes(df)
    df = flag_outliers(df)
    assert df["is_negative_dispatch_wait"].iloc[0]
    assert not df["is_negative_dispatch_wait"].iloc[1]
    assert df["is_wait_over_24h"].iloc[1]
    assert not df["is_valid_row"].iloc[0]
    assert not df["is_valid_row"].iloc[1]


# ---------------------------------------------------------------------
# 5) 자치구명 정규화 테스트
# ---------------------------------------------------------------------
def test_normalize_district_name_variants():
    assert normalize_district_name("강남") == "강남구"
    assert normalize_district_name("강남구") == "강남구"
    assert normalize_district_name("서울 강남구") == "강남구"
    assert normalize_district_name("서울특별시 강남구") == "강남구"
    assert normalize_district_name("  강남구  ") == "강남구"


# ---------------------------------------------------------------------
# 6) 매핑되지 않은 자치구 처리 테스트
# ---------------------------------------------------------------------
def test_normalize_district_name_unmapped_returns_none():
    assert normalize_district_name("세종시") is None
    assert normalize_district_name("부산 해운대구") is None
    assert normalize_district_name("") is None
    assert normalize_district_name(None) is None


# ---------------------------------------------------------------------
# 9) 평균과 중앙값 계산 테스트
# ---------------------------------------------------------------------
def test_average_and_median_wait_minutes():
    df = pd.DataFrame({
        "request_at": pd.to_datetime(["2025-01-01 09:00:00"] * 5),
        "dispatch_at": pd.to_datetime([
            "2025-01-01 09:10:00", "2025-01-01 09:20:00", "2025-01-01 09:30:00",
            "2025-01-01 09:40:00", "2025-01-01 09:50:00",
        ]),
    })
    df["dispatch_wait_min"] = (df["dispatch_at"] - df["request_at"]).dt.total_seconds() / 60
    assert df["dispatch_wait_min"].mean() == 30.0
    assert df["dispatch_wait_min"].median() == 30.0
