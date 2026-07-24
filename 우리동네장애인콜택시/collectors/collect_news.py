"""네이버 뉴스 검색 API를 이용한 장애인콜택시 관련뉴스 수집 스크립트.

API 키가 없거나 호출이 실패해도 예외를 던지지 않고 조용히 종료한다(0건이면
기존 DB 데이터를 유지). Streamlit 실행 중에는 이 스크립트를 호출하지 않는다.

사용 예:
    uv run python collectors/collect_news.py
"""
from __future__ import annotations

import hashlib
import html
import logging
import re
import sys
from datetime import datetime
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests

from config import NAVER
from repositories.news_repository import insert_news_dedup

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
REQUEST_TIMEOUT = 10
DISPLAY_PER_QUERY = 20

SEARCH_KEYWORDS = [
    "서울 장애인콜택시",
    "서울시 장애인콜택시",
    "서울 교통약자 이동지원",
    "서울시설공단 장애인콜택시",
    "장애인 이동권 서울",
    "교통약자 이동지원센터 서울",
]

# 서울 관련 기사 우선 필터링에 사용하는 힌트 단어
SEOUL_HINT_WORDS = ["서울", "시설공단", "교통약자"]


def strip_html(text: str) -> str:
    """HTML 태그 제거 + HTML entity 변환 + 공백 정리."""
    text = re.sub(r"<[^>]+>", "", text or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_title(title: str) -> str:
    """제목 정규화(공백/기호 제거, 소문자화) - 중복 제거 기준."""
    normalized = re.sub(r"[^0-9가-힣a-zA-Z]", "", title or "")
    return normalized.lower()


def make_title_hash(title: str) -> str:
    return hashlib.sha256(normalize_title(title).encode("utf-8")).hexdigest()


def guess_publisher(original_link: str | None) -> str | None:
    """네이버 뉴스 검색 API는 언론사명을 별도로 제공하지 않아 원문 URL의 도메인으로 대신한다."""
    if not original_link:
        return None
    try:
        netloc = urlparse(original_link).netloc
        return netloc.replace("www.", "") or None
    except ValueError:
        return None


def parse_pub_date(pub_date: str) -> datetime | None:
    try:
        return parsedate_to_datetime(pub_date)
    except (TypeError, ValueError):
        return None


def fetch_news_for_keyword(keyword: str) -> list[dict]:
    headers = {"X-Naver-Client-Id": NAVER.client_id, "X-Naver-Client-Secret": NAVER.client_secret}
    params = {"query": keyword, "display": DISPLAY_PER_QUERY, "start": 1, "sort": "date"}
    try:
        resp = requests.get(NAVER_NEWS_API_URL, headers=headers, params=params, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.warning("네이버 뉴스 API 호출 실패(%s): %s", keyword, type(e).__name__)
        return []

    try:
        payload = resp.json()
    except ValueError:
        logger.warning("네이버 뉴스 API 응답 파싱 실패(%s)", keyword)
        return []

    items = []
    for raw in payload.get("items", []):
        title = strip_html(raw.get("title", ""))
        if not title:
            continue
        description = strip_html(raw.get("description", ""))
        original_link = raw.get("originallink") or raw.get("link")
        items.append({
            "title": title,
            "description": description,
            "publisher": guess_publisher(original_link),
            "published_at": parse_pub_date(raw.get("pubDate", "")),
            "original_url": original_link,
            "naver_url": raw.get("link"),
            "search_keyword": keyword,
            "collected_at": datetime.now(),
            "title_hash": make_title_hash(title),
        })
    return items


def collect_all() -> list[dict]:
    """키워드별 수집 -> 동일 URL 중복 제거 -> 제목 정규화 중복 제거 ->
    서울 관련 기사 우선 필터링 -> 최신순 정렬."""
    by_url: dict[str, dict] = {}
    for keyword in SEARCH_KEYWORDS:
        for item in fetch_news_for_keyword(keyword):
            key = item["original_url"] or item["title_hash"]
            if key not in by_url:
                by_url[key] = item

    by_title: dict[str, dict] = {}
    for item in by_url.values():
        by_title.setdefault(item["title_hash"], item)

    seoul_related = [
        item for item in by_title.values()
        if any(word in item["title"] or word in item["description"] for word in SEOUL_HINT_WORDS)
    ]
    seoul_related.sort(key=lambda x: x["published_at"] or datetime.min, reverse=True)
    return seoul_related


def main() -> None:
    if not NAVER.is_configured:
        logger.warning("NAVER_CLIENT_ID/NAVER_CLIENT_SECRET이 설정되지 않아 뉴스 수집을 건너뜁니다. .env를 확인하세요.")
        return

    logger.info("뉴스 수집 시작")
    items = collect_all()
    if not items:
        logger.warning("수집된 뉴스가 0건입니다. 기존 DB 데이터를 유지합니다.")
        return
    count = insert_news_dedup(items)
    logger.info("뉴스 %d건 저장(갱신) 완료", count)


if __name__ == "__main__":
    main()
