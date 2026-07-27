"""
미구현 파트 자리표시 화면
-------------------------
팀원 담당 파트(이용현황·예약하기)가 완성되기 전까지 대신 보여준다.
담당자 모듈이 준비되면 main.py의 RENDERERS에 등록하면 자동으로 대체된다.
"""

from __future__ import annotations

import streamlit as st


def render(page: dict[str, str]) -> None:
    """common/brand.py의 PAGES 항목 하나를 받아 안내 화면을 그린다."""
    st.header(f"{page['icon']} {page['label']}")
    st.info(
        f"**{page['label']}** 화면은 팀원 담당 파트입니다.\n\n"
        f"담당자가 모듈을 완성하면 `main.py` 라우팅에 연결됩니다."
    )
    st.caption("기획 내용: " + page.get("sub", "").replace("\n", " "))
