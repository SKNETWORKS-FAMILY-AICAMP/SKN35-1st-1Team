"""
관련뉴스 데이터와 검색 로직
---------------------------
화면(views/news.py)은 이 모듈의 데이터와 search()만 사용한다.
현재는 예시(Dummy) 콘텐츠이며, 실제 수집으로 바꿀 때 이 파일만 교체하면 된다.
"""

from __future__ import annotations

PER_PAGE = 6

# 탭 구성 — (표시 라벨, 필터 값)
TABS: list[tuple[str, str]] = [
    ("전체", "전체"),
    ("복지사업", "복지사업"),
    ("지원사업", "지원사업"),
    ("택시소식", "택시소식"),
]

# 카테고리 → CSS 클래스 (색상은 style/news.css의 .nbadge.* 에서 관리)
CATEGORY_CLASS: dict[str, str] = {
    "복지사업": "welfare",
    "지원사업": "support",
    "택시소식": "taxi",
}

NEWS_ITEMS: list[dict[str, str]] = [
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


def search(category: str = "전체", keyword: str = "") -> list[dict[str, str]]:
    """카테고리와 검색어로 뉴스를 거른다. 검색어는 제목·본문·출처를 함께 찾는다."""
    return [
        item for item in NEWS_ITEMS
        if (category == "전체" or item["cat"] == category)
        and (not keyword
             or keyword in item["title"]
             or keyword in item["desc"]
             or keyword in item["source"])
    ]
