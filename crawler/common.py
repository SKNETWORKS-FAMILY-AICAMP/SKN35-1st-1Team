"""
크롤러 공통 유틸
----------------
세션 생성, 재시도, 인코딩 처리, 텍스트 정규화, 원본 저장을 담당한다.
BeautifulSoup 크롤러와 Selenium 크롤러가 공유한다.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

sys.path.append(str(Path(__file__).resolve().parent.parent))
import config  # noqa: E402


def build_session() -> requests.Session:
    """User-Agent가 설정된 requests 세션을 만든다."""
    s = requests.Session()
    s.headers.update({
        "User-Agent": config.USER_AGENT,
        "Accept-Language": "ko-KR,ko;q=0.9",
    })
    return s


def fetch_soup(session: requests.Session, url: str,
               params: dict | None = None) -> BeautifulSoup:
    """URL을 요청해 BeautifulSoup 객체로 반환한다. 실패 시 MAX_RETRY까지 재시도."""
    last_error: Exception | None = None
    for attempt in range(1, config.MAX_RETRY + 1):
        try:
            res = session.get(url, params=params, timeout=config.REQUEST_TIMEOUT)
            res.raise_for_status()
            # 대상 사이트는 EUC-KR/UTF-8이 혼재하므로 실제 인코딩을 추정해 적용
            res.encoding = res.apparent_encoding or res.encoding
            time.sleep(config.REQUEST_DELAY_SEC)   # 서버 부하 방지
            return BeautifulSoup(res.text, "lxml")
        except Exception as exc:                    # noqa: BLE001
            last_error = exc
            wait = attempt * 2
            print(f"  [재시도 {attempt}/{config.MAX_RETRY}] {url} — {exc} ({wait}s 대기)")
            time.sleep(wait)
    raise RuntimeError(f"요청 실패: {url} — {last_error}")


def clean_text(raw: str | None) -> str:
    """
    수집 원문을 정규화한다.

    1) HTML 엔티티 복원 (&nbsp; &amp; 등)
    2) 유니코드 공백(\xa0)·탭·개행 정리
    3) 3줄 이상 연속 개행 → 2줄로 축소
    4) 줄 끝 공백 제거 및 양끝 트림
    """
    if not raw:
        return ""
    text = html.unescape(raw)
    text = text.replace("\xa0", " ").replace("​", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    return text.strip()


def strip_q_prefix(question: str) -> str:
    """질문 앞의 'Q.', 'Q)', '[Q]' 같은 접두 기호를 제거한다."""
    return re.sub(r"^\s*\[?Q\]?\s*[.)\]:]?\s*", "", question or "").strip()


def save_raw(records: list[dict], path: Path, meta: dict | None = None) -> None:
    """수집 원본을 JSON으로 저장한다 (산출물 ② '수집 데이터'의 원본 단계)."""
    payload = {
        "collected_at": datetime.now().isoformat(timespec="seconds"),
        "record_count": len(records),
        "meta": meta or {},
        "records": records,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"  → 원본 저장: {path.relative_to(config.BASE_DIR)} ({len(records)}건)")


def load_raw(path: Path) -> list[dict]:
    """save_raw로 저장한 JSON에서 레코드 목록만 읽어온다."""
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload.get("records", [])
