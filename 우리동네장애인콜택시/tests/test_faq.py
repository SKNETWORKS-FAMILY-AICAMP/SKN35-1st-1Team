"""FAQ 수집/저장 실패 처리 테스트."""
from __future__ import annotations

import requests

from collectors.collect_faq import check_page_reachable
from repositories.faq_repository import upsert_faqs


# ---------------------------------------------------------------------
# 12) FAQ 수집 실패 처리 테스트
# ---------------------------------------------------------------------
def test_upsert_faqs_with_empty_list_keeps_existing_data_and_touches_no_db(monkeypatch):
    called = {"connected": False}

    def _spy_get_connection(*args, **kwargs):
        called["connected"] = True
        raise AssertionError("빈 목록일 때는 DB에 접속하면 안 된다")

    import repositories.faq_repository as faq_repo
    monkeypatch.setattr(faq_repo, "get_connection", _spy_get_connection)

    result = upsert_faqs([])
    assert result == 0
    assert called["connected"] is False


def test_check_page_reachable_returns_false_on_network_error(monkeypatch):
    def _raise(*args, **kwargs):
        raise requests.exceptions.ConnectionError("네트워크 오류(테스트용)")

    monkeypatch.setattr("collectors.collect_faq.requests.get", _raise)
    assert check_page_reachable("https://example.com/not-reachable") is False
