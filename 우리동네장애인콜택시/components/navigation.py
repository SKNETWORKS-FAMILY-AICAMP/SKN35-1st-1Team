"""서브페이지 공통 내비게이션(메인으로 돌아가기)."""
from __future__ import annotations

import streamlit as st


def render_home_link() -> None:
    st.page_link("app.py", label="🏠 메인으로 돌아가기", use_container_width=False)
