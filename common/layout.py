"""
공통 레이아웃 (사이드바)
------------------------
홈을 제외한 모든 페이지에서 같은 사이드바를 그린다.
페이지 목록은 common/brand.py의 PAGES·NAV_ORDER를 따른다.
"""

from __future__ import annotations
import streamlit as st
from common.assets import FACE_URI
from common.brand import BRAND_EN, BRAND_KO, NAV_ORDER, PAGES, TAGLINE

def render_sidebar() -> None:
    """브랜드 헤더 + 메뉴 버튼 + 안내 문구를 사이드바에 그린다."""
    with st.sidebar:
        st.markdown(
            f"""
            <a class="brand" href="?nav=home" target="_self" title="홈으로" style="margin-bottom: 3rem;">
                <img src="{FACE_URI}" alt="해치"/>
                <div>
                    <div class="brand-name">{BRAND_KO} <span>{BRAND_EN}</span></div>
                    <div class="brand-sub">{TAGLINE}</div>
                </div>
            </a>
            """,
            unsafe_allow_html=True,
        )
        # st.markdown('<div class="nav-cap">메뉴</div>', unsafe_allow_html=True)

        for key in NAV_ORDER:
            page = PAGES[key]
            active = st.session_state.menu == key
            # if st.button(f"{page['icon']}  {page['label']}", key=f"nav_{key}",
            if st.button(f"{page['label']}", key=f"nav_{key}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.menu = key
                st.rerun()

