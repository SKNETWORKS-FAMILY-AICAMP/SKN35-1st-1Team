"""혼잡도 분위수/등급 산정 공통 로직.

집계 스크립트(preprocessing/build_aggregates.py)와 서비스 계층
(services/congestion_service.py)이 동일한 기준을 사용하도록 공유한다.
"""
from __future__ import annotations

import pandas as pd

# 과거 접수 건수 분위수 기준 4단계
CONGESTION_LEVELS = [
    (30, "비교적 여유", "🟢"),
    (70, "보통", "🟡"),
    (90, "다소 혼잡", "🟠"),
]
CONGESTION_HIGH = ("혼잡", "🔴")


def congestion_level_from_percentile(percentile: float | None) -> str:
    """분위수(0~100)를 4단계 혼잡도 등급 문자열로 변환한다.

    하위 30%: 비교적 여유 / 30~70%: 보통 / 70~90%: 다소 혼잡 / 상위 10%(>=90): 혼잡
    """
    if percentile is None or pd.isna(percentile):
        return "정보없음"
    for threshold, label, _icon in CONGESTION_LEVELS:
        if percentile < threshold:
            return label
    return CONGESTION_HIGH[0]


def congestion_icon(level: str) -> str:
    for _threshold, label, icon in CONGESTION_LEVELS:
        if label == level:
            return icon
    if level == CONGESTION_HIGH[0]:
        return CONGESTION_HIGH[1]
    return "⚪"


def percentile_rank(values: pd.Series) -> pd.Series:
    """그룹 내 상대적 순위를 0~100 백분위로 반환한다(값이 클수록 높은 분위)."""
    if len(values) <= 1:
        return pd.Series([50.0] * len(values), index=values.index)
    return values.rank(pct=True) * 100
