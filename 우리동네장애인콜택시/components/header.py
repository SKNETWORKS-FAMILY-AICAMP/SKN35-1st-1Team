"""공통 페이지 헤더."""
from __future__ import annotations

import streamlit as st


def render_page_header(title: str, description: str | None = None) -> None:
    st.title(title)
    if description:
        # 설명은 회색 캡션 하나로만 처리하지 않고 본문 텍스트로도 함께 노출한다.
        st.markdown(description)
