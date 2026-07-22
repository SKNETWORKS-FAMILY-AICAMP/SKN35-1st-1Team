# -*- coding: utf-8 -*-
"""페이지 1 — 지원정책 비교 / 맞춤 조회 / 기관별 게시판"""
import streamlit as st

from lib import db, sample_data as sd, ui

ui.setup("지원정책 비교", "📊")
ui.brandbar()
st.title("📊 지원정책 비교")

tab1, tab2, tab3 = st.tabs(["지원금 한도 비교", "보훈·산재 맞춤 조회", "기관별 안내(게시판)"])

WON = lambda v: f"{int(v):,}원" if v is not None else "-"

# ============================ 탭 1: 지역/대상 입력 → 비교 ============================
with tab1:
    st.markdown("**지역**과 **대상**을 선택하면 수집된 지원사업 공고 기준으로 지원금 한도를 비교합니다.")
    c1, c2 = st.columns([1, 2])
    with c1:
        region = st.selectbox("지역", ["전체"] + sd.REGIONS, key="cmp_region")
    with c2:
        targets = st.multiselect("대상 (복수 선택)", sd.TARGET_TYPES, default=sd.TARGET_TYPES,
                                 key="cmp_targets")

    df = db.get_support_programs(region=region, targets=targets)

    if df.empty:
        st.info("조건에 맞는 지원사업이 없습니다. 지역/대상을 바꿔보세요.")
    else:
        top = df.sort_values("limit_amount", ascending=False)
        m1, m2, m3 = st.columns(3)
        m1.metric("검색된 사업 수", f"{len(df)}건")
        m2.metric("최대 지원 한도", WON(top.iloc[0]["limit_amount"]))
        m3.metric("평균 지원 한도", WON(df["limit_amount"].mean()))

        show = df[["region", "target_type", "agency", "program_name",
                   "support_item", "limit_amount", "eligibility"]].copy()
        show["limit_amount"] = show["limit_amount"].map(WON)
        show.columns = ["지역", "대상", "기관", "지원사업명", "지원항목", "지원금 한도", "자격조건"]
        st.dataframe(show, use_container_width=True, hide_index=True)

        st.markdown("##### 지원금 한도 비교 그래프")
        chart_df = df.assign(라벨=df["region"] + "·" + df["target_type"]).set_index("라벨")[["limit_amount"]]
        chart_df.columns = ["지원금 한도(원)"]
        st.bar_chart(chart_df, use_container_width=True)

        with st.expander("공고 원문 링크 보기"):
            for _, r in df.iterrows():
                st.markdown(f"- **{r['program_name']}** ({r['agency']}) — {r['source_url']}")

# ============================ 탭 2: 보훈/산재 맞춤 ============================
with tab2:
    st.markdown("**보훈** 또는 **산재** 대상을 선택하면 관련 지원사업과 자격요건을 모아 보여줍니다.")
    choice = st.radio("대상 선택", ["보훈", "산재"], horizontal=True, key="tailor_target")
    region2 = st.selectbox("지역(선택)", ["전체"] + sd.REGIONS, key="tailor_region")

    df2 = db.get_support_programs(region=region2, targets=[choice])
    if df2.empty:
        st.info(f"'{choice}' 대상 지원사업이 없습니다.")
    else:
        st.success(f"'{choice}' 관련 지원사업 {len(df2)}건")
        for _, r in df2.iterrows():
            with st.container(border=True):
                st.markdown(f"#### {r['program_name']}")
                a, b = st.columns([1, 1])
                a.markdown(f"**기관:** {r['agency']}\n\n**지역:** {r['region']}\n\n**지원항목:** {r['support_item']}")
                b.markdown(f"**지원금 한도:** {WON(r['limit_amount'])}\n\n**자격조건:** {r['eligibility']}")
                st.markdown(f"🔗 [공고 원문 바로가기]({r['source_url']})")

# ============================ 탭 3: 기관별 게시판 (입력 없음) ============================
with tab3:
    st.markdown("입력 없이 기관별 지원 항목과 수혜 자격 조건을 **게시판 형식**으로 안내합니다.")
    sec1, sec2 = st.columns(2)

    def render_board(col, agency, icon):
        with col:
            st.subheader(f"{icon} {agency}")
            for n in db.get_agency_notices(agency):
                with st.container(border=True):
                    st.markdown(f"**{n['title']}**")
                    st.caption(n["date"])
                    st.write(n["body"])

    render_board(sec1, "국가보훈부", "🎖")
    render_board(sec2, "근로복지공단", "🏭")

st.caption("⚠ 표시 값은 화면 확인용 샘플입니다. 실제 지원금·자격은 각 기관 공고를 확인하세요.")
