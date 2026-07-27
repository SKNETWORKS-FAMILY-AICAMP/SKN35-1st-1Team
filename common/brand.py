"""
브랜드 상수와 페이지 정의
-------------------------
색상은 style/style.css의 CSS 변수(--primary 등)에서 관리한다.
파이썬과 CSS 양쪽에 색을 중복 정의하지 않는다.
"""

from __future__ import annotations

BRAND_KO = "해치타GO"
BRAND_EN = "Haechi Ta-GO"
TAGLINE = "해치와 소울 프렌즈가 함께 타고 달리는 따뜻한 이동 서비스"

# 페이지 정의 — key가 곧 라우팅 값(?nav=<key>)이자 session_state.menu 값이다.
PAGES: dict[str, dict[str, str]] = {
    "home":    {"icon": "🏠", "label": "홈"},
   "usage":   {"icon": "query_stats", "icon_bg": "#ffd93f", "icon_color": "#e9bd2a",
                "label": "이용현황",
                "sub": "자치구별 대기시간 및\n실시간 차량 현황 확인", "owner": "팀원"},
    "reserve": {"icon": "event_available", "icon_bg": "#7fd6b5", "icon_color": "#4bb691",
                "label": "예약하기",
                "sub": "예약 정보 정리 도우미 및\n간편 예약 시스템 신청", "owner": "팀원"},
    "faq":     {"icon": "help_center", "icon_bg": "#7db8ff", "icon_color": "#5691e0",
                "label": "FAQ",
                "sub": "자주 묻는 질문과\n이용 방법 상세 안내", "owner": "본인"},
    "news":    {"icon": "newspaper", "icon_bg": "#ff8a80", "icon_color": "#e56b61",
                "label": "관련뉴스",
                "sub": "공지사항 및 장애인\n복지 관련 최신 소식", "owner": "팀원"},
 }

NAV_ORDER = ["usage", "reserve", "faq", "news"]   # 사이드바 순서 ('홈' 제외)
TILE_ORDER = ["usage", "reserve", "faq", "news"]  # 홈 바로가기 카드 순서
