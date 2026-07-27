"""
필수산출물 화면 — 단독 실행 앱
------------------------------
부트캠프 제출용 3개 화면(DB설계 · 수집데이터 · 프로젝트소개)만 모아 놓았다.

실행: streamlit run 필수산출물/app.py

이 폴더는 본 앱(main.py)과 완전히 독립적이다.
팀 저장소에 합칠 때 필요 없으면 폴더째 삭제해도 본 앱은 그대로 동작한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# 이 폴더를 import 경로에 명시적으로 추가한다.
# streamlit run은 스크립트 폴더를 자동으로 넣어주지만 실행 방식에 따라 다르므로 직접 보장한다.
sys.path.insert(0, str(Path(__file__).resolve().parent))

import about      # noqa: E402
import rawdata    # noqa: E402
import schema     # noqa: E402

st.set_page_config(
    page_title="필수산출물 · 서울시 장애인 콜택시",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "🗄 DB 설계": schema.render,
    "📁 수집 데이터": rawdata.render,
    "ℹ 프로젝트 소개": about.render,
}


def _load_style() -> None:
    css = (Path(__file__).resolve().parent / "style.css").read_text(encoding="utf-8")
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def main() -> None:
    _load_style()

    with st.sidebar:
        st.markdown("### 📦 필수 산출물")
        st.caption("부트캠프 제출용 화면")
        choice = st.radio("산출물", list(PAGES), label_visibility="collapsed")
        st.divider()
        st.caption("⚠ 표시 데이터는 예시(Dummy)입니다.")

    PAGES[choice]()


if __name__ == "__main__":
    main()
