"""뉴스 수집(collectors/collect_news.py) 전처리 로직 테스트."""
from __future__ import annotations

from collectors.collect_news import make_title_hash, normalize_title, strip_html


# ---------------------------------------------------------------------
# 11) 뉴스 HTML 태그 제거 테스트
# ---------------------------------------------------------------------
def test_strip_html_removes_tags_and_unescapes_entities():
    raw = "서울시 <b>장애인콜택시</b> 이용자 &quot;대기시간 줄었다&quot; &amp; 만족도 상승"
    cleaned = strip_html(raw)
    assert "<b>" not in cleaned
    assert "</b>" not in cleaned
    assert "&quot;" not in cleaned
    assert '"대기시간 줄었다"' in cleaned
    assert "&" in cleaned  # &amp; -> & 로 변환


def test_strip_html_collapses_whitespace():
    raw = "서울시   장애인콜택시   \n\n 확대 운영"
    assert strip_html(raw) == "서울시 장애인콜택시 확대 운영"


# ---------------------------------------------------------------------
# 10) 뉴스 제목 중복 제거 테스트
# ---------------------------------------------------------------------
def test_normalize_title_ignores_spacing_and_punctuation():
    assert normalize_title("서울시, 장애인콜택시 확대!") == normalize_title("서울시 장애인콜택시 확대")


def test_title_hash_same_for_normalized_duplicates():
    title_a = "서울 장애인콜택시 이용자 늘었다"
    title_b = "서울   장애인콜택시  이용자 늘었다!!"
    assert make_title_hash(title_a) == make_title_hash(title_b)


def test_title_hash_differs_for_different_titles():
    assert make_title_hash("서울 장애인콜택시 확대") != make_title_hash("서울 교통약자 이동지원 확대")
