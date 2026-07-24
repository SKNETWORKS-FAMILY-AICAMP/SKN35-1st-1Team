"""전처리 파이프라인의 순수 함수 모음.

각 함수는 DataFrame을 받아 컬럼을 추가/변환한 DataFrame을 반환하며,
부수효과(파일 입출력 등)가 없어 pytest로 독립 검증이 가능하다.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from districts import WEEKDAY_NAMES_KO, hour_to_time_group, normalize_district_name
from preprocessing.config import (
    COLUMN_RENAME_MAP,
    DATETIME_COLUMNS,
    DEFAULT_DISABILITY_GROUP,
    DEFAULT_PURPOSE_GROUP,
    DEFAULT_VEHICLE_GROUP,
    DISABILITY_GROUP_MAP,
    MAX_REASONABLE_TRIP_HOURS,
    MAX_REASONABLE_WAIT_HOURS,
    PURPOSE_GROUP_MAP,
    VEHICLE_GROUP_MAP,
)


def rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    """원본 한글 컬럼명을 표준 영문 컬럼명으로 변경한다. 원본 CSV는 건드리지 않는다."""
    existing_map = {k: v for k, v in COLUMN_RENAME_MAP.items() if k in df.columns}
    return df.rename(columns=existing_map)


def parse_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """일시 컬럼들을 datetime으로 변환한다. 변환 실패 값은 NaT가 된다(예외로 앱이 죽지 않음)."""
    df = df.copy()
    for col in DATETIME_COLUMNS:
        if col in df.columns:
            # format="mixed": 같은 컬럼 안에 마이크로초 유무 등 표기가 섞여 있어도
            # 값별로 개별 파싱한다. 고정 포맷을 추정시키면(fast-path) 형식이 다른
            # 정상 값까지 통째로 NaT 처리되는 pandas 이슈가 있어 반드시 지정한다.
            df[col] = pd.to_datetime(df[col], errors="coerce", format="mixed")
    return df


def normalize_district_columns(df: pd.DataFrame) -> pd.DataFrame:
    """출발/목적 자치구를 서울 25개 표준명으로 정규화한다.

    원본 표기(origin_district_raw/destination_district_raw)는 그대로 보존하고,
    정규화 결과를 origin_district/destination_district에 별도로 담는다.
    표준 25개 구와 일치하지 않으면 매핑 실패로 보고 None(결측)으로 둔다(임의 강제 매핑 금지).
    """
    df = df.copy()
    if "origin_district_raw" in df.columns:
        df["origin_district"] = df["origin_district_raw"].map(normalize_district_name)
    if "destination_district_raw" in df.columns:
        df["destination_district"] = df["destination_district_raw"].map(normalize_district_name)
    return df


def _map_group(series: pd.Series, mapping: dict[str, str], default: str) -> pd.Series:
    return series.map(lambda v: mapping.get(str(v).strip(), default) if pd.notna(v) else default)


def group_categorical_columns(df: pd.DataFrame) -> pd.DataFrame:
    """이용목적/차량구분/장애유형 원본값을 분석용 그룹 범주로 단순화한다."""
    df = df.copy()
    if "purpose_raw" in df.columns:
        df["purpose_group"] = _map_group(df["purpose_raw"], PURPOSE_GROUP_MAP, DEFAULT_PURPOSE_GROUP)
    if "vehicle_type_raw" in df.columns:
        df["vehicle_type_group"] = _map_group(df["vehicle_type_raw"], VEHICLE_GROUP_MAP, DEFAULT_VEHICLE_GROUP)
    if "disability_type_raw" in df.columns:
        df["disability_type_group"] = _map_group(df["disability_type_raw"], DISABILITY_GROUP_MAP, DEFAULT_DISABILITY_GROUP)
    return df


def add_date_parts(df: pd.DataFrame) -> pd.DataFrame:
    """접수일시 기준 날짜 파생 컬럼을 추가한다. weekday_num: 0=월요일 ... 6=일요일(pandas 기본값과 동일)."""
    df = df.copy()
    request_at = df["request_at"]
    df["request_date"] = request_at.dt.date
    df["request_year"] = request_at.dt.year
    df["request_month"] = request_at.dt.month
    df["request_day"] = request_at.dt.day
    df["request_hour"] = request_at.dt.hour
    df["weekday_num"] = request_at.dt.weekday
    df["weekday_name"] = df["weekday_num"].map(
        lambda n: WEEKDAY_NAMES_KO[int(n)] if pd.notna(n) else None
    )
    df["is_weekend"] = df["weekday_num"].isin([5, 6])
    df["time_group"] = df["request_hour"].map(
        lambda h: hour_to_time_group(int(h)) if pd.notna(h) else None
    )
    return df


def classify_status(df: pd.DataFrame) -> pd.DataFrame:
    """접수/배차/승차/완료/취소 상태를 판정한다.

    우선순위: 취소일시 존재 > 하차일시 존재(완료) > 승차일시 존재(승차) >
    배차일시 존재(배차) > 그 외(접수).
    """
    df = df.copy()
    conditions = [
        df["cancel_at"].notna(),
        df["dropoff_at"].notna(),
        df["pickup_at"].notna(),
        df["dispatch_at"].notna(),
    ]
    choices = ["cancelled", "completed", "boarded", "dispatched"]
    df["status"] = np.select(conditions, choices, default="requested")
    return df


def _minutes_between(later: pd.Series, earlier: pd.Series) -> pd.Series:
    return (later - earlier).dt.total_seconds() / 60


def compute_wait_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """대기시간/탑승준비시간/이동시간을 분 단위로 계산한다.

    정의:
      dispatch_wait_min = 배차일시 - 접수일시
      pickup_wait_min   = 승차일시 - 접수일시
      boarding_delay_min = 승차일시 - 배차일시
      trip_duration_min  = 하차일시 - 승차일시
    """
    df = df.copy()
    df["dispatch_wait_min"] = _minutes_between(df["dispatch_at"], df["request_at"])
    df["pickup_wait_min"] = _minutes_between(df["pickup_at"], df["request_at"])
    df["boarding_delay_min"] = _minutes_between(df["pickup_at"], df["dispatch_at"])
    df["trip_duration_min"] = _minutes_between(df["dropoff_at"], df["pickup_at"])
    return df


def flag_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """이상치를 삭제하지 않고 플래그 컬럼으로 남긴다. 분석 집계 단계에서 is_valid_row로 제외 여부를 결정한다."""
    df = df.copy()
    max_wait_min = MAX_REASONABLE_WAIT_HOURS * 60
    max_trip_min = MAX_REASONABLE_TRIP_HOURS * 60

    df["is_negative_dispatch_wait"] = df["dispatch_wait_min"] < 0
    df["is_negative_pickup_wait"] = df["pickup_wait_min"] < 0
    df["is_negative_boarding_delay"] = df["boarding_delay_min"] < 0
    df["is_negative_trip_duration"] = df["trip_duration_min"] < 0
    df["is_wait_over_24h"] = (df["dispatch_wait_min"] > max_wait_min) | (df["pickup_wait_min"] > max_wait_min)
    df["is_trip_duration_over_24h"] = df["trip_duration_min"] > max_trip_min
    df["is_negative_fare"] = df["fare"] < 0
    df["is_negative_distance"] = df["distance"] < 0
    df["is_origin_mapping_fail"] = df["origin_district"].isna()
    df["is_destination_mapping_fail"] = df["destination_district"].isna()
    df["is_date_parse_fail"] = df["request_at"].isna()

    dedup_cols = [c for c in [
        "request_at", "origin_district_raw", "destination_district_raw", "fare", "distance",
    ] if c in df.columns]
    df["is_duplicate"] = df.duplicated(subset=dedup_cols, keep="first") if dedup_cols else False

    flag_cols = [
        "is_negative_dispatch_wait", "is_negative_pickup_wait", "is_negative_boarding_delay",
        "is_negative_trip_duration", "is_wait_over_24h", "is_trip_duration_over_24h",
        "is_negative_fare", "is_negative_distance", "is_origin_mapping_fail",
        "is_destination_mapping_fail", "is_date_parse_fail", "is_duplicate",
    ]
    df["is_valid_row"] = ~df[flag_cols].any(axis=1)
    return df


def run_all_transforms(df: pd.DataFrame) -> pd.DataFrame:
    """전체 변환 파이프라인을 순서대로 적용한다."""
    df = rename_columns(df)
    df = parse_datetime_columns(df)
    df = normalize_district_columns(df)
    df = group_categorical_columns(df)
    df = classify_status(df)
    df = compute_wait_minutes(df)
    # add_date_parts는 request_at이 NaT(날짜 변환 실패)인 행도 예외 없이 NaN/None으로 채운다.
    df = add_date_parts(df)
    df = flag_outliers(df)
    return df
