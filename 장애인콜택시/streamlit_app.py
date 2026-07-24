"""
서울시 장애인 콜택시 이용현황 분석 및 자동차 보조기구 지원 조회 시스템
-----------------------------------------------------------------
UI/UX 프로토타입 (Mockup)

- 목적: 데이터 조회 프로그램(Streamlit GUI)의 화면 설계 우선 구현
- 규칙: 실제 크롤링/DB 연결 없음. 모든 데이터는 코드 내부 더미(Dummy) 데이터.
- 실행: streamlit run streamlit_app.py
- 의존성: streamlit, pandas, plotly
"""

import random
from datetime import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------------------- #
# 전역 설정 및 상수
# --------------------------------------------------------------------------- #
st.set_page_config(
    page_title="서울시 장애인 콜택시 · 자동차 보조기구 조회 시스템",
    page_icon="🦽",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 색상 톤: Blue / White / Gray
PRIMARY = "#1f6feb"
PRIMARY_DARK = "#0d47a1"
GRAY = "#6b7280"

# 서울시 25개 자치구
SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구",
    "광진구", "구로구", "금천구", "노원구", "도봉구",
    "동대문구", "동작구", "마포구", "서대문구", "서초구",
    "성동구", "성북구", "송파구", "양천구", "영등포구",
    "용산구", "은평구", "종로구", "중구", "중랑구",
]

DISABILITY_TYPES = ["지체장애", "뇌병변장애", "시각장애", "청각장애", "지적장애", "기타"]
DEVICE_TYPES = ["운전보조장치", "승하차보조장치", "휠체어고정장치", "핸드컨트롤", "좌석회전장치"]
MANUFACTURERS = ["오토모빌케어", "무브프리", "케어드라이브", "베리어프리텍", "이지모빌리티"]


# --------------------------------------------------------------------------- #
# 스타일 (Bootstrap 느낌의 대시보드)
# --------------------------------------------------------------------------- #
def inject_style() -> None:
    """페이지 전역 CSS를 주입한다."""
    st.markdown(
        f"""
        <style>
        .main {{ background-color: #f5f7fa; }}
        .block-container {{ padding-top: 2rem; }}
        h1, h2, h3 {{ color: {PRIMARY_DARK}; }}
        div[data-testid="stMetric"] {{
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-left: 5px solid {PRIMARY};
            border-radius: 10px;
            padding: 16px 18px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.06);
        }}
        .device-card {{
            background:#ffffff; border:1px solid #e5e7eb; border-radius:12px;
            padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.06); height:100%;
        }}
        .badge-ok {{ background:#e6f4ea; color:#1e7e34; padding:2px 10px;
            border-radius:12px; font-size:0.8rem; font-weight:600; }}
        .badge-no {{ background:#fdecea; color:#c62828; padding:2px 10px;
            border-radius:12px; font-size:0.8rem; font-weight:600; }}
        .hero {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
            color:#fff; padding:28px 32px; border-radius:16px; margin-bottom:8px;
        }}
        .hero h1 {{ color:#fff; margin:0 0 6px 0; }}
        .hero p {{ color:#e3ecff; margin:0; font-size:1.02rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# 더미 데이터 생성 (실제 DB/CSV 대신 코드에서 생성)
# --------------------------------------------------------------------------- #
@st.cache_data
def make_taxi_usage() -> pd.DataFrame:
    """자치구 × 연도 × 월 단위 콜택시 이용현황 더미 데이터."""
    random.seed(42)
    rows = []
    for year in (2022, 2023, 2024):
        for month in range(1, 13):
            for gu in SEOUL_DISTRICTS:
                rows.append(
                    {
                        "연도": year,
                        "월": month,
                        "자치구": gu,
                        "이용건수": random.randint(300, 2500),
                        "평균대기시간(분)": random.randint(15, 70),
                        "운행차량수": random.randint(3, 25),
                    }
                )
    return pd.DataFrame(rows)


@st.cache_data
def make_devices() -> pd.DataFrame:
    """자동차 보조기구 더미 데이터."""
    random.seed(7)
    products = [
        "핸드 컨트롤 브레이크", "회전형 운전석 시트", "휠체어 자동 리프트",
        "전동 승하차 발판", "손 조작 액셀 레버", "휠체어 고정 벨트 시스템",
        "좌측 액셀 페달", "스티어링 노브", "자동 도어 오프너", "슬라이딩 보드",
    ]
    rows = []
    for i, name in enumerate(products):
        rows.append(
            {
                "제품명": name,
                "장애유형": random.choice(DISABILITY_TYPES),
                "종류": random.choice(DEVICE_TYPES),
                "제조사": random.choice(MANUFACTURERS),
                "가격": random.randint(15, 320) * 10000,
                "지원여부": random.choice(["지원", "지원", "미지원"]),
                "설명": f"{name} 제품으로 안전한 승하차와 운전을 보조합니다.",
            }
        )
    return pd.DataFrame(rows)


@st.cache_data
def make_policies() -> pd.DataFrame:
    """지원정책 더미 데이터."""
    rows = [
        ("서울시", "장애인 자동차 보조기구 지원사업", "최대 200만원",
         "등록 장애인(지체·뇌병변)", "2024.03 ~ 2024.11", "서울 전역"),
        ("한국장애인고용공단", "출퇴근 차량 개조 지원", "최대 300만원",
         "취업 장애인", "상시", "전국"),
        ("서울시설공단", "장애인 콜택시 이용 지원", "이용요금 감면",
         "보행상 장애인", "상시", "서울 전역"),
        ("보건복지부", "자동차 손 조작장치 지원", "최대 150만원",
         "1~3급 지체장애", "2024.01 ~ 2024.12", "전국"),
        ("강남구청", "장애인 이동편의 개조비 지원", "최대 100만원",
         "관내 등록 장애인", "2024.04 ~ 2024.09", "강남구"),
        ("경기도", "장애인 차량 리프트 설치 지원", "최대 250만원",
         "중증 장애인", "2024.02 ~ 2024.10", "경기 전역"),
    ]
    return pd.DataFrame(
        rows,
        columns=["기관", "정책명", "지원금", "대상", "신청기간", "지역"],
    )


@st.cache_data
def make_faqs() -> pd.DataFrame:
    """FAQ 더미 데이터."""
    rows = [
        ("이용방법", "장애인 콜택시는 어떻게 신청하나요?",
         "전화(1588-4388) 또는 모바일 앱을 통해 사전 예약 및 즉시 호출이 가능합니다."),
        ("이용방법", "콜택시 이용 요금은 얼마인가요?",
         "일반 택시 대비 감면된 요금이 적용되며, 거리와 시간에 따라 산정됩니다."),
        ("자격", "누가 장애인 콜택시를 이용할 수 있나요?",
         "보행상 장애가 있는 등록 장애인 및 일시적 이동 제약자가 이용 대상입니다."),
        ("보조기구", "자동차 보조기구 지원은 어디서 신청하나요?",
         "거주지 관할 구청 또는 서울시 복지포털을 통해 신청할 수 있습니다."),
        ("보조기구", "보조기구 지원금은 얼마까지 받을 수 있나요?",
         "품목과 정책에 따라 다르며, 최대 300만원까지 지원되는 사업이 있습니다."),
        ("기타", "이용 통계 데이터는 어디서 확인하나요?",
         "본 시스템의 '이용현황' 메뉴에서 자치구·연도·월별 통계를 조회할 수 있습니다."),
    ]
    return pd.DataFrame(rows, columns=["카테고리", "질문", "답변"])


# --------------------------------------------------------------------------- #
# 페이지: 홈
# --------------------------------------------------------------------------- #
def page_home(taxi: pd.DataFrame, devices: pd.DataFrame,
              policies: pd.DataFrame, faqs: pd.DataFrame) -> None:
    """홈 대시보드 화면."""
    st.markdown(
        """
        <div class="hero">
            <h1>🦽 서울시 장애인 콜택시 · 자동차 보조기구 지원 조회 시스템</h1>
            <p>장애인 콜택시 이용현황을 분석하고, 자동차 보조기구 및 지원정책을
            한 곳에서 조회할 수 있는 통합 정보 시스템입니다.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("총 콜택시 이용건수", f"{taxi['이용건수'].sum():,} 건")
    col2.metric("등록된 보조기구 수", f"{len(devices)} 종")
    col3.metric("지원정책 수", f"{len(policies)} 건")
    col4.metric("등록 FAQ 수", f"{len(faqs)} 건")

    st.write("")
    with st.container(border=True):
        st.subheader("📌 이용 안내")
        st.markdown(
            """
            - **📊 이용현황**: 연도·월·자치구별 장애인 콜택시 이용 통계를 그래프로 확인합니다.
            - **🦽 보조기구 조회**: 장애유형·종류·제조사 조건으로 자동차 보조기구를 검색합니다.
            - **🏛 지원정책 조회**: 지역·대상·기관별 지원정책을 표로 조회합니다.
            - **❓ FAQ**: 자주 묻는 질문을 카테고리별로 확인합니다.

            > 본 화면은 UI 프로토타입이며, 표시되는 데이터는 예시(Dummy) 데이터입니다.
            """
        )


# --------------------------------------------------------------------------- #
# 페이지: 콜택시 이용현황
# --------------------------------------------------------------------------- #
def page_usage(taxi: pd.DataFrame) -> None:
    """콜택시 이용현황 조회 및 시각화 화면."""
    st.header("📊 서울시 장애인 콜택시 이용현황")

    with st.container(border=True):
        st.markdown("**🔎 검색 조건**")
        c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1])
        year = c1.selectbox("연도", sorted(taxi["연도"].unique()), index=2)
        month = c2.selectbox("월", ["전체"] + list(range(1, 13)))
        gu = c3.selectbox("자치구", ["전체"] + SEOUL_DISTRICTS)
        c4.write("")
        c4.write("")
        search = c4.button("🔍 조회", use_container_width=True, type="primary")

    # 조건 필터링
    df = taxi[taxi["연도"] == year].copy()
    if month != "전체":
        df = df[df["월"] == month]
    if gu != "전체":
        df = df[df["자치구"] == gu]

    if not search:
        st.info("검색 조건을 선택하고 **조회** 버튼을 눌러주세요. (아래는 기본 미리보기)")

    tab1, tab2, tab3 = st.tabs(["📋 조회 결과", "📊 그래프 분석", "📈 추이"])

    with tab1:
        st.dataframe(df, use_container_width=True, hide_index=True)
        st.caption(f"총 {len(df):,} 건 조회됨")

    with tab2:
        col_a, col_b = st.columns(2)
        by_gu = (
            df.groupby("자치구", as_index=False)["이용건수"].sum()
            .sort_values("이용건수", ascending=False)
        )
        fig_bar = px.bar(
            by_gu, x="자치구", y="이용건수",
            title="자치구별 이용건수", color_discrete_sequence=[PRIMARY],
        )
        col_a.plotly_chart(fig_bar, use_container_width=True)

        top = by_gu.head(7)
        fig_pie = px.pie(
            top, names="자치구", values="이용건수",
            title="이용건수 상위 자치구 비율", hole=0.4,
        )
        col_b.plotly_chart(fig_pie, use_container_width=True)

    with tab3:
        trend = (
            taxi[taxi["연도"] == year]
            .groupby("월", as_index=False)["이용건수"].sum()
        )
        fig_line = px.line(
            trend, x="월", y="이용건수", markers=True,
            title=f"{year}년 월별 이용건수 추이",
            color_discrete_sequence=[PRIMARY_DARK],
        )
        fig_line.update_xaxes(dtick=1)
        st.plotly_chart(fig_line, use_container_width=True)


# --------------------------------------------------------------------------- #
# 페이지: 자동차 보조기구 조회
# --------------------------------------------------------------------------- #
def page_devices(devices: pd.DataFrame) -> None:
    """자동차 보조기구 카드형 조회 화면."""
    st.header("🦽 자동차 보조기구 조회")

    with st.container(border=True):
        st.markdown("**🔎 검색 조건**")
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 0.8])
        d_type = c1.selectbox("장애유형", ["전체"] + DISABILITY_TYPES)
        kind = c2.selectbox("보조기구 종류", ["전체"] + DEVICE_TYPES)
        maker = c3.selectbox("제조사", ["전체"] + MANUFACTURERS)
        c4.write("")
        c4.write("")
        c4.button("🔍 검색", use_container_width=True, type="primary")

    df = devices.copy()
    if d_type != "전체":
        df = df[df["장애유형"] == d_type]
    if kind != "전체":
        df = df[df["종류"] == kind]
    if maker != "전체":
        df = df[df["제조사"] == maker]

    st.caption(f"총 {len(df)} 개 제품 검색됨")
    st.write("")

    if df.empty:
        st.warning("검색 조건에 맞는 보조기구가 없습니다.")
        return

    # 카드 3열 그리드 출력
    cols = st.columns(3)
    for idx, (_, row) in enumerate(df.iterrows()):
        badge = (
            '<span class="badge-ok">지원 가능</span>'
            if row["지원여부"] == "지원"
            else '<span class="badge-no">지원 불가</span>'
        )
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class="device-card">
                    <img src="https://placehold.co/300x160/1f6feb/ffffff?text=Device"
                         style="width:100%;border-radius:8px;margin-bottom:10px;"/>
                    <h4 style="margin:0 0 6px 0;">{row['제품명']}</h4>
                    <div style="color:{GRAY};font-size:0.85rem;margin-bottom:6px;">
                        {row['제조사']} · {row['종류']}
                    </div>
                    <div style="font-weight:700;color:{PRIMARY_DARK};font-size:1.1rem;">
                        {row['가격']:,}원
                    </div>
                    <div style="margin:8px 0;">{badge}</div>
                    <div style="color:{GRAY};font-size:0.85rem;">{row['설명']}</div>
                </div>
                <div style="height:16px;"></div>
                """,
                unsafe_allow_html=True,
            )


# --------------------------------------------------------------------------- #
# 페이지: 지원정책 조회
# --------------------------------------------------------------------------- #
def page_policy(policies: pd.DataFrame) -> None:
    """지원정책 표 조회 화면."""
    st.header("🏛 지원정책 조회")

    with st.container(border=True):
        st.markdown("**🔎 검색 조건**")
        c1, c2, c3, c4 = st.columns([1.2, 1.2, 1.2, 0.8])
        region = c1.selectbox("지역", ["전체"] + sorted(policies["지역"].unique()))
        target = c2.text_input("지원대상 (키워드)", placeholder="예: 지체장애")
        org = c3.selectbox("기관", ["전체"] + list(policies["기관"].unique()))
        c4.write("")
        c4.write("")
        c4.button("🔍 조회", use_container_width=True, type="primary")

    df = policies.copy()
    if region != "전체":
        df = df[df["지역"] == region]
    if org != "전체":
        df = df[df["기관"] == org]
    if target.strip():
        df = df[df["대상"].str.contains(target.strip())]

    st.caption(f"총 {len(df)} 건의 정책이 조회되었습니다.")
    st.dataframe(df, use_container_width=True, hide_index=True)


# --------------------------------------------------------------------------- #
# 페이지: FAQ
# --------------------------------------------------------------------------- #
def page_faq(faqs: pd.DataFrame) -> None:
    """FAQ 아코디언 화면."""
    st.header("❓ 자주 묻는 질문 (FAQ)")

    c1, c2 = st.columns([2, 1])
    keyword = c1.text_input("검색어", placeholder="궁금한 내용을 입력하세요")
    category = c2.selectbox("카테고리", ["전체"] + list(faqs["카테고리"].unique()))

    df = faqs.copy()
    if category != "전체":
        df = df[df["카테고리"] == category]
    if keyword.strip():
        mask = df["질문"].str.contains(keyword.strip()) | df["답변"].str.contains(keyword.strip())
        df = df[mask]

    st.write("")
    if df.empty:
        st.warning("검색 결과가 없습니다.")
        return

    for _, row in df.iterrows():
        with st.expander(f"[{row['카테고리']}] {row['질문']}"):
            st.write(row["답변"])


# --------------------------------------------------------------------------- #
# 페이지: 데이터베이스 설계 (필수 산출물 ①)
# --------------------------------------------------------------------------- #
def page_schema() -> None:
    """DB 설계 문서 화면 — 테이블 스키마와 관계를 문서화한다."""
    st.header("🗄 데이터베이스 설계 (스키마 문서)")
    st.caption("필수 산출물 ① · 실제 MySQL 적재 전 설계안입니다.")

    schema = {
        "taxi_usage (콜택시 이용현황)": [
            ("usage_id", "INT PK AUTO_INCREMENT", "이용 레코드 고유번호"),
            ("year", "INT", "이용 연도"),
            ("month", "INT", "이용 월"),
            ("district_id", "INT FK → district", "자치구 코드"),
            ("use_count", "INT", "이용 건수"),
            ("avg_wait_min", "INT", "평균 대기시간(분)"),
            ("vehicle_count", "INT", "운행 차량 수"),
        ],
        "assistive_device (자동차 보조기구)": [
            ("device_id", "INT PK AUTO_INCREMENT", "보조기구 고유번호"),
            ("name", "VARCHAR(100)", "제품명"),
            ("disability_type", "VARCHAR(30)", "적용 장애유형"),
            ("device_type", "VARCHAR(30)", "보조기구 종류"),
            ("manufacturer", "VARCHAR(50)", "제조사"),
            ("price", "INT", "가격(원)"),
            ("is_supported", "BOOLEAN", "지원 여부"),
            ("description", "TEXT", "제품 설명"),
        ],
        "support_policy (지원정책)": [
            ("policy_id", "INT PK AUTO_INCREMENT", "정책 고유번호"),
            ("organization", "VARCHAR(80)", "주관 기관"),
            ("policy_name", "VARCHAR(120)", "정책명"),
            ("support_amount", "VARCHAR(50)", "지원금"),
            ("target", "VARCHAR(80)", "지원 대상"),
            ("apply_period", "VARCHAR(50)", "신청 기간"),
            ("region", "VARCHAR(30)", "지원 지역"),
        ],
        "district (자치구 코드)": [
            ("district_id", "INT PK", "자치구 코드"),
            ("district_name", "VARCHAR(20)", "자치구 이름"),
        ],
        "faq (자주 묻는 질문)": [
            ("faq_id", "INT PK AUTO_INCREMENT", "FAQ 고유번호"),
            ("category", "VARCHAR(30)", "카테고리"),
            ("question", "VARCHAR(200)", "질문"),
            ("answer", "TEXT", "답변"),
        ],
    }

    for table, cols in schema.items():
        with st.expander(f"📑 {table}", expanded=(table.startswith("taxi"))):
            df = pd.DataFrame(cols, columns=["컬럼명", "타입/제약", "설명"])
            st.dataframe(df, use_container_width=True, hide_index=True)

    with st.container(border=True):
        st.subheader("🔗 테이블 관계 (ERD 요약)")
        st.code(
            """
district (1) ──< (N) taxi_usage      # 자치구별 이용현황
assistive_device                     # 독립 마스터 테이블
support_policy                       # 독립 마스터 테이블
faq                                  # 독립 마스터 테이블
            """,
            language="text",
        )
        st.caption("※ 콜택시 이용현황은 자치구(district)와 1:N 관계로 연결됩니다.")


# --------------------------------------------------------------------------- #
# 페이지: 수집 데이터 (필수 산출물 ②)
# --------------------------------------------------------------------------- #
def page_rawdata(taxi: pd.DataFrame, devices: pd.DataFrame,
                 policies: pd.DataFrame) -> None:
    """수집 데이터 화면 — 크롤링으로 확보할 원본 데이터 형태를 보여준다."""
    st.header("📁 수집 데이터 (원본)")
    st.caption("필수 산출물 ② · BeautifulSoup/Selenium으로 수집 예정인 원본 형태 예시입니다.")

    sources = {
        "🚕 콜택시 이용현황": (
            taxi, "서울시설공단 / 서울 열린데이터광장 (예시)"),
        "🦽 자동차 보조기구": (
            devices, "보조기구 제조사·복지몰 상세페이지 (예시)"),
        "🏛 지원정책": (
            policies, "각 기관 복지정책 안내 페이지 (예시)"),
    }

    tabs = st.tabs(list(sources.keys()))
    for tab, (label, (df, source)) in zip(tabs, sources.items()):
        with tab:
            c1, c2 = st.columns(2)
            c1.metric("수집 행 수", f"{len(df):,} 행")
            c2.metric("컬럼 수", f"{df.shape[1]} 개")
            st.markdown(f"**데이터 출처:** {source}")
            st.dataframe(df.head(50), use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ CSV 다운로드",
                df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{label}.csv",
                mime="text/csv",
                use_container_width=False,
            )


# --------------------------------------------------------------------------- #
# 페이지: 프로젝트 소개
# --------------------------------------------------------------------------- #
def page_about() -> None:
    """프로젝트 소개 화면."""
    st.header("ℹ 프로젝트 소개")

    with st.container(border=True):
        st.subheader("🎯 프로젝트 목적")
        st.markdown(
            """
            서울시 장애인 콜택시의 이용현황을 분석하고, 자동차 보조기구 및 관련
            지원정책 정보를 통합 제공하여 **장애인의 이동권 향상**과
            **정보 접근성 개선**을 지원한다.
            """
        )

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("🛠 기술 스택")
            st.markdown(
                """
                - **Python** — 전체 백엔드/수집 로직
                - **BeautifulSoup** — 정적 페이지 크롤링
                - **Selenium** — 동적 페이지 크롤링
                - **MySQL** — 데이터베이스 저장소
                - **PyMySQL** — Python ↔ MySQL 연동
                - **Streamlit** — 데이터 조회 GUI
                """
            )
    with col2:
        with st.container(border=True):
            st.subheader("📦 필수 산출물")
            st.markdown(
                """
                1. **데이터베이스 설계 문서**
                2. **수집 데이터**
                3. **데이터 조회 프로그램** (현재 화면)
                """
            )

    with st.container(border=True):
        st.subheader("🗂 프로젝트 구조 (예정)")
        st.code(
            """
bootcamp-seoul-taxi-system/
├── crawler/            # BeautifulSoup / Selenium 수집 코드
│   ├── taxi_crawler.py
│   └── device_crawler.py
├── db/                 # MySQL 스키마 및 적재 스크립트
│   ├── schema.sql
│   └── loader.py
├── streamlit_app.py    # 데이터 조회 GUI (본 파일)
└── requirements.txt
            """,
            language="text",
        )


# --------------------------------------------------------------------------- #
# 메인 라우팅
# --------------------------------------------------------------------------- #
def main() -> None:
    """사이드바 메뉴 기반 페이지 라우팅."""
    inject_style()

    taxi = make_taxi_usage()
    devices = make_devices()
    policies = make_policies()
    faqs = make_faqs()

    with st.sidebar:
        st.markdown(f"### 🦽 통합 조회 시스템")
        st.caption("서울시 장애인 콜택시 · 보조기구 지원")
        st.divider()
        menu = st.radio(
            "메뉴",
            [
                "🏠 홈",
                "📊 이용현황",
                "🦽 보조기구 조회",
                "🏛 지원정책 조회",
                "❓ FAQ",
                "🗄 DB 설계",
                "📁 수집 데이터",
                "ℹ 프로젝트 소개",
            ],
            label_visibility="collapsed",
        )
        st.divider()
        st.caption(f"© {datetime.now().year} 부트캠프 팀 프로젝트")
        st.caption("⚠ 표시 데이터는 예시(Dummy)입니다.")

    if menu == "🏠 홈":
        page_home(taxi, devices, policies, faqs)
    elif menu == "📊 이용현황":
        page_usage(taxi)
    elif menu == "🦽 보조기구 조회":
        page_devices(devices)
    elif menu == "🏛 지원정책 조회":
        page_policy(policies)
    elif menu == "❓ FAQ":
        page_faq(faqs)
    elif menu == "🗄 DB 설계":
        page_schema()
    elif menu == "📁 수집 데이터":
        page_rawdata(taxi, devices, policies)
    else:
        page_about()


if __name__ == "__main__":
    main()
