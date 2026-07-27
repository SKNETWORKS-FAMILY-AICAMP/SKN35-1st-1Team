"""텍스트 변환 유틸."""

from __future__ import annotations

import html


def to_html(text: object) -> str:
    """본문의 개행을 HTML 줄바꿈으로 바꾼다. 태그는 이스케이프한다."""
    return html.escape(str(text)).replace("\n", "<br>")
