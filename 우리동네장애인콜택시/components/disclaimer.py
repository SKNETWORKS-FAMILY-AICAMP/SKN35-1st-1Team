"""서비스 성격 안내 문구. 메인 화면과 예약하기 페이지에 반드시 표시한다."""
from __future__ import annotations

import streamlit as st

from config import SERVICE_DISCLAIMER


def render_service_disclaimer() -> None:
    st.info(f"ℹ️ **안내**\n\n{SERVICE_DISCLAIMER}", icon="ℹ️")


def render_data_freshness_note(text: str) -> None:
    """정보 변경 가능성 안내(예: FAQ/뉴스 마지막 수집 시각)."""
    st.caption(f"🕒 {text}")
