"""필수산출물 ③ 프로젝트 소개 — 목적·기술스택·산출물·구조."""

from __future__ import annotations

import streamlit as st

PROJECT_TREE = """
bootcamp-seoul-taxi-system/
├── main.py             # 앱 진입점 (라우팅만 담당)
├── views/              # 화면 — home / faq / news / placeholder
├── common/             # 브랜드 상수 · SVG 에셋 · 스타일 로더 · 사이드바
├── style/              # CSS — style(공통) / home / faq / news
├── crawler/            # BeautifulSoup · Selenium 수집 코드
├── preprocess/         # 수집 데이터 정제 파이프라인
├── db/                 # MySQL 스키마 · 적재(loader) · 조회(repository)
├── data/               # raw(원본 JSON) / processed(정제 CSV)
├── docs/               # 필수 산출물 문서 3종
└── 필수산출물/          # DB설계 · 수집데이터 · 프로젝트소개 화면 (본 화면)
"""


def render() -> None:
    """프로젝트 소개 화면."""
    st.header("ℹ 프로젝트 소개")

    with st.container(border=True):
        st.subheader("🎯 프로젝트 목적")
        st.markdown(
            """
            서울시 장애인 콜택시의 이용현황을 분석하고, 자동차 보조기구 및 관련
            지원정책 정보를 통합 제공하여 **장애인의 이동권 향상**과
            **정보 접근성 개선**을 지원한다.
            """
        )

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("🛠 기술 스택")
            st.markdown(
                """
                - **Python** — 전체 백엔드/수집 로직
                - **BeautifulSoup** — 정적 페이지 크롤링
                - **Selenium** — 동적 페이지 크롤링
                - **MySQL** — 데이터베이스 저장소
                - **PyMySQL** — Python ↔ MySQL 연동
                - **Streamlit** — 데이터 조회 GUI
                """
            )
    with col2:
        with st.container(border=True):
            st.subheader("📦 필수 산출물")
            st.markdown(
                """
                1. **데이터베이스 설계 문서**
                2. **수집 데이터**
                3. **데이터 조회 프로그램** (현재 화면)
                """
            )

    with st.container(border=True):
        st.subheader("🗂 프로젝트 구조")
        st.code(PROJECT_TREE, language="text")
