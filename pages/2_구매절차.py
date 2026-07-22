# -*- coding: utf-8 -*-
"""페이지 2 — 구매 절차: 판매자 리스트업 / 합법 개조·검사 / 서류·기관 연계"""
import streamlit as st

from lib import db, sample_data as sd, ui

ui.setup("구매 절차", "🛒")
ui.brandbar()
st.title("🛒 구매 절차")

tab1, tab2, tab3 = st.tabs(["판매자·업체 리스트", "합법 개조·검사 절차", "신청 서류·기관 연계"])

# ============================ 탭 1: 판매자 리스트업 (엔카 스타일) ============================
with tab1:
    st.markdown("판매 업체/판매자를 **사진·리뷰·연락처**와 함께 확인하고, 상호를 누르면 **상세페이지**로 이동합니다.")
    region = st.selectbox("지역 필터", ["전체"] + sd.REGIONS, key="seller_region")
    sellers = db.get_sellers(region=region)

    if "sel_seller" not in st.session_state:
        st.session_state.sel_seller = None

    if st.session_state.sel_seller is None:
        # ---- 목록 뷰 ----
        if sellers.empty:
            st.info("해당 지역 등록 판매자가 없습니다.")
        for _, s in sellers.iterrows():
            with st.container(border=True):
                photo, info, act = st.columns([1, 3, 1])
                with photo:
                    st.markdown(
                        "<div style='height:90px;background:#eef2f7;border-radius:8px;"
                        "display:flex;align-items:center;justify-content:center;font-size:34px'>🚙</div>",
                        unsafe_allow_html=True,
                    )
                with info:
                    st.markdown(f"#### {s['shop_name']}")
                    st.caption(f"📍 {s['region']}  ·  ⭐ {s['rating']} ({s['review_count']}개 리뷰)")
                    st.write(s["career"])
                    st.markdown(f"🔗 작업물/블로그: {s['portfolio_url']}")
                with act:
                    st.write("")
                    if st.button("상세보기 →", key=f"open_{s['id']}", use_container_width=True):
                        st.session_state.sel_seller = int(s["id"])
                        st.rerun()
    else:
        # ---- 상세 뷰 ----
        sid = st.session_state.sel_seller
        s = sellers[sellers["id"] == sid]
        if s.empty:
            s = db.get_sellers()[db.get_sellers()["id"] == sid]
        s = s.iloc[0]

        if st.button("← 목록으로"):
            st.session_state.sel_seller = None
            st.rerun()

        st.header(s["shop_name"])
        st.caption(f"📍 {s['region']}  ·  ⭐ {s['rating']} ({s['review_count']}개 리뷰)")
        left, right = st.columns([1, 1])
        with left:
            st.markdown(
                "<div style='height:180px;background:#eef2f7;border-radius:10px;"
                "display:flex;align-items:center;justify-content:center;font-size:64px'>🚙</div>",
                unsafe_allow_html=True,
            )
        with right:
            st.markdown(f"**전화:** {s['phone']}")
            st.markdown(f"**이메일:** {s['email']}")
            st.markdown(f"**작업자 이력:** {s['career']}")
            st.markdown(f"**작업물/블로그:** {s['portfolio_url']}")

        st.subheader("💬 리뷰")
        for rv in db.get_reviews(sid):
            with st.container(border=True):
                st.markdown(f"{'⭐' * int(rv['rating'])}  **{rv['author']}**")
                st.write(rv["content"])

        with st.form(f"review_form_{sid}"):
            st.markdown("**리뷰 작성**")
            rc1, rc2 = st.columns([1, 4])
            new_rate = rc1.selectbox("평점", [5, 4, 3, 2, 1], key=f"nr_{sid}")
            new_text = rc2.text_input("내용", key=f"nt_{sid}")
            if st.form_submit_button("등록"):
                st.success("리뷰가 등록되었습니다. (초안: DB 연동 시 seller_reviews 에 저장)")

# ============================ 탭 2: 합법 개조·검사 절차 + 지도 ============================
with tab2:
    st.markdown("보조기구 종류를 고르면 **필수 인허가·구조변경 절차**를 단계별로 보여줍니다.")
    device = st.selectbox("보조기구 종류", db.get_device_types(), key="device_type")

    steps = db.get_modification_steps(device)
    cols = st.columns(len(steps))
    for col, stp in zip(cols, steps):
        with col:
            with st.container(border=True):
                st.markdown(f"**{stp['title']}**")
                st.caption(stp["detail"])

    st.info("※ 손조작장치·리프트 등 장착은 한국교통안전공단 **구조변경(튜닝) 승인 + 검사**가 필수입니다.")

    st.divider()
    st.markdown("##### 📍 우리 지역 공식 개조 공업사 / 검사소")
    reg = st.selectbox("거주 도시 선택", ["전체"] + sd.REGIONS, key="shop_region")
    shops = db.get_inspection_shops(region=reg)
    if shops.empty:
        st.info("해당 지역 정보가 없습니다. (샘플: 서울/경기/부산)")
    else:
        map_df = shops.rename(columns={"lat": "latitude", "lon": "longitude"})[["latitude", "longitude"]]
        st.map(map_df, zoom=6)
        for _, sh in shops.iterrows():
            icon = "🔧" if sh["kind"] == "공업사" else "🏢"
            st.markdown(f"- {icon} **{sh['name']}** ({sh['kind']}) — {sh['address']} · ☎ {sh['phone']}")

# ============================ 탭 3: 서류 안내 + 기관 연계 ============================
with tab3:
    st.markdown("기관마다 복잡한 신청 서류·절차를 정리하고, 신청 페이지로 바로 연결합니다.")

    with st.container(border=True):
        st.markdown("#### 📄 신청 서류 안내(자동 생성 초안)")
        cc1, cc2 = st.columns(2)
        name = cc1.text_input("성명")
        target = cc2.selectbox("대상 구분", sd.TARGET_TYPES)
        device2 = cc1.selectbox("장착 보조기구", db.get_device_types(), key="doc_device")
        region3 = cc2.selectbox("거주 지역", sd.REGIONS, key="doc_region")
        if st.button("서류 체크리스트 생성"):
            agency = {"보훈": "국가보훈부(관할 보훈지청)", "산재": "근로복지공단",
                      "일반": f"{region3} 관할 주민센터/지자체"}[target]
            st.success("아래 체크리스트를 참고해 준비하세요. (초안)")
            st.markdown(
                f"""
**신청인:** {name or '(성명)'} · **대상:** {target} · **지역:** {region3} · **보조기구:** {device2}

**제출 서류(예시)**
- [ ] 신청서 (해당 기관 양식)
- [ ] 장애인 등록증 / {target} 관련 증빙
- [ ] 자동차등록증 (본인 명의)
- [ ] 운전면허증 사본
- [ ] 견적서 (공식 개조 업체)
- [ ] 통장 사본

**접수처:** {agency}
                """
            )

    st.divider()
    st.markdown("#### 🔗 기관 · 대행 바로가기")
    b1, b2, b3 = st.columns(3)
    with b1:
        st.link_button("🚗 한국교통안전공단(구조변경)", "https://www.kotsa.or.kr", use_container_width=True)
    with b2:
        st.link_button("🎖 국가보훈부", "https://www.mpva.go.kr", use_container_width=True)
    with b3:
        st.link_button("🏭 근로복지공단", "https://www.comwel.or.kr", use_container_width=True)
    st.caption("대행 업체 링크 리스트는 DB(agency/대행 테이블) 연동 시 이 영역에 노출됩니다.")

st.caption("⚠ 표시 값·업체는 화면 확인용 샘플입니다.")
