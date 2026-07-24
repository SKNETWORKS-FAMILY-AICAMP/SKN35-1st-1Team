"""우리동네 장애인 콜택시 - 메인 화면.

서울시 장애인콜택시 이용현황 분석 및 조회 시스템. 실제 예약/배차를 처리하지 않는다.
"""
from __future__ import annotations

import streamlit as st

from components.accessibility import apply_accessibility_css
from components.disclaimer import render_service_disclaimer

st.set_page_config(
    page_title="우리동네 장애인 콜택시",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_accessibility_css()

st.title("🚕 우리동네 장애인 콜택시")
st.markdown("과거 이용 데이터로 통계를 확인하고, 예약 전 정보를 미리 정리해 보세요.")

render_service_disclaimer()

st.write("")

MENU_ITEMS = [
    {"page": "pages/1_이용현황.py", "icon": "📊", "label": "이용현황", "description": "지역별·시간대별 통계"},
    {"page": "pages/2_예약하기.py", "icon": "📝", "label": "예약하기", "description": "예약 준비 도우미"},
    {"page": "pages/3_FAQ.py", "icon": "❓", "label": "FAQ", "description": "자주 묻는 질문"},
    {"page": "pages/4_관련뉴스.py", "icon": "📰", "label": "관련뉴스", "description": "최신 뉴스 모아보기"},
]

row1 = st.columns(2)
row2 = st.columns(2)
for col, item in zip(row1 + row2, MENU_ITEMS):
    with col:
        with st.container(border=True):
            st.markdown(f"<div class='app-tile-icon'>{item['icon']}</div>", unsafe_allow_html=True)
            st.page_link(item["page"], label=item["label"], use_container_width=True)
            st.markdown(f"<div class='app-tile-desc'>{item['description']}</div>", unsafe_allow_html=True)
