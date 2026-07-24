"""MySQL 연결 관리.

- Streamlit 페이지에서는 get_connection() (캐시된 엔진 기반)을 사용한다.
- scripts/*.py (create_tables, load_aggregates 등)는 Streamlit 런타임 밖에서
  실행되므로 create_db_engine()을 직접 사용한다.
"""
from __future__ import annotations

import logging
from contextlib import contextmanager

import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.exc import SQLAlchemyError

from config import DB

logger = logging.getLogger(__name__)


class DatabaseUnavailableError(Exception):
    """MySQL 서버가 꺼져 있거나 접속 정보가 잘못된 경우 발생한다.

    화면에는 기술적 traceback을 노출하지 않고 안내 문구만 표시한다.
    """


def create_db_engine() -> Engine:
    return create_engine(DB.sqlalchemy_url(), pool_pre_ping=True, pool_recycle=1800)


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    return create_db_engine()


@contextmanager
def get_connection():
    """DB 연결을 열고, 실패 시 DatabaseUnavailableError로 통일해서 던진다."""
    try:
        engine = get_engine()
        conn: Connection = engine.connect()
    except SQLAlchemyError as e:
        logger.error("DB 연결 실패(%s): %s", type(e).__name__, e)
        raise DatabaseUnavailableError("데이터베이스에 연결할 수 없습니다.") from e

    try:
        yield conn
    except SQLAlchemyError as e:
        logger.error("DB 쿼리 오류(%s): %s", type(e).__name__, e)
        raise DatabaseUnavailableError("데이터베이스 조회 중 오류가 발생했습니다.") from e
    finally:
        conn.close()


def check_connection() -> bool:
    """DB 접속 가능 여부만 확인한다. 실패해도 예외를 던지지 않는다."""
    try:
        with get_connection() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except DatabaseUnavailableError:
        return False
