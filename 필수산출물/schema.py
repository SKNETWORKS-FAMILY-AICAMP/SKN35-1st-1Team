"""필수산출물 ① 데이터베이스 설계 — 테이블 스키마와 관계 문서."""

from __future__ import annotations

import pandas as pd
import streamlit as st

SCHEMA: dict[str, list[tuple[str, str, str]]] = {
    "taxi_usage (콜택시 이용현황)": [
        ("usage_id", "INT PK AUTO_INCREMENT", "이용 레코드 고유번호"),
        ("year", "INT", "이용 연도"),
        ("month", "INT", "이용 월"),
        ("district_id", "INT FK → district", "자치구 코드"),
        ("use_count", "INT", "이용 건수"),
        ("avg_wait_min", "INT", "평균 대기시간(분)"),
        ("vehicle_count", "INT", "운행 차량 수"),
    ],
    "assistive_device (자동차 보조기구)": [
        ("device_id", "INT PK AUTO_INCREMENT", "보조기구 고유번호"),
        ("name", "VARCHAR(100)", "제품명"),
        ("disability_type", "VARCHAR(30)", "적용 장애유형"),
        ("device_type", "VARCHAR(30)", "보조기구 종류"),
        ("manufacturer", "VARCHAR(50)", "제조사"),
        ("price", "INT", "가격(원)"),
        ("is_supported", "BOOLEAN", "지원 여부"),
        ("description", "TEXT", "제품 설명"),
    ],
    "support_policy (지원정책)": [
        ("policy_id", "INT PK AUTO_INCREMENT", "정책 고유번호"),
        ("organization", "VARCHAR(80)", "주관 기관"),
        ("policy_name", "VARCHAR(120)", "정책명"),
        ("support_amount", "VARCHAR(50)", "지원금"),
        ("target", "VARCHAR(80)", "지원 대상"),
        ("apply_period", "VARCHAR(50)", "신청 기간"),
        ("region", "VARCHAR(30)", "지원 지역"),
    ],
    "district (자치구 코드)": [
        ("district_id", "INT PK", "자치구 코드"),
        ("district_name", "VARCHAR(20)", "자치구 이름"),
    ],
    "faq (자주 묻는 질문)": [
        ("faq_id", "INT PK AUTO_INCREMENT", "FAQ 고유번호"),
        ("category", "VARCHAR(30)", "카테고리"),
        ("question", "VARCHAR(200)", "질문"),
        ("answer", "TEXT", "답변"),
    ],
}

ERD = """
district (1) ──< (N) taxi_usage      # 자치구별 이용현황
assistive_device                     # 독립 마스터 테이블
support_policy                       # 독립 마스터 테이블
faq                                  # 독립 마스터 테이블
"""


def render() -> None:
    """DB 설계 문서 화면 — 테이블 스키마와 관계를 문서화한다."""
    st.header("🗄 데이터베이스 설계 (스키마 문서)")
    st.caption("필수 산출물 ① · 실제 MySQL 적재 전 설계안입니다.")

    for table, columns in SCHEMA.items():
        with st.expander(f"📑 {table}", expanded=table.startswith("taxi")):
            df = pd.DataFrame(columns, columns=["컬럼명", "타입/제약", "설명"])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("🔗 테이블 관계 (ERD 요약)")
        st.code(ERD, language="text")
        st.caption("※ 콜택시 이용현황은 자치구(district)와 1:N 관계로 연결됩니다.")
