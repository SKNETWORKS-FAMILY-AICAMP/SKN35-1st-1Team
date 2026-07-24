"""예약하기 페이지의 개인정보(연락처/상세주소) 비저장 원칙 정적 검증.

연락처, 출발/목적 상세 위치는 DB/CSV/파일/로그/캐시 어디에도 저장되지 않아야 한다.
페이지 코드 자체에 캐시 데코레이터나 로깅 호출이 없는지 정적으로 검사한다.
"""
from __future__ import annotations

from pathlib import Path

RESERVATION_PAGE = Path("pages/2_예약하기.py")


def _read_source() -> str:
    assert RESERVATION_PAGE.exists(), "예약하기 페이지 파일을 찾을 수 없습니다."
    return RESERVATION_PAGE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------
# 14) 개인정보 비저장 확인 테스트
# ---------------------------------------------------------------------
def test_reservation_page_never_caches_anything():
    source = _read_source()
    assert "st.cache_data" not in source
    assert "st.cache_resource" not in source


def test_reservation_page_never_logs_anything():
    source = _read_source()
    assert "logger." not in source
    assert "logging." not in source
    assert "print(" not in source


def test_reservation_page_does_not_write_files_or_db():
    source = _read_source()
    forbidden_snippets = ["to_csv(", "to_parquet(", "open(", "INSERT INTO", "safe_execute("]
    for snippet in forbidden_snippets:
        assert snippet not in source, f"예약하기 페이지에 금지된 저장 동작이 있습니다: {snippet}"
