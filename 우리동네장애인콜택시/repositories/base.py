"""repository 계층 공통 유틸리티.

Streamlit 페이지는 이 계층을 통해서만 DB를 조회한다(페이지에서 직접 SQL 작성 금지).
모든 쿼리는 SQLAlchemy text() + 파라미터 바인딩을 사용하고, DB 장애 시에도
앱이 죽지 않도록 빈 DataFrame/None을 반환한다.
"""
from __future__ import annotations

import logging

import pandas as pd
from sqlalchemy import text

from services.database import DatabaseUnavailableError, get_connection

logger = logging.getLogger(__name__)


def safe_read_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    """SELECT 쿼리를 안전하게 실행한다. 실패 시 빈 DataFrame을 반환한다."""
    try:
        with get_connection() as conn:
            return pd.read_sql(text(query), conn, params=params or {})
    except DatabaseUnavailableError:
        logger.warning("DB 조회 실패로 빈 결과를 반환합니다.")
        return pd.DataFrame()
    except Exception:
        logger.exception("예상치 못한 조회 오류")
        return pd.DataFrame()


def safe_execute(query: str, params: dict | None = None) -> bool:
    """INSERT/UPDATE 등 실행형 쿼리. 성공 여부를 bool로 반환한다."""
    try:
        with get_connection() as conn:
            conn.execute(text(query), params or {})
            conn.commit()
        return True
    except DatabaseUnavailableError:
        logger.warning("DB 실행 실패")
        return False
    except Exception:
        logger.exception("예상치 못한 실행 오류")
        return False
