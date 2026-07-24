"""FAQ 테이블 조회/적재 전담 계층."""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text

from repositories.base import safe_read_sql
from services.database import DatabaseUnavailableError, get_connection

logger = logging.getLogger(__name__)


def get_faqs(category: str | None = None, keyword: str | None = None) -> pd.DataFrame:
    # CONCAT()은 MySQL 전용이라 이식성이 떨어져, 와일드카드 패턴을 파이썬에서 미리 만들어 바인딩한다.
    keyword_pattern = f"%{keyword}%" if keyword else None
    query = """
        SELECT faq_id, category, question, answer, source_url, source_name, collected_at, updated_at, display_order
        FROM faq
        WHERE is_active = 1
          AND (:category IS NULL OR category = :category)
          AND (:keyword_pattern IS NULL OR question LIKE :keyword_pattern OR answer LIKE :keyword_pattern)
        ORDER BY display_order, faq_id
    """
    return safe_read_sql(query, {"category": category, "keyword_pattern": keyword_pattern})


def get_categories() -> list[str]:
    df = safe_read_sql("SELECT DISTINCT category FROM faq WHERE is_active = 1 ORDER BY category")
    return df["category"].tolist() if not df.empty else []


def get_last_collected_at() -> str | None:
    df = safe_read_sql("SELECT MAX(collected_at) AS last_collected_at FROM faq")
    if df.empty or pd.isna(df.iloc[0]["last_collected_at"]):
        return None
    return str(df.iloc[0]["last_collected_at"])


def upsert_faqs(items: list[dict]) -> int:
    """category+question 기준 UPSERT. 트랜잭션으로 처리하며 실패 시 전체 롤백한다.

    items가 비어있으면 기존 FAQ 데이터를 그대로 유지하고 아무 작업도 하지 않는다
    (수집 실패/0건 시 기존 DB를 빈 값으로 덮어쓰지 않는다는 원칙).
    """
    if not items:
        logger.info("FAQ 수집 결과가 0건이라 기존 데이터를 유지합니다.")
        return 0

    try:
        with get_connection() as conn:
            with conn.begin():
                for item in items:
                    existing = conn.execute(
                        text("SELECT faq_id FROM faq WHERE category = :category AND question = :question"),
                        {"category": item["category"], "question": item["question"]},
                    ).fetchone()
                    if existing:
                        conn.execute(
                            text(
                                """
                                UPDATE faq SET answer = :answer, source_url = :source_url,
                                    source_name = :source_name, updated_at = :updated_at,
                                    display_order = :display_order, is_active = 1
                                WHERE faq_id = :faq_id
                                """
                            ),
                            {**item, "faq_id": existing[0]},
                        )
                    else:
                        conn.execute(
                            text(
                                """
                                INSERT INTO faq (category, question, answer, source_url, source_name,
                                    collected_at, updated_at, display_order, is_active)
                                VALUES (:category, :question, :answer, :source_url, :source_name,
                                    :collected_at, :updated_at, :display_order, 1)
                                """
                            ),
                            item,
                        )
            return len(items)
    except DatabaseUnavailableError:
        logger.warning("FAQ 저장 실패(DB 연결 불가) - 기존 데이터 유지")
        return 0
    except Exception:
        logger.exception("FAQ 저장 중 예상치 못한 오류 - 기존 데이터 유지")
        return 0
