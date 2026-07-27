"""
해치타GO (Haechi Ta-GO) — 팀 통합 앱 (셸)
------------------------------------------
"해치와 소울 프렌즈가 함께 타고 달리는 따뜻한 이동 서비스"

  · 홈        → 브랜드 히어로 + 컨셉 일러스트 + 바로가기 카드 4개 (사이드바 없음)
  · 이용현황  → 담당: 팀원 (미구현 — 담당자 모듈 연결 예정)
  · 예약하기  → 담당: 팀원 (미구현 — 담당자 모듈 연결 예정)
  · FAQ       → 담당: 본인 ✅ app/faq_page.py 연결 완료
  · 관련뉴스  → 담당: 본인 ✅ 탭 + 2열 카드 그리드 + 검색 + 페이지네이션

접근성: 장애인 이용자 대상 — 큰 글씨·고대비·넓은 터치 영역.
실행 : streamlit run app/main_app.py
"""

from __future__ import annotations

import base64
import sys
from pathlib import Path

import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.faq_page import render as render_faq   # noqa: E402

st.set_page_config(
    page_title="해치타GO (Haechi Ta-GO)",
    page_icon="🚕",
    layout="wide",
    initial_sidebar_state="expanded",
)

PRIMARY = "#1a365d"
PRIMARY_DARK = "#0f2440"
ACCENT = "#2c5282"
WARM = "#e07b39"   # 따뜻한 포인트 컬러

BRAND_KO = "해치타GO"
BRAND_EN = "Haechi Ta-GO"
TAGLINE = "해치와 소울 프렌즈가 함께 타고 달리는 따뜻한 이동 서비스"

# 페이지 정의 (사이드바 순서 = NAV_ORDER, '홈'은 제외)
PAGES = {
    "home":    {"icon": "🏠", "label": "홈"},
    "usage":   {"icon": "📊", "label": "이용현황", "sub": "자치구별 대기시간 및\n실시간 차량 현황 확인", "owner": "팀원"},
    "reserve": {"icon": "📝", "label": "예약하기", "sub": "예약 정보 정리 도우미 및\n간편 예약 시스템 신청", "owner": "팀원"},
    "faq":     {"icon": "❓", "label": "FAQ",      "sub": "자주 묻는 질문과\n이용 방법 상세 안내", "owner": "본인"},
    "news":    {"icon": "📰", "label": "관련뉴스", "sub": "공지사항 및 장애인\n복지 관련 최신 소식", "owner": "본인"},
}
NAV_ORDER = ["usage", "reserve", "faq", "news"]   # 사이드바 (홈 없음)
TILE_ORDER = ["usage", "reserve", "faq", "news"]  # 홈 카드

# 관련뉴스 카테고리별 뱃지 색 (배경, 글자)
CATE_STYLE = {
    "복지사업": ("#e8eef6", "#1a365d"),
    "지원사업": ("#fef1e0", "#b45309"),
    "택시소식": ("#e4f5ec", "#0f7a44"),
}

NEWS_ITEMS = [
    {"cat": "복지사업", "date": "2026-07-24", "source": "보건복지부",
     "title": "장애인 활동지원 서비스 대상 확대·급여 시간 상향",
     "desc": "일상생활과 이동을 돕는 활동지원 급여 대상이 넓어지고 월 지원 시간이 늘어납니다. 신청은 주민센터·복지로에서 가능합니다.",
     "url": "https://www.mohw.go.kr"},
    {"cat": "지원사업", "date": "2026-07-22", "source": "한국장애인고용공단",
     "title": "자동차 손 조작장치 개조비 최대 300만원 지원",
     "desc": "취업 장애인의 출퇴근을 돕기 위한 차량 개조비를 확대 지원합니다. 공단 지사에서 상시 접수하며 심사 후 지급됩니다.",
     "url": "https://www.kead.or.kr"},
    {"cat": "택시소식", "date": "2026-07-20", "source": "서울시설공단",
     "title": "장애인콜택시 24시간 운영 전면 시행",
     "desc": "야간·새벽 이동 수요에 맞춰 전 차량이 24시간 연중무휴로 운영됩니다. 심야 배차가 늘어 대기시간이 단축될 전망입니다.",
     "url": "https://www.sisul.or.kr"},
    {"cat": "복지사업", "date": "2026-07-18", "source": "서울특별시",
     "title": "장애인 이동지원 바우처 신규 도입",
     "desc": "이동이 어려운 중증 장애인을 위한 교통 바우처가 신설되어 콜택시·바우처택시 요금을 추가로 지원합니다.",
     "url": "https://www.seoul.go.kr"},
    {"cat": "택시소식", "date": "2026-07-15", "source": "서울시설공단",
     "title": "즉시콜 배차 시스템 개선…실시간 위치 기반 매칭",
     "desc": "실시간 위치 기반 배차로 평균 대기시간이 줄고, 앱에서 배차 현황을 바로 확인할 수 있게 개선됩니다.",
     "url": "https://www.sisul.or.kr"},
    {"cat": "지원사업", "date": "2026-07-12", "source": "서울특별시",
     "title": "콜택시 이용요금 감면 확대·심야 할증 완화",
     "desc": "이용요금 감면 폭이 늘고 심야 시간대 할증이 완화됩니다. 등록 이용자에게 별도 신청 없이 자동 적용됩니다.",
     "url": "https://www.seoul.go.kr"},
    {"cat": "복지사업", "date": "2026-07-10", "source": "국토교통부",
     "title": "저상버스·장애인콜택시 운행 대수 확대",
     "desc": "휠체어 탑승이 가능한 차량이 늘어 지역 간 이동 편의가 개선됩니다. 단계적으로 차량이 증차될 예정입니다.",
     "url": "https://www.molit.go.kr"},
    {"cat": "택시소식", "date": "2026-07-08", "source": "서울시설공단",
     "title": "차세대 친환경 전기 콜택시 50대 추가 도입 완료",
     "desc": "저상 전기 차량 도입으로 휠체어 이용자의 승하차 편의를 높이고 대기환경 개선에도 기여할 전망입니다.",
     "url": "https://www.sisul.or.kr"},
    {"cat": "지원사업", "date": "2026-07-05", "source": "국민건강보험공단",
     "title": "보조기기 교부사업 품목에 휠체어 고정장치 추가",
     "desc": "차량용 휠체어 고정장치와 승하차 보조장치가 교부 품목에 새로 포함되어 지원 범위가 넓어집니다.",
     "url": "https://www.nhis.or.kr"},
    {"cat": "택시소식", "date": "2026-07-02", "source": "서울특별시",
     "title": "바우처택시 가맹 차량 확대…감면 이용 편의 향상",
     "desc": "일반 택시를 감면 요금으로 이용하는 바우처택시 가맹 차량이 늘어 즉시 이용 가능성이 높아집니다.",
     "url": "https://www.seoul.go.kr"},
    {"cat": "복지사업", "date": "2026-06-28", "source": "서울시설공단",
     "title": "'장애인의 날' 맞아 콜택시 무료 운행 이벤트",
     "desc": "장애인의 날 당일 서울 시내 전역에서 장애인콜택시를 무료로 이용할 수 있는 특별 이벤트가 진행됩니다.",
     "url": "https://www.sisul.or.kr"},
    {"cat": "지원사업", "date": "2026-06-25", "source": "한국장애인고용공단",
     "title": "중증장애인 출퇴근 통근버스 운영 지역 확대",
     "desc": "출퇴근에 어려움을 겪는 중증장애인을 위한 통근버스 노선과 운영 지역이 단계적으로 늘어납니다.",
     "url": "https://www.kead.or.kr"},
]

PER_PAGE = 6


# --------------------------------------------------------------------------- #
# 컨셉 일러스트 (SVG) — 분홍 해치 운전 + 소울 프렌즈 4종이 손 흔드는 장면
# --------------------------------------------------------------------------- #
def _friend(cx: int, body: str, dark: str) -> str:
    """소울 프렌즈 한 명 (손 흔드는 캐릭터)."""
    wave = (f'<path d="M{cx+15} 200 q16 -8 20 -26" stroke="{body}" stroke-width="7" '
            f'fill="none" stroke-linecap="round"/>')
    return f"""
    <g>
      <ellipse cx="{cx}" cy="210" rx="19" ry="24" fill="{body}" stroke="{dark}" stroke-width="3"/>
      <path d="M{cx-16} 214 q-8 3 -9 12" stroke="{body}" stroke-width="7" fill="none" stroke-linecap="round"/>
      {wave}
      <circle cx="{cx-6}" cy="204" r="2.6" fill="#3a2b2b"/>
      <circle cx="{cx+6}" cy="204" r="2.6" fill="#3a2b2b"/>
      <circle cx="{cx-10}" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
      <circle cx="{cx+10}" cy="210" r="3.4" fill="#ff9a9a" opacity="0.55"/>
      <path d="M{cx-6} 211 q6 5 12 0" stroke="#3a2b2b" stroke-width="2.4" fill="none" stroke-linecap="round"/>
      <ellipse cx="{cx-7}" cy="234" rx="6" ry="4" fill="{dark}"/>
      <ellipse cx="{cx+7}" cy="234" rx="6" ry="4" fill="{dark}"/>
    </g>"""


SCENE_SVG = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 720 300">
  <defs>
    <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffe9d6"/><stop offset="1" stop-color="#e4f1ff"/>
    </linearGradient>
  </defs>
  <rect width="720" height="300" rx="24" fill="url(#sky)"/>
  <circle cx="628" cy="60" r="38" fill="#ffd98a" opacity="0.9"/>
  <g fill="#ffffff" opacity="0.92">
    <ellipse cx="120" cy="54" rx="44" ry="19"/><ellipse cx="156" cy="60" rx="30" ry="15"/>
    <ellipse cx="452" cy="40" rx="32" ry="14"/>
  </g>
  <!-- 반짝임 -->
  <g fill="#ffb84d" opacity="0.9">
    <path d="M300 44 l3 8 8 3 -8 3 -3 8 -3 -8 -8 -3 8 -3 z"/>
    <path d="M486 96 l2 6 6 2 -6 2 -2 6 -2 -6 -6 -2 6 -2 z"/>
  </g>
  <!-- 바닥 -->
  <rect x="0" y="236" width="720" height="64" fill="#cdd8e8"/>
  <rect x="0" y="236" width="720" height="8" fill="#b9c6da"/>
  <g fill="#ffffff"><rect x="30" y="266" width="30" height="6" rx="3"/><rect x="96" y="266" width="30" height="6" rx="3"/><rect x="162" y="266" width="30" height="6" rx="3"/></g>

  <!-- 택시 -->
  <path d="M150 150 q6 -46 62 -50 l118 0 q42 4 54 50 z" fill="#ffd23f" stroke="#e0a500" stroke-width="4"/>
  <rect x="86" y="150" width="330" height="86" rx="26" fill="#ffd23f" stroke="#e0a500" stroke-width="4"/>
  <!-- 루프 사인 -->
  <rect x="298" y="86" width="62" height="22" rx="6" fill="#1a365d"/>
  <text x="329" y="102" text-anchor="middle" font-family="Arial, sans-serif" font-size="13" font-weight="800" fill="#ffffff">TAXI</text>
  <!-- 창문 -->
  <rect x="214" y="112" width="52" height="38" rx="8" fill="#d3ecff" stroke="#9cc8ee" stroke-width="2"/>
  <rect x="300" y="112" width="52" height="38" rx="8" fill="#d3ecff" stroke="#9cc8ee" stroke-width="2"/>
  <!-- 체커 스트라이프 -->
  <rect x="86" y="188" width="330" height="14" fill="#1a365d" opacity="0.92"/>
  <g fill="#ffffff">
    <rect x="92" y="190" width="10" height="10"/><rect x="112" y="190" width="10" height="10"/>
    <rect x="132" y="190" width="10" height="10"/><rect x="152" y="190" width="10" height="10"/>
    <rect x="172" y="190" width="10" height="10"/><rect x="192" y="190" width="10" height="10"/>
    <rect x="212" y="190" width="10" height="10"/><rect x="232" y="190" width="10" height="10"/>
    <rect x="252" y="190" width="10" height="10"/><rect x="272" y="190" width="10" height="10"/>
    <rect x="292" y="190" width="10" height="10"/><rect x="312" y="190" width="10" height="10"/>
    <rect x="332" y="190" width="10" height="10"/><rect x="352" y="190" width="10" height="10"/>
    <rect x="372" y="190" width="10" height="10"/><rect x="392" y="190" width="10" height="10"/>
  </g>
  <!-- 헤드라이트 -->
  <ellipse cx="408" cy="176" rx="8" ry="6" fill="#fff6cf" stroke="#e0a500" stroke-width="2"/>
  <!-- 바퀴 -->
  <circle cx="160" cy="236" r="24" fill="#2b2b33"/><circle cx="160" cy="236" r="10" fill="#c7ccd6"/>
  <circle cx="342" cy="236" r="24" fill="#2b2b33"/><circle cx="342" cy="236" r="10" fill="#c7ccd6"/>

  <!-- 해치 운전자 (왼쪽 창문) -->
  <path d="M240 92 l10 22 h-20 z" fill="#ffce54" stroke="#eab226" stroke-width="2"/>
  <circle cx="240" cy="132" r="22" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <ellipse cx="223" cy="126" rx="7" ry="9" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <ellipse cx="257" cy="126" rx="7" ry="9" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <circle cx="232" cy="130" r="3" fill="#3a2b2b"/><circle cx="248" cy="130" r="3" fill="#3a2b2b"/>
  <circle cx="228" cy="138" r="4" fill="#ff7aa8" opacity="0.6"/><circle cx="252" cy="138" r="4" fill="#ff7aa8" opacity="0.6"/>
  <path d="M232 140 q8 8 16 0" stroke="#3a2b2b" stroke-width="2.6" fill="none" stroke-linecap="round"/>

  <!-- 소울 프렌즈 4종 (배웅하며 손 흔들기) -->
  {_friend(504, "#7fd6b5", "#4bb691")}
  {_friend(560, "#7db8ff", "#5691e0")}
  {_friend(616, "#ffd93f", "#e9bd2a")}
  {_friend(670, "#ff8a80", "#e56b61")}
</svg>"""

FACE_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 60 60">
  <path d="M30 6 l7 13 h-14 z" fill="#ffce54"/>
  <circle cx="30" cy="34" r="21" fill="#ff9ec7" stroke="#f47ba9" stroke-width="2"/>
  <circle cx="22" cy="32" r="3" fill="#3a2b2b"/><circle cx="38" cy="32" r="3" fill="#3a2b2b"/>
  <circle cx="18" cy="40" r="4" fill="#ff7aa8" opacity="0.6"/><circle cx="42" cy="40" r="4" fill="#ff7aa8" opacity="0.6"/>
  <path d="M22 41 q8 8 16 0" stroke="#3a2b2b" stroke-width="3" fill="none" stroke-linecap="round"/>
</svg>"""


def _data_uri(svg: str) -> str:
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{b64}"


SCENE_URI = _data_uri(SCENE_SVG)
FACE_URI = _data_uri(FACE_SVG)


# --------------------------------------------------------------------------- #
# 스타일
# --------------------------------------------------------------------------- #
def inject_style() -> None:
    st.markdown(
        f"""
        <style>
        h1, h2, h3 {{ color:{PRIMARY_DARK}; }}

        /* ---------- 사이드바 ---------- */
        section[data-testid="stSidebar"] {{ background:#f7f9fc; border-right:1px solid #e5e7eb; }}
        .brand {{ display:flex; align-items:center; gap:12px; padding:8px 6px 4px;
            border-radius:12px; }}
        .brand, .brand *, .home-link {{ text-decoration:none !important; }}
        .brand:hover {{ background:#eef2f8; }}
        .brand img {{ width:42px; height:42px; }}
        .brand-name {{ font-size:1.2rem; font-weight:900; color:{PRIMARY}; line-height:1.15; }}
        .brand-name span {{ font-size:0.72rem; font-weight:700; color:#8a94a3; }}
        .brand-sub {{ font-size:0.76rem; color:#9aa4b2; margin-top:2px; }}
        .home-link {{ display:inline-block; margin:6px 6px 2px; font-size:0.86rem; font-weight:700;
            color:{ACCENT}; text-decoration:none; }}
        .home-link:hover {{ text-decoration:underline; }}
        .nav-cap {{ font-size:0.78rem; font-weight:700; letter-spacing:.04em; color:#8a94a3;
            margin:14px 6px 6px; text-transform:uppercase; }}
        [class*="st-key-nav_"] button {{ justify-content:flex-start !important; text-align:left;
            font-size:1.05rem; font-weight:700; border-radius:12px; padding:12px 14px;
            border:none; margin-bottom:2px; min-height:48px; }}
        [class*="st-key-nav_"] button p {{ font-size:1.05rem; font-weight:700; }}
        [class*="st-key-nav_"] button[kind="secondary"] {{ background:transparent; color:#374151; }}
        [class*="st-key-nav_"] button[kind="secondary"]:hover {{ background:#e8edf3; color:{PRIMARY}; }}
        [class*="st-key-nav_"] button[kind="primary"] {{ background:{PRIMARY}; color:#fff;
            box-shadow:0 2px 8px rgba(26,54,93,0.25); }}
        [class*="st-key-nav_"] button[kind="primary"] p {{ color:#fff; }}

        /* ---------- 홈 히어로 ---------- */
        .home-hero {{ text-align:center; padding:8px 0 2px; }}
        .hero-illust {{ width:100%; max-width:660px; height:auto; display:block; margin:0 auto 14px;
            border-radius:24px; box-shadow:0 10px 30px rgba(26,54,93,0.12); }}
        .hero-logo {{ font-size:2.7rem; font-weight:900; color:{PRIMARY}; letter-spacing:-.01em; }}
        .hero-logo .en {{ font-size:1.15rem; font-weight:800; color:#7c86a0; margin-left:10px; }}
        .hero-tag {{ font-size:1.18rem; color:{WARM}; font-weight:700; margin-top:8px; }}

        .home-h2 {{ text-align:center; margin:30px 0 4px; }}
        .home-h2 h2 {{ font-size:2rem; color:{PRIMARY}; margin:0; }}
        .home-h2 p {{ color:#6b7280; font-size:1.05rem; margin:10px 0 0; line-height:1.6; }}

        /* ---------- 홈 카드 4개 ---------- */
        .tilewrap {{ display:grid; grid-template-columns:1fr 1fr; gap:22px;
            max-width:860px; margin:22px auto 8px; }}
        .tilecard {{ display:block; background:#fff; border:1px solid #e6e9f0; border-radius:22px;
            padding:34px 28px; text-align:center;
            box-shadow:0 2px 10px rgba(0,0,0,0.05);
            transition:transform .15s ease, box-shadow .15s ease, border-color .15s ease; }}
        .tilecard, .tilecard * {{ text-decoration:none !important; }}
        .tilecard:hover {{ transform:translateY(-6px); box-shadow:0 16px 34px rgba(26,54,93,0.16);
            border-color:#cdd8ec; }}
        .tile-ico {{ width:76px; height:76px; margin:0 auto 16px; border-radius:22px;
            background:#e9edfb; display:flex; align-items:center; justify-content:center; font-size:2.3rem; }}
        .tile-title {{ font-size:1.5rem; font-weight:800; color:{PRIMARY}; margin-bottom:10px; }}
        .tile-sub {{ font-size:1.02rem; color:#6b7280; line-height:1.65; white-space:pre-line; }}

        /* ---------- 관련뉴스 ---------- */
        .stTabs [data-baseweb="tab"] {{ font-size:1.12rem; font-weight:700; padding:10px 20px; }}
        .stTabs [aria-selected="true"] {{ color:{PRIMARY}; }}
        .ncard {{ background:#fff; border:1px solid #e5e7eb; border-radius:16px; padding:20px 22px;
            margin-bottom:16px; box-shadow:0 1px 5px rgba(0,0,0,0.05); min-height:212px;
            display:flex; flex-direction:column; transition:box-shadow .15s ease, transform .15s ease; }}
        .ncard:hover {{ box-shadow:0 8px 22px rgba(26,54,93,0.14); transform:translateY(-2px); }}
        .ncard-top {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
        .nbadge {{ font-size:0.82rem; font-weight:700; padding:4px 12px; border-radius:12px; }}
        .ndate {{ color:#9aa4b2; font-size:0.9rem; }}
        .ntitle {{ font-size:1.25rem; font-weight:800; color:{PRIMARY}; line-height:1.4; margin-bottom:8px;
            display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
        .ndesc {{ font-size:1.02rem; color:#4b5563; line-height:1.6; flex:1;
            display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
        .ndiv {{ border-top:1px solid #eef0f3; margin:14px 0 12px; }}
        .ncard-bot {{ display:flex; justify-content:space-between; align-items:center; }}
        .nsource {{ color:{PRIMARY}; font-weight:700; font-size:0.95rem; }}
        .nlink {{ color:{ACCENT}; font-weight:700; font-size:0.95rem; text-decoration:none; }}
        .nlink:hover {{ text-decoration:underline; }}
        [class*="st-key-pg_"] button {{ border-radius:10px; font-weight:700; min-width:46px; }}
        [class*="st-key-pg_"] button[kind="primary"] {{ background:{PRIMARY}; color:#fff; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _hide_sidebar_css() -> None:
    """홈 화면에서는 사이드바를 완전히 숨긴다."""
    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] { display:none !important; }
        div[data-testid="stSidebarCollapsedControl"] { display:none !important; }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# 사이드바 (홈 제외한 페이지에서만)
# --------------------------------------------------------------------------- #
def render_sidebar() -> None:
    with st.sidebar:
        st.markdown(
            f"""
            <a class="brand" href="?nav=home" target="_self" title="홈으로">
                <img src="{FACE_URI}" alt="해치"/>
                <div>
                    <div class="brand-name">{BRAND_KO} <span>{BRAND_EN}</span></div>
                    <div class="brand-sub">{TAGLINE}</div>
                </div>
            </a>
            <a class="home-link" href="?nav=home" target="_self">← 홈으로</a>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="nav-cap">메뉴</div>', unsafe_allow_html=True)
        for key in NAV_ORDER:
            p = PAGES[key]
            active = st.session_state.menu == key
            if st.button(f"{p['icon']}  {p['label']}", key=f"nav_{key}",
                         use_container_width=True,
                         type="primary" if active else "secondary"):
                st.session_state.menu = key
                st.rerun()
        st.divider()
        st.caption("📞 이용문의 1588-4388 · 24시간")
        st.caption("⚠ 표시 데이터는 예시(Dummy)입니다.")


# --------------------------------------------------------------------------- #
# 홈 (사이드바 없음 · 브랜드 히어로 + 카드 4개)
# --------------------------------------------------------------------------- #
def render_home() -> None:
    hero = (
        '<div class="home-hero">'
        f'<img class="hero-illust" src="{SCENE_URI}" alt="해치타GO 캐릭터 일러스트"/>'
        f'<div class="hero-logo">🚕 {BRAND_KO}<span class="en">{BRAND_EN}</span></div>'
        f'<div class="hero-tag">{TAGLINE}</div>'
        '</div>'
        '<div class="home-h2">'
        '<h2>더 쉽고 편리한 이동의 시작</h2>'
        '<p>해치타GO는 교통약자의 안전하고 편리한 이동을 위해<br>'
        '해치와 소울 프렌즈가 함께합니다.</p>'
        '</div>'
    )
    st.markdown(hero, unsafe_allow_html=True)

    cards = "".join(
        f'<a class="tilecard" href="?nav={key}" target="_self">'
        f'<div class="tile-ico">{PAGES[key]["icon"]}</div>'
        f'<div class="tile-title">{PAGES[key]["label"]}</div>'
        f'<div class="tile-sub">{PAGES[key]["sub"].replace(chr(10), "<br>")}</div>'
        f'</a>'
        for key in TILE_ORDER
    )
    st.markdown(f'<div class="tilewrap">{cards}</div>', unsafe_allow_html=True)


# --------------------------------------------------------------------------- #
# 관련뉴스 (탭 + 2열 카드 그리드 + 검색 + 페이지네이션)
# --------------------------------------------------------------------------- #
def _news_card_html(item: dict) -> str:
    bg, fg = CATE_STYLE.get(item["cat"], ("#eef2f7", "#374151"))
    return f"""
    <div class="ncard">
        <div class="ncard-top">
            <span class="nbadge" style="background:{bg};color:{fg}">{item['cat']}</span>
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


def _news_grid(cat: str, kw: str) -> None:
    items = [
        n for n in NEWS_ITEMS
        if (cat == "전체" or n["cat"] == cat)
        and (not kw or kw in n["title"] or kw in n["desc"] or kw in n["source"])
    ]

    # 검색어가 바뀌면 해당 탭 1페이지로 리셋
    sig_key, page_key = f"nsig_{cat}", f"npage_{cat}"
    if st.session_state.get(sig_key) != kw:
        st.session_state[sig_key] = kw
        st.session_state[page_key] = 1

    total = len(items)
    pages = max(1, -(-total // PER_PAGE))
    page = min(st.session_state.get(page_key, 1), pages)
    st.session_state[page_key] = page

    st.markdown(f"**{total}건**의 뉴스" + (f"  ·  검색어: `{kw}`" if kw else ""))
    st.write("")
    if total == 0:
        st.warning("검색 결과가 없습니다. 다른 검색어나 탭을 선택해 보세요.")
        return

    start = (page - 1) * PER_PAGE
    grid = st.columns(2, gap="medium")
    for idx, item in enumerate(items[start:start + PER_PAGE]):
        with grid[idx % 2]:
            st.markdown(_news_card_html(item), unsafe_allow_html=True)
    _pagination(cat, page, pages)


def render_news() -> None:
    st.header("📰 관련뉴스")
    st.caption("장애인콜택시와 관련된 최신 소식과 정책 변화, 이용 안내 정보를 한눈에 확인하세요.")

    keyword = st.text_input("검색", placeholder="뉴스 제목이나 키워드를 검색하세요",
                            label_visibility="collapsed")
    kw = keyword.strip()

    tab_cats = ["전체", "복지사업", "지원사업", "택시소식"]
    tabs = st.tabs(["📄 전체", "🏛 복지사업", "💰 지원사업", "🚕 택시소식"])
    for tab, cat in zip(tabs, tab_cats):
        with tab:
            _news_grid(cat, kw)
    st.caption("※ 표시된 소식은 UI 예시(Dummy) 콘텐츠입니다.")


# --------------------------------------------------------------------------- #
# 미구현 파트 자리표시
# --------------------------------------------------------------------------- #
def render_placeholder(page: dict) -> None:
    st.header(f"{page['icon']} {page['label']}")
    st.info(
        f"**{page['label']}** 화면은 팀원 담당 파트입니다.\n\n"
        f"담당자가 모듈을 완성하면 `app/main_app.py` 라우팅에 연결됩니다."
    )
    st.caption("기획 내용: " + page.get("sub", "").replace("\n", " "))


# --------------------------------------------------------------------------- #
# 메인 라우팅
# --------------------------------------------------------------------------- #
def _handle_nav_query() -> None:
    """홈 카드/브랜드의 링크(?nav=...) 클릭을 처리한다."""
    qp = st.query_params
    if "nav" in qp:
        target = qp.get("nav")
        if target in PAGES:
            st.session_state.menu = target
        st.query_params.clear()
        st.rerun()


def main() -> None:
    if "menu" not in st.session_state:
        st.session_state.menu = "home"

    _handle_nav_query()
    inject_style()

    menu = st.session_state.menu
    if menu == "home":
        _hide_sidebar_css()
        render_home()
        return

    render_sidebar()
    if menu == "faq":
        render_faq()              # ← 본인 담당 파트
    elif menu == "news":
        render_news()             # ← 관련뉴스 (탭 + 2열 그리드)
    else:
        render_placeholder(PAGES[menu])


if __name__ == "__main__":
    main()
