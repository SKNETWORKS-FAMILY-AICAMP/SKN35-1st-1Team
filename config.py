"""
프로젝트 공통 설정
------------------
경로·DB접속·크롤링 대상 URL을 한 곳에서 관리한다.
팀 병합 시 다른 파트도 이 모듈의 DB 설정을 그대로 재사용한다.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# --------------------------------------------------------------------------- #
# 경로 (모두 프로젝트 루트 기준 상대경로로 파생 — 절대경로 하드코딩 금지)
# --------------------------------------------------------------------------- #
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
DB_DIR = BASE_DIR / "db"
DOCS_DIR = BASE_DIR / "docs"

for _d in (RAW_DIR, PROCESSED_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# 파이프라인 단계별 산출 파일
RAW_BOARD_JSON = RAW_DIR / "faq_board_raw.json"          # ① 게시판 (BeautifulSoup)
RAW_GUIDE_JSON = RAW_DIR / "faq_guide_raw.json"          # ② 안내페이지 (BeautifulSoup)
RAW_SELENIUM_JSON = RAW_DIR / "faq_board_selenium.json"  # ③ 게시판 (Selenium)

PROCESSED_FAQ_CSV = PROCESSED_DIR / "faq_clean.csv"
PROCESSED_KEYWORD_CSV = PROCESSED_DIR / "faq_keyword_clean.csv"
PROCESSED_SOURCE_CSV = PROCESSED_DIR / "faq_source_clean.csv"
QUALITY_REPORT_JSON = PROCESSED_DIR / "quality_report.json"

# --------------------------------------------------------------------------- #
# 크롤링 대상 (서울시설공단 장애인콜택시 공식 홈페이지)
# --------------------------------------------------------------------------- #
SISUL_BASE = "https://www.sisul.or.kr"

# 게시판형 FAQ — 목록 → 상세 2단계 수집
BOARD_LIST_URL = f"{SISUL_BASE}/open_content/calltaxi/bbs/bbsMsgList.do"
BOARD_DETAIL_URL = f"{SISUL_BASE}/open_content/calltaxi/bbs/bbsMsgDetail.do"
BOARD_PAGE_URL = f"{SISUL_BASE}/open_content/calltaxi/community/faq.jsp"
BOARD_PARAMS = {"bcd": "faq", "cate1": "calltaxi"}

# FAQ 카테고리 표준 분류 (faq_category 테이블의 기준값 — 이 목록 외 값은 허용하지 않음)
FAQ_CATEGORIES: list[str] = [
    "가입·등록",
    "이용대상·자격",
    "이용방법·접수",
    "요금·결제",
    "배차·대기",
    "운행지역·시간",
    "준수사항·기타",
]
DEFAULT_CATEGORY = "준수사항·기타"

# 안내 페이지형 — 기획서 지정 대상(가입안내 / 이용기준 / 이용방법 3종)
# group 값은 반드시 FAQ_CATEGORIES 안의 값이어야 한다.
GUIDE_PAGES: list[dict[str, str]] = [
    {"code": "join", "title": "가입안내", "group": "가입·등록",
     "path": "/open_content/calltaxi/introduce/join.jsp"},
    {"code": "receipt", "title": "이용기준", "group": "이용대상·자격",
     "path": "/open_content/calltaxi/introduce/receipt.jsp"},
    {"code": "guide_internet", "title": "이용방법 - 인터넷접수", "group": "이용방법·접수",
     "path": "/open_content/calltaxi/introduce/guide.jsp"},
    {"code": "guide_sms", "title": "이용방법 - 문자접수", "group": "이용방법·접수",
     "path": "/open_content/calltaxi/introduce/guide4.jsp"},
    {"code": "guide_app", "title": "이용방법 - 앱접수", "group": "이용방법·접수",
     "path": "/open_content/calltaxi/introduce/guide5.jsp"},
    # 보조 대상 — FAQ 성격이 강해 데이터 보강용으로 함께 수집
    {"code": "allday", "title": "전일접수제 이용안내", "group": "이용방법·접수",
     "path": "/open_content/calltaxi/introduce/allday.jsp"},
    {"code": "obey", "title": "이용자 준수사항", "group": "준수사항·기타",
     "path": "/open_content/calltaxi/introduce/obey.jsp"},
]

# 설정 오타로 표준 분류를 벗어나는 값이 들어가면 즉시 알아채도록 검증한다
_invalid = [p["group"] for p in GUIDE_PAGES if p["group"] not in FAQ_CATEGORIES]
if _invalid:
    raise ValueError(f"GUIDE_PAGES의 group이 FAQ_CATEGORIES에 없습니다: {_invalid}")

# 크롤링 매너 설정
REQUEST_TIMEOUT = 20
REQUEST_DELAY_SEC = 0.7   # 요청 간 지연 (서버 부하 방지)
MAX_RETRY = 3
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/150.0.0.0 Safari/537.36"
)

# --------------------------------------------------------------------------- #
# MySQL 접속 정보 (.env 에서 로드)
# --------------------------------------------------------------------------- #
load_dotenv(BASE_DIR / ".env")


def get_db_config() -> dict:
    """PyMySQL connect()에 그대로 넘길 수 있는 접속 설정을 반환한다."""
    return {
        "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
        "database": os.getenv("MYSQL_DATABASE", "seoul_calltaxi"),
        "charset": os.getenv("MYSQL_CHARSET", "utf8mb4"),
    }


DB_NAME = os.getenv("MYSQL_DATABASE", "seoul_calltaxi")
