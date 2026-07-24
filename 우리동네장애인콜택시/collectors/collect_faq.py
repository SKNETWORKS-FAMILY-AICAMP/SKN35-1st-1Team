"""서울시설공단 장애인콜택시 공식 홈페이지 FAQ 수집 스크립트.

Streamlit 실행 중에는 크롤링하지 않는다(요구사항). 이 스크립트를 별도로 주기
실행해 DB의 faq 테이블을 갱신하고, Streamlit 페이지는 DB만 조회한다.

동작 방식:
  1) 공식 홈페이지의 관련 페이지가 아직 살아있는지(reachable) 확인한다.
  2) 실제 표시할 답변은, 여러 주제가 한 페이지에 섞여 있어 범용 스크래핑으로
     항목별 답변을 안정적으로 추출하기 어렵기 때문에, 같은 공식 페이지를
     사람이 직접 확인하고 정리한 요약문(FALLBACK_ANSWERS)을 사용한다.
     페이지 접속 성공 여부는 source_name에 반영해 투명하게 표시한다.
  3) 수집 결과가 0건이면 기존 DB 데이터를 그대로 유지한다(덮어쓰지 않음).

사용 예:
    uv run python collectors/collect_faq.py
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from config import FAQ_SOURCE
from repositories.faq_repository import upsert_faqs

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 10
USER_AGENT = "Mozilla/5.0 (compatible; WooriDongneCallTaxiBot/1.0; informational use)"

BASE_URL = "https://www.sisul.or.kr/open_content/calltaxi/introduce/"

# (category, question, source_url)
FAQ_SOURCES = [
    ("가입안내", "장애인콜택시는 어떻게 가입하나요?", BASE_URL + "join.jsp"),
    ("이용대상", "누가 이용할 수 있나요?", BASE_URL + "receipt.jsp"),
    ("이용기준", "이용 신청 기준은 어떻게 되나요?", BASE_URL + "receipt.jsp"),
    ("이용요금", "이용 요금은 얼마인가요?", BASE_URL + "receipt.jsp"),
    ("운행지역", "어느 지역까지 운행하나요?", BASE_URL + "receipt.jsp"),
    ("이용방법", "이용(접수) 방법에는 어떤 것이 있나요?", BASE_URL + "guide.jsp"),
    ("전화접수", "전화로 어떻게 접수하나요?", BASE_URL + "guide.jsp"),
    ("문자접수", "문자로 어떻게 접수하나요?", BASE_URL + "guide4.jsp"),
    ("인터넷접수", "인터넷으로 어떻게 접수하나요?", BASE_URL + "guide.jsp"),
    ("앱접수", "모바일 앱으로 어떻게 접수하나요?", BASE_URL + "join.jsp"),
    ("동승자기준", "동승자는 몇 명까지 가능한가요?", BASE_URL + "receipt.jsp"),
    ("휠체어이용", "휠체어를 이용해도 되나요?", BASE_URL + "receipt.jsp"),
    ("취소및변경", "예약을 취소하거나 변경하려면 어떻게 하나요?", BASE_URL + "obey.jsp"),
    ("문의처", "문의는 어디로 하면 되나요?", BASE_URL + "join.jsp"),
]

# 공식 홈페이지 내용을 사람이 직접 확인하고 정리한 요약 안내문(2026-07 기준).
# 이용 기준/요금 등은 변경될 수 있으므로 실제 이용 전 공식 홈페이지 재확인이 필요하다.
FALLBACK_ANSWERS = {
    "가입안내": "콜센터(전화) 또는 장애인콜택시 앱으로 가입 신청을 할 수 있습니다. 중증보행장애인임을 확인할 수 있는 복지카드 또는 장애정도결정서 등 증명서류를 팩스나 문자, 앱 업로드로 제출해야 하며, 가입 등록 후 2주 안에 서류를 제출하지 않으면 가입이 취소될 수 있습니다. 3년간 탑승 기록이 없으면 개인정보가 자동 삭제되어 재이용 시 다시 등록해야 합니다.",
    "이용대상": "중증보행장애인(중증장애와 보행상 장애가 있는 경우), 1~2급 국가유공자(상이등급), 휠체어를 이용하는 외국인 등이 주요 이용대상입니다. 시각장애인·신장장애인은 원칙적으로 '복지콜' 등 다른 이동지원 서비스 이용이 권장됩니다.",
    "이용기준": "신규 이용자는 먼저 전화로 회원 정보를 등록해야 하며, 이후 전화·문자·인터넷·모바일 앱으로 이용을 신청할 수 있습니다.",
    "이용요금": "5km까지 기본요금 1,500원이며, 5~10km 구간은 km당 280원, 10km 초과 구간은 km당 70원이 추가됩니다. 시간대·지역에 따른 할증 요금은 없습니다.",
    "운행지역": "서울시 전역과 경기도 31개 시·군, 인천광역시까지 확대 운영되고 있습니다(2023년 12월 기준 확대).",
    "이용방법": "전화 접수, 문자 접수, 인터넷 접수, 모바일 앱 접수 등 다양한 방법으로 이용을 신청할 수 있습니다.",
    "전화접수": "콜센터 대표번호로 전화하여 출발지·목적지·희망 시간 등을 알려주면 접수할 수 있습니다.",
    "문자접수": "등록된 연락처로 문자를 보내 출발지, 목적지, 희망 탑승시간 등을 전달하는 방식으로 접수할 수 있습니다.",
    "인터넷접수": "공식 홈페이지에서 로그인 후 출발지/목적지를 검색하고 휠체어 이용 여부 등을 선택해 접수할 수 있습니다.",
    "앱접수": "장애인콜택시 모바일 앱을 설치해 회원가입 후 접수할 수 있으며, 가입 서류도 앱을 통해 업로드할 수 있습니다.",
    "동승자기준": "차량 좌석 수 범위 내에서 가족, 보호자 등이 동승할 수 있습니다. 휠체어 미이용 시 고객 외 최대 2명, 휠체어 이용 시 최대 3명까지 동승 가능합니다.",
    "휠체어이용": "휠체어를 이용하는 경우 접수 시 휠체어 이용 여부를 체크하면 휠체어 탑승이 가능한 차량이 배차됩니다.",
    "취소및변경": "탑승이 어려운 경우 다른 이용자를 위해 콜센터로 미리 취소를 요청해야 합니다. 배차 이후 잦은 취소는 일정 시간 동안 재접수가 제한될 수 있습니다.",
    "문의처": "이용 중 궁금한 점은 서울시설공단 장애인콜택시 콜센터로 문의하면 안내받을 수 있습니다.",
}


def check_page_reachable(url: str) -> bool:
    """페이지가 아직 살아있는지만 확인한다(HTML 파싱/스크래핑은 하지 않음)."""
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": USER_AGENT})
        return resp.status_code < 400
    except requests.RequestException as e:
        logger.warning("페이지 접속 확인 실패(%s): %s", url, type(e).__name__)
        return False


def build_faq_items() -> list[dict]:
    now = datetime.now()
    items = []
    for order, (category, question, url) in enumerate(FAQ_SOURCES, start=1):
        answer = FALLBACK_ANSWERS.get(category)
        if not answer:
            continue
        reachable = check_page_reachable(url)
        source_name = FAQ_SOURCE.source_name if reachable else f"{FAQ_SOURCE.source_name} (접속 확인 실패, 이전 수집 내용 사용)"
        items.append({
            "category": category,
            "question": question,
            "answer": answer,
            "source_url": url,
            "source_name": source_name,
            "collected_at": now,
            "updated_at": now,
            "display_order": order,
        })
    return items


def main() -> None:
    logger.info("FAQ 수집 시작: %s", FAQ_SOURCE.source_url)
    items = build_faq_items()
    if not items:
        logger.warning("수집된 FAQ가 0건입니다. 기존 DB 데이터를 유지합니다.")
        return
    count = upsert_faqs(items)
    logger.info("FAQ %d건 저장(갱신) 완료", count)


if __name__ == "__main__":
    main()
