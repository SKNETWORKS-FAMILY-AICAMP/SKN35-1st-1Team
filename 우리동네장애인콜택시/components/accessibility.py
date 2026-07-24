"""최소한의 커스텀 CSS로 접근성(큰 글씨, 넓은 터치 영역, 높은 명도 대비)을 보강한다.

Streamlit 기본 접근성(키보드 포커스, 시맨틱 요소 등)을 덮어쓰지 않는 범위에서만 조정한다.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

_CSS_PATH = Path(__file__).resolve().parent.parent / "assets" / "styles.css"


def apply_accessibility_css() -> None:
    css = _CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)
