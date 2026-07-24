"""장애인콜택시 이용안내 FAQ."""
from __future__ import annotations

import streamlit as st

from components.accessibility import apply_accessibility_css
from components.disclaimer import render_data_freshness_note
from components.header import render_page_header
from components.navigation import render_home_link
from services import faq_service as svc

st.set_page_config(page_title="FAQ | 우리동네 장애인 콜택시", page_icon="❓", layout="wide")
apply_accessibility_css()
render_home_link()
render_page_header("장애인콜택시 이용안내 FAQ", "서울시설공단 장애인콜택시 공식 홈페이지 내용을 바탕으로 정리했습니다.")

st.warning("이용 기준과 요금 등은 변경될 수 있으므로 실제 이용 전 공식 홈페이지에서 다시 확인해 주세요.", icon="⚠️")

last_collected = svc.get_last_collected_at()
render_data_freshness_note(f"마지막 수집/확인 시각: {last_collected}" if last_collected else "아직 FAQ가 수집되지 않았습니다.")

st.divider()

filter_col1, filter_col2 = st.columns([1, 2])
with filter_col1:
    categories = ["전체"] + svc.get_categories()
    category_choice = st.selectbox("카테고리", categories)
with filter_col2:
    keyword = st.text_input("키워드 검색", placeholder="예: 요금, 휠체어, 취소")

category = None if category_choice == "전체" else category_choice
faq_df = svc.get_faq_list(category=category, keyword=keyword.strip() or None)

if faq_df.empty:
    st.info(
        "조건에 맞는 FAQ가 없습니다. DB가 아직 준비되지 않았거나 FAQ 수집이 실행되지 않았을 수 있습니다.\n\n"
        "관리자는 `uv run python collectors/collect_faq.py` 로 FAQ를 수집할 수 있습니다.",
        icon="📭",
    )
else:
    st.caption(f"총 {len(faq_df)}건의 FAQ가 있습니다.")
    for _, row in faq_df.iterrows():
        with st.expander(f"[{row['category']}] {row['question']}"):
            st.markdown(row["answer"])
            source_line = []
            if row.get("source_name"):
                source_line.append(str(row["source_name"]))
            if row.get("source_url"):
                source_line.append(f"[공식 출처 링크]({row['source_url']})")
            if source_line:
                st.caption(" · ".join(source_line))
            if row.get("updated_at"):
                st.caption(f"최종 업데이트: {row['updated_at']}")
