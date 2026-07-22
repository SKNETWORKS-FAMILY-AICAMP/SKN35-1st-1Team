# -*- coding: utf-8 -*-
"""
app.py — 홈 (장애인 자동차 지원 시스템)
--------------------------------------------------
실행: streamlit run app.py
좌측 사이드바에서 페이지 이동.
"""
import streamlit as st

from lib import db, ui

ui.setup("장애인 자동차 지원 시스템", "🚗")


def data_mode_badge():
    if db.using_db():
        st.sidebar.success("🟢 DB 모드 (MySQL 연결됨)")
    else:
        st.sidebar.warning("🟡 샘플 데이터 모드\n(.streamlit/secrets.toml 설정 시 DB 전환)")


data_mode_badge()

ui.hero(
    "장애인 자동차 지원 시스템",
    "지역·대상(보훈·산재·일반)별 국가 지원사업 비교부터 합법 개조·검사, 검증된 구매처, "
    "주변 편의시설과 FAQ까지 — 필요한 정보를 한 곳에서.",
)

st.subheader("📑 메뉴")
c1, c2, c3 = st.columns(3)
with c1:
    with st.container(border=True):
        st.markdown("### 📊 지원정책 비교")
        st.markdown(
            "- 지역/대상 입력 → **지원금 한도 비교**\n"
            "- 보훈·산재 **맞춤형 정보**\n"
            "- 국가보훈부·근로복지공단 **게시판**"
        )
        st.page_link("pages/1_지원정책_비교.py", label="바로가기 →")
with c2:
    with st.container(border=True):
        st.markdown("### 🛒 구매 절차")
        st.markdown(
            "- **판매자/업체 리스트업** (사진·리뷰·상세)\n"
            "- 합법 **개조·검사 절차** + 지역 지도\n"
            "- 신청 서류 안내 · 교통안전공단 연계"
        )
        st.page_link("pages/2_구매절차.py", label="바로가기 →")
with c3:
    with st.container(border=True):
        st.markdown("### ℹ️ 추가 정보·FAQ")
        st.markdown(
            "- 도별 **차량 등록 통계 그래프**\n"
            "- 위치기반 **편의시설 지도**\n"
            "- 보조기구 **FAQ 게시판**"
        )
        st.page_link("pages/3_추가정보_FAQ.py", label="바로가기 →")

st.divider()
with st.expander("🛠 기술 구성 / 팀 개발 메모"):
    st.markdown(
        """
- **데이터 수집:** Python + BeautifulSoup / Selenium (기관 공고·업체·통계 크롤링)
- **저장:** MySQL (`sql/schema.sql` 참고 — 6개 테이블)
- **연동/조회:** `lib/db.py` (DB 연결 시 자동 전환, 실패 시 `lib/sample_data.py` 폴백)
- **화면:** Streamlit 멀티페이지 (`app.py` + `pages/`)

**팀원 작업 포인트**
1. `sql/schema.sql` 로 DB 생성 → `.streamlit/secrets.toml` 에 접속정보 입력
2. 크롤러가 수집한 데이터를 각 테이블에 INSERT
3. `lib/db.py` 의 `# TODO(DB)` 주석 부분에 실제 SELECT 문 채우기
   (함수 시그니처/반환형은 그대로 두면 화면은 수정 불필요)
        """
    )
st.caption("⚠ 현재 표시되는 수치·업체·자격요건은 화면 확인용 샘플입니다. 실제 값과 다를 수 있습니다.")
