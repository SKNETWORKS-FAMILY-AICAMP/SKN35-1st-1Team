"""
장애인 관련 뉴스 대시보드
- '뉴스' 버튼 클릭 → 하위 3개 버튼(장애인복지 / 장애인지원 / 장애인콜택시) 노출
- 하위 버튼 클릭 → keyword 컬럼 기준으로 필터링된 뉴스 카드 출력
"""

import streamlit as st
import pymysql
import pandas as pd

DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "1234",
    "database": "newsdb",
}

st.set_page_config(page_title="장애인 관련 뉴스", layout="wide")


@st.cache_data(ttl=300)
def load_news(where_clause: str) -> pd.DataFrame:
    conn = pymysql.connect(**DB_CONFIG)
    try:
        query = f"""
            SELECT headline, body, press, url, crawled_at
            FROM disability_news
            WHERE {where_clause}
            ORDER BY crawled_at DESC
        """
        df = pd.read_sql(query, conn)
    finally:
        conn.close()
    return df


# keyword 컬럼값과 정확히 일치시켜서 필터링 (CSV의 실제 keyword 값 기준)
SUB_CATEGORY_FILTERS = {
    "장애인복지": "keyword = '장애인 복지 서울'",
    "장애인지원": "keyword = '장애인 지원 서울'",
    "장애인콜택시": "keyword = '장애인 콜택시 서울'",
}

# ── 세션 상태 초기화 ──
if "show_news_menu" not in st.session_state:
    st.session_state.show_news_menu = False
if "selected_sub" not in st.session_state:
    st.session_state.selected_sub = None

st.title("♿ 장애인 관련 정보 사이트")

# ── 최상위 '뉴스' 버튼 ──
if st.button("📰 뉴스", use_container_width=False):
    st.session_state.show_news_menu = not st.session_state.show_news_menu  # 다시 누르면 접기

# ── '뉴스' 버튼을 눌렀을 때만 하위 3개 버튼 노출 ──
if st.session_state.show_news_menu:
    st.divider()
    col1, col2, col3 = st.columns(3)
    sub_buttons = [
        (col1, "장애인복지"),
        (col2, "장애인지원"),
        (col3, "장애인콜택시"),
    ]
    for col, label in sub_buttons:
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.selected_sub = label

    # ── 하위 버튼 중 하나가 선택된 상태면 해당 뉴스 목록 표시 ──
    if st.session_state.selected_sub:
        selected = st.session_state.selected_sub
        st.subheader(f"📌 {selected} 관련 뉴스")

        where_clause = SUB_CATEGORY_FILTERS[selected]
        df = load_news(where_clause)

        if df.empty:
            st.info("해당 카테고리에 수집된 뉴스가 없습니다.")
        else:
            st.caption(f"총 {len(df)}건")
            for _, row in df.iterrows():
                with st.container(border=True):
                    st.markdown(f"#### [{row['headline']}]({row['url']})")
                    st.write(row["body"] if row["body"] else "(본문 요약 없음)")
                    meta_col1, meta_col2 = st.columns([1, 1])
                    with meta_col1:
                        st.caption(f"📰 {row['press']}")
                    with meta_col2:
                        st.caption(f"🕓 수집일시: {row['crawled_at']}")
                        