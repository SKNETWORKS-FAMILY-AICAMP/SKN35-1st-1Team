"""DB 접속 실패 시에도 앱이 죽지 않고 안전하게 degrade하는지 확인하는 테스트."""
from __future__ import annotations

import contextlib

from repositories import base as base_module
from repositories import taxi_repository
from services.database import DatabaseUnavailableError


@contextlib.contextmanager
def _fail_connection():
    raise DatabaseUnavailableError("데이터베이스에 연결할 수 없습니다(테스트용 모의 실패).")
    yield  # pragma: no cover - 실행되지 않음


# ---------------------------------------------------------------------
# 13) DB 접속 실패 처리 테스트
# ---------------------------------------------------------------------
def test_safe_read_sql_returns_empty_dataframe_when_db_down(monkeypatch):
    monkeypatch.setattr(base_module, "get_connection", _fail_connection)
    df = base_module.safe_read_sql("SELECT 1")
    assert df.empty


def test_safe_execute_returns_false_when_db_down(monkeypatch):
    monkeypatch.setattr(base_module, "get_connection", _fail_connection)
    assert base_module.safe_execute("SELECT 1") is False


def test_repository_function_degrades_gracefully_when_db_down(monkeypatch):
    monkeypatch.setattr(base_module, "get_connection", _fail_connection)
    result = taxi_repository.get_area_list()
    assert result.empty


def test_safe_read_sql_handles_unexpected_exception():
    def _boom(*args, **kwargs):
        raise RuntimeError("예상치 못한 오류")

    import repositories.base as b
    original = b.get_connection
    try:
        b.get_connection = _boom
        df = b.safe_read_sql("SELECT 1")
        assert df.empty
    finally:
        b.get_connection = original
