"""뉴스 테이블 조회/적재 전담 계층."""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text

from repositories.base import safe_read_sql
from services.database import DatabaseUnavailableError, get_connection

logger = logging.getLogger(__name__)


def get_news(search_keyword: str | None = None, limit: int = 30) -> pd.DataFrame:
    query = """
        SELECT news_id, title, description, publisher, published_at, original_url, naver_url,
               search_keyword, collected_at
        FROM news
        WHERE is_active = 1
          AND (:search_keyword IS NULL OR search_keyword = :search_keyword)
        ORDER BY published_at DESC
        LIMIT :limit_n
    """
    return safe_read_sql(query, {"search_keyword": search_keyword, "limit_n": limit})


def get_keywords() -> list[str]:
    df = safe_read_sql("SELECT DISTINCT search_keyword FROM news WHERE is_active = 1 ORDER BY search_keyword")
    return df["search_keyword"].tolist() if not df.empty else []


def get_last_collected_at() -> str | None:
    df = safe_read_sql("SELECT MAX(collected_at) AS last_collected_at FROM news")
    if df.empty or pd.isna(df.iloc[0]["last_collected_at"]):
        return None
    return str(df.iloc[0]["last_collected_at"])


def insert_news_dedup(items: list[dict]) -> int:
    """title_hash(정규화된 제목의 해시) 기준 중복을 제거하며 적재한다.

    이미 존재하는 기사는 collected_at만 갱신하고 새로 만들지 않는다.
    items가 비어있으면 기존 뉴스 데이터를 그대로 유지한다.
    """
    if not items:
        logger.info("뉴스 수집 결과가 0건이라 기존 데이터를 유지합니다.")
        return 0

    try:
        with get_connection() as conn:
            with conn.begin():
                for item in items:
                    conn.execute(
                        text(
                            """
                            INSERT INTO news (title, description, publisher, published_at, original_url,
                                naver_url, search_keyword, collected_at, title_hash, is_active)
                            VALUES (:title, :description, :publisher, :published_at, :original_url,
                                :naver_url, :search_keyword, :collected_at, :title_hash, 1)
                            ON DUPLICATE KEY UPDATE
                                collected_at = VALUES(collected_at),
                                is_active = 1
                            """
                        ),
                        item,
                    )
            return len(items)
    except DatabaseUnavailableError:
        logger.warning("뉴스 저장 실패(DB 연결 불가) - 기존 데이터 유지")
        return 0
    except Exception:
        logger.exception("뉴스 저장 중 예상치 못한 오류 - 기존 데이터 유지")
        return 0
