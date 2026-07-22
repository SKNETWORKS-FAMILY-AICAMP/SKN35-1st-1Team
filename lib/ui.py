# -*- coding: utf-8 -*-
"""
ui.py — 공용 UI/스타일 (홈페이지·앱 느낌으로 통일)
------------------------------------------------------
각 페이지 최상단에서:
    from lib import ui
    ui.setup("페이지 제목", "📊")
    ui.brandbar()
홈에서는 ui.hero(...) 사용.
"""
import streamlit as st

BRAND = "#1863c4"

_CSS = """
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');

:root { --brand:#1863c4; --brand-d:#124a94; --ink:#1a1f29; --line:#e6ebf3; --muted:#5a6270; }

html, body, [class*="css"], .stMarkdown, button, input, textarea, select,
[data-testid="stMetricValue"], [data-baseweb="tab"] {
  font-family: 'Pretendard', -apple-system, 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important;
}

/* 기본 크롬 정리 */
[data-testid="stToolbar"], [data-testid="stDecoration"], footer { display:none !important; }
.block-container { padding-top: 1.1rem !important; max-width: 1180px; }

/* 상단 브랜드바 */
.brandbar{
  position:sticky; top:0; z-index:99; margin-bottom:18px;
  padding:13px 22px; border-radius:14px; color:#fff;
  background:linear-gradient(90deg,var(--brand),var(--brand-d));
  display:flex; align-items:center; gap:11px;
  box-shadow:0 6px 18px rgba(24,99,196,.22);
}
.brandbar .logo{ font-size:22px; }
.brandbar .t{ font-weight:800; font-size:18px; letter-spacing:-.01em; }
.brandbar .s{ margin-left:auto; opacity:.9; font-size:12.5px; }
@media (max-width:640px){ .brandbar .s{ display:none; } }

/* 히어로 (홈) */
.hero{
  background:linear-gradient(135deg,#1863c4,#0e3f82); color:#fff;
  padding:34px 30px; border-radius:20px; margin-bottom:22px;
  box-shadow:0 12px 32px rgba(14,63,130,.28);
}
.hero h1{ margin:0 0 8px; font-size:30px; font-weight:800; letter-spacing:-.02em; }
.hero p{ margin:0; opacity:.93; font-size:15px; line-height:1.6; }

/* 버튼/링크 라운드 */
.stButton>button, .stDownloadButton>button, .stLinkButton>a, [data-testid="stBaseButton-secondary"]{
  border-radius:10px !important; font-weight:600 !important;
}
.stButton>button:hover{ border-color:var(--brand) !important; color:var(--brand) !important; }

/* 카드형 컨테이너(테두리 컨테이너 hover) */
[data-testid="stVerticalBlockBorderWrapper"]{ border-radius:16px !important; }
[data-testid="stVerticalBlockBorderWrapper"]:hover{
  box-shadow:0 8px 22px rgba(24,99,196,.12);
}

/* metric 카드화 */
[data-testid="stMetric"]{
  background:#f5f8fd; border:1px solid var(--line); border-radius:14px; padding:14px 16px;
}

/* 탭 */
[data-baseweb="tab-list"]{ gap:6px; }
[data-baseweb="tab"]{ border-radius:10px 10px 0 0; font-weight:600; }

/* 데이터프레임 라운드 */
[data-testid="stDataFrame"]{ border-radius:12px; overflow:hidden; }

/* 사이드바 상단 타이틀 */
[data-testid="stSidebarNav"]::before{
  content:"🚗 장애인 자동차 지원"; display:block;
  padding:14px 16px 6px; font-weight:800; color:var(--brand); font-size:15px;
}
</style>
"""


def setup(page_title: str, icon: str = "🚗", layout: str = "wide") -> None:
    st.set_page_config(page_title=page_title, page_icon=icon, layout=layout)
    st.markdown(_CSS, unsafe_allow_html=True)


def brandbar(subtitle: str = "지원금 비교 · 개조·검사 · 구매 · 편의시설") -> None:
    st.markdown(
        f'<div class="brandbar"><span class="logo">🚗</span>'
        f'<span class="t">장애인 자동차 지원</span>'
        f'<span class="s">{subtitle}</span></div>',
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',
        unsafe_allow_html=True,
    )
