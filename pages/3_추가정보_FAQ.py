# -*- coding: utf-8 -*-
"""페이지 3 — 추가 정보 및 FAQ: 등록 통계 / 편의시설 지도 / FAQ 게시판"""
import streamlit as st

from lib import db, sample_data as sd, ui

ui.setup("추가 정보·FAQ", "ℹ️")
ui.brandbar()
st.title("ℹ️ 추가 정보 및 FAQ")

tab1, tab2, tab3 = st.tabs(["차량 등록 통계", "편의시설 지도", "FAQ 게시판"])

# ============================ 탭 1: 도별 등록 통계 그래프 ============================
with tab1:
    st.markdown("거주 지역을 선택하면 해당 지역 **장애인 차량 등록 통계**를 그래프로 확인합니다.")
    stats = db.get_registration_stats()

    region = st.selectbox("지역 선택", sd.REGIONS, index=sd.REGIONS.index("서울"), key="stat_region")
    row = stats[stats["region"] == region]
    val = int(row["registered"].iloc[0]) if not row.empty else 0

    m1, m2, m3 = st.columns(3)
    m1.metric(f"{region} 등록 대수", f"{val:,}대")
    m2.metric("전국 합계", f"{int(stats['registered'].sum()):,}대")
    rank = stats.sort_values("registered", ascending=False).reset_index(drop=True)
    my_rank = rank.index[rank["region"] == region]
    m3.metric("전국 순위", f"{int(my_rank[0]) + 1}위 / {len(stats)}" if len(my_rank) else "-")

    st.markdown("##### 전국 도별 등록 현황 (2024, 샘플)")
    chart_df = stats.set_index("region")[["registered"]].rename(columns={"registered": "등록 대수"})
    st.bar_chart(chart_df, use_container_width=True)

# ============================ 탭 2: 편의시설 지도 (LBS) ============================
with tab2:
    st.markdown("거주지를 입력하면 근처 **장애인 주차구역 · 휠체어 충전소 · 편의시설**을 지도와 목록으로 안내합니다.")
    c1, c2 = st.columns([1, 2])
    region2 = c1.selectbox("거주 도시", sd.REGIONS, key="fac_region")
    kinds = c2.multiselect("시설 종류", ["주차", "충전", "편의"], default=["주차", "충전", "편의"])

    fac = db.get_facilities(region=region2, kinds=kinds)
    if fac.empty:
        st.info("해당 지역 등록 시설이 없습니다. (샘플: 서울/경기/부산)")
    else:
        map_df = fac.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]]
        st.map(map_df, zoom=6)
        icon = {"주차": "🅿️", "충전": "🔌", "편의": "♿"}
        for _, f in fac.iterrows():
            st.markdown(f"- {icon.get(f['kind'], '📍')} **{f['name']}** ({f['kind']}) — {f['address']}")

# ============================ 탭 3: FAQ 게시판 ============================
with tab3:
    st.markdown("장애인 차량 보조기구 관련 질문과 답변을 **게시판 형식**으로 확인하고 등록할 수 있습니다.")

    if "faq_extra" not in st.session_state:
        st.session_state.faq_extra = []

    kw = st.text_input("🔍 검색어 (질문 내용)", key="faq_kw")
    faqs = db.get_faqs() + st.session_state.faq_extra
    if kw:
        faqs = [f for f in faqs if kw in f["question"] or kw in (f.get("answer") or "")]

    if not faqs:
        st.info("검색 결과가 없습니다.")
    for f in faqs:
        with st.expander(f"[{f.get('category', '기타')}] {f['question']}"):
            st.write(f.get("answer") or "(답변 준비 중)")

    st.divider()
    with st.form("faq_form"):
        st.markdown("**질문 등록**")
        cat = st.selectbox("분류", ["개조/검사", "지원금", "구매", "등록", "기타"])
        q = st.text_input("질문")
        a = st.text_area("답변(선택)", height=80)
        if st.form_submit_button("등록"):
            if q.strip():
                st.session_state.faq_extra.insert(0, {"category": cat, "question": q, "answer": a})
                st.success("등록되었습니다. (초안: 세션 저장 / DB 연동 시 faqs 테이블에 INSERT)")
                st.rerun()
            else:
                st.error("질문을 입력해주세요.")

st.caption("⚠ 통계·시설 정보는 화면 확인용 샘플입니다.")
