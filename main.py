"""
해치타GO (Haechi Ta-GO) — 팀 통합 앱 진입점
--------------------------------------------
"해치와 소울 프렌즈가 함께 타고 달리는 따뜻한 이동 서비스"

  · 홈        → 브랜드 히어로 + 바로가기 카드 4개 (사이드바 없음)
  · 이용현황  → 담당: 팀원 (미구현 — 담당자 모듈 연결 예정)
  · 예약하기  → 담당: 팀원 (미구현 — 담당자 모듈 연결 예정)
  · FAQ       → 담당: 본인 ✅ views/faq.py
  · 관련뉴스  → 담당: 팀원 · 화면만 선구현 (views/news.py, 데이터는 예시)

접근성: 장애인 이용자 대상 — 큰 글씨·고대비·넓은 터치 영역.
실행 : streamlit run main.py

이 파일은 라우팅만 담당한다. 화면은 views/, 공통 요소는 common/, 스타일은 style/에 있다.
새 페이지를 붙일 때는 common/brand.py의 PAGES에 항목을 추가하고
아래 RENDERERS에 render 함수를 등록하면 된다.
"""

from __future__ import annotations
import streamlit as st
from common import layout, styles
from common.brand import PAGES
from views import faq, home, news, placeholder, reserve

st.set_page_config(
    page_title="해치타GO (Haechi Ta-GO)",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 페이지 key → 렌더 함수. 여기에 없는 key는 placeholder로 처리된다.
# 메뉴 구현 렌더링 부분 **
RENDERERS = {
    "faq": faq.render,
    "news": news.render,
    "reserve": reserve.render,
}

def _handle_nav_query() -> None:
    """홈 카드/브랜드의 링크(?nav=...) 클릭을 처리한다."""
    query = st.query_params
    if "nav" in query:
        target = query.get("nav")
        if target in PAGES:
            st.session_state.menu = target
        st.query_params.clear()
        st.rerun()

def main() -> None:
    if "menu" not in st.session_state:
        st.session_state.menu = "home"

    _handle_nav_query()
    styles.load("style.css")

    menu = st.session_state.menu

    # 홈은 사이드바 없이 전체 화면으로 보여준다
    if menu == "home":
        home.render()
        return

    layout.render_sidebar()
    render = RENDERERS.get(menu)
    if render is not None:
        render()
    else:
        placeholder.render(PAGES[menu])

if __name__ == "__main__":
    main()
