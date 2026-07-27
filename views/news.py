"""
관련뉴스 화면
-------------
탭(전체/복지사업/지원사업/택시소식) + 2열 카드 그리드 + 검색 + 페이지네이션.
뉴스 데이터와 검색 로직은 common/news_data.py에 있다.
"""

from __future__ import annotations

import streamlit as st

from common import news_data, styles
from common.news_data import CATEGORY_CLASS, PER_PAGE, TABS


def _card_html(item: dict[str, str]) -> str:
    """뉴스 카드 한 장. 카테고리 색상은 CSS 클래스(.nbadge.*)로 처리한다."""
    cate_class = CATEGORY_CLASS.get(item["cat"], "")
    return f"""
    <div class="ncard">
        <div class="ncard-top">
            <span class="nbadge {cate_class}">{item['cat']}</span>
            <span class="ndate">{item['date']}</span>
        </div>
        <div class="ntitle">{item['title']}</div>
        <div class="ndesc">{item['desc']}</div>
        <div class="ndiv"></div>
        <div class="ncard-bot">
            <span class="nsource">{item['source']}</span>
            <a class="nlink" href="{item['url']}" target="_blank" rel="noopener">원문보기 ↗</a>
        </div>
    </div>
    """


def _pagination(cat: str, page: int, pages: int) -> None:
    """페이지가 2개 이상일 때만 ‹ 1 2 3 › 버튼을 그린다."""
    if pages <= 1:
        return
    st.write("")
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        cols = st.columns(pages + 2)
        if cols[0].button("‹", key=f"pg_{cat}_prev", disabled=(page == 1),
                          use_container_width=True):
            st.session_state[f"npage_{cat}"] = max(1, page - 1)
            st.rerun()
        for i in range(1, pages + 1):
            if cols[i].button(str(i), key=f"pg_{cat}_{i}", use_container_width=True,
                              type="primary" if i == page else "secondary"):
                st.session_state[f"npage_{cat}"] = i
                st.rerun()
        if cols[pages + 1].button("›", key=f"pg_{cat}_next", disabled=(page == pages),
                                  use_container_width=True):
            st.session_state[f"npage_{cat}"] = min(pages, page + 1)
            st.rerun()


def _grid(cat: str, keyword: str) -> None:
    """탭 하나의 내용 — 검색 결과를 2열 카드로 그리고 페이지를 나눈다."""
    items = news_data.search(cat, keyword)

    # 검색어가 바뀌면 해당 탭을 1페이지로 되돌린다
    sig_key, page_key = f"nsig_{cat}", f"npage_{cat}"
    if st.session_state.get(sig_key) != keyword:
        st.session_state[sig_key] = keyword
        st.session_state[page_key] = 1

    total = len(items)
    pages = max(1, -(-total // PER_PAGE))
    page = min(st.session_state.get(page_key, 1), pages)
    st.session_state[page_key] = page

    st.markdown(f"**{total}건**의 뉴스" + (f"  ·  검색어: `{keyword}`" if keyword else ""))
    st.write("")
    if total == 0:
        st.warning("검색 결과가 없습니다. 다른 검색어나 탭을 선택해 보세요.")
        return

    start = (page - 1) * PER_PAGE
    grid = st.columns(2, gap="medium")
    for idx, item in enumerate(items[start:start + PER_PAGE]):
        with grid[idx % 2]:
            st.markdown(_card_html(item), unsafe_allow_html=True)
    _pagination(cat, page, pages)


def render() -> None:
    """관련뉴스 화면을 그린다."""
    styles.load("news.css")

    st.title("관련뉴스")
    st.caption("장애인콜택시와 관련된 최신 소식과 정책 변화, 이용 안내 정보를 한눈에 확인하세요.")

    keyword = st.text_input("검색", placeholder="뉴스 제목이나 키워드를 검색하세요",
                            label_visibility="collapsed").strip()

    tabs = st.tabs([label for label, _ in TABS])
    for tab, (_, cat) in zip(tabs, TABS):
        with tab:
            _grid(cat, keyword)