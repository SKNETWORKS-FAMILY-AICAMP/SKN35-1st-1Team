"""장애인콜택시 관련뉴스."""
from __future__ import annotations

import streamlit as st

from components.accessibility import apply_accessibility_css
from components.disclaimer import render_data_freshness_note
from components.header import render_page_header
from components.navigation import render_home_link
from services import news_service as svc

st.set_page_config(page_title="관련뉴스 | 우리동네 장애인 콜택시", page_icon="📰", layout="wide")
apply_accessibility_css()
render_home_link()
render_page_header("장애인콜택시 관련뉴스", "네이버 뉴스 검색 API로 수집한 장애인콜택시·교통약자 이동지원 관련 최신 뉴스입니다.")

if not svc.naver_api_configured():
    st.warning(
        "네이버 뉴스 검색 API 키(NAVER_CLIENT_ID, NAVER_CLIENT_SECRET)가 설정되어 있지 않습니다. "
        "새 뉴스를 수집하려면 [네이버 개발자센터](https://developers.naver.com)에서 API 키를 발급받아 "
        ".env 파일에 등록한 뒤 `uv run python collectors/collect_news.py`를 실행해 주세요. "
        "지금은 DB에 이미 저장된 뉴스만 표시합니다.",
        icon="🔑",
    )

last_collected = svc.get_last_collected_at()
render_data_freshness_note(f"최근 수집 시각: {last_collected}" if last_collected else "아직 수집된 뉴스가 없습니다.")

st.divider()

filter_col1, filter_col2 = st.columns([2, 1])
with filter_col1:
    keywords = ["전체"] + svc.get_keywords()
    keyword_choice = st.selectbox("검색 키워드", keywords)
with filter_col2:
    sort_order = st.radio("정렬", ["최신순", "오래된순"], horizontal=True)

search_keyword = None if keyword_choice == "전체" else keyword_choice
news_df = svc.get_news_list(search_keyword=search_keyword, limit=30)

if news_df.empty:
    st.info(
        "표시할 뉴스가 없습니다. DB가 아직 준비되지 않았거나 뉴스 수집이 실행되지 않았을 수 있습니다.",
        icon="📭",
    )
else:
    if sort_order == "오래된순":
        news_df = news_df.sort_values("published_at")
    st.caption(f"최대 30건까지 표시됩니다. (현재 {len(news_df)}건)")

    for _, row in news_df.iterrows():
        with st.container(border=True):
            st.markdown(f"#### {row['title']}")
            meta = []
            if row.get("publisher"):
                meta.append(str(row["publisher"]))
            if row.get("published_at") is not None and str(row["published_at"]) != "NaT":
                meta.append(str(row["published_at"]))
            if row.get("search_keyword"):
                meta.append(f"검색어: {row['search_keyword']}")
            if meta:
                st.caption(" · ".join(meta))
            if row.get("description"):
                st.write(row["description"])
            if row.get("original_url"):
                st.markdown(f"[원문 보기]({row['original_url']})")
