"""
필수산출물 화면용 예시(Dummy) 데이터
------------------------------------
'수집 데이터' 화면에서 원본 데이터의 형태를 보여주기 위한 샘플이다.
seed를 고정해 실행할 때마다 같은 값이 나온다.
"""

from __future__ import annotations

import random

import pandas as pd
import streamlit as st

# 서울시 25개 자치구
SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구",
]

DISABILITY_TYPES = ["지체장애", "뇌병변장애", "시각장애", "청각장애", "지적장애", "기타"]
DEVICE_TYPES = ["운전보조장치", "승하차보조장치", "휠체어고정장치", "핸드컨트롤", "좌석회전장치"]
MANUFACTURERS = ["오토모빌케어", "무브프리", "케어드라이브", "베리어프리텍", "이지모빌리티"]


@st.cache_data
def make_taxi_usage() -> pd.DataFrame:
    """자치구 × 연도 × 월 단위 콜택시 이용현황 더미 데이터."""
    random.seed(42)
    rows = []
    for year in (2022, 2023, 2024):
        for month in range(1, 13):
            for gu in SEOUL_DISTRICTS:
                rows.append(
                    {
                        "연도": year,
                        "월": month,
                        "자치구": gu,
                        "이용건수": random.randint(300, 2500),
                        "평균대기시간(분)": random.randint(15, 70),
                        "운행차량수": random.randint(3, 25),
                    }
                )
    return pd.DataFrame(rows)


@st.cache_data
def make_devices() -> pd.DataFrame:
    """자동차 보조기구 더미 데이터."""
    random.seed(7)
    products = [
        "핸드 컨트롤 브레이크", "회전형 운전석 시트", "휠체어 자동 리프트",
        "전동 승하차 발판", "손 조작 액셀 레버", "휠체어 고정 벨트 시스템",
        "좌측 액셀 페달", "스티어링 노브", "자동 도어 오프너", "슬라이딩 보드",
    ]
    rows = []
    for name in products:
        rows.append(
            {
                "제품명": name,
                "장애유형": random.choice(DISABILITY_TYPES),
                "종류": random.choice(DEVICE_TYPES),
                "제조사": random.choice(MANUFACTURERS),
                "가격": random.randint(15, 320) * 10000,
                "지원여부": random.choice(["지원", "지원", "미지원"]),
                "설명": f"{name} 제품으로 안전한 승하차와 운전을 보조합니다.",
            }
        )
    return pd.DataFrame(rows)


@st.cache_data
def make_policies() -> pd.DataFrame:
    """지원정책 더미 데이터."""
    rows = [
        ("서울시", "장애인 자동차 보조기구 지원사업", "최대 200만원",
         "등록 장애인(지체·뇌병변)", "2024.03 ~ 2024.11", "서울 전역"),
        ("한국장애인고용공단", "출퇴근 차량 개조 지원", "최대 300만원",
         "취업 장애인", "상시", "전국"),
        ("서울시설공단", "장애인 콜택시 이용 지원", "이용요금 감면",
         "보행상 장애인", "상시", "서울 전역"),
        ("보건복지부", "자동차 손 조작장치 지원", "최대 150만원",
         "1~3급 지체장애", "2024.01 ~ 2024.12", "전국"),
        ("강남구청", "장애인 이동편의 개조비 지원", "최대 100만원",
         "관내 등록 장애인", "2024.04 ~ 2024.09", "강남구"),
        ("경기도", "장애인 차량 리프트 설치 지원", "최대 250만원",
         "중증 장애인", "2024.02 ~ 2024.10", "경기 전역"),
    ]
    return pd.DataFrame(
        rows,
        columns=["기관", "정책명", "지원금", "대상", "신청기간", "지역"],
    )
