"""
CSS 로더
--------
style/ 아래 CSS 파일을 읽어 페이지에 주입한다.

  · 공통 스타일  → main.py에서 style.css 를 한 번 로드
  · 페이지 스타일 → 각 view가 자기 CSS만 로드 (home.css / faq.css / news.css)

파일 내용은 프로세스당 한 번만 읽는다(@lru_cache).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import streamlit as st

STYLE_DIR = Path(__file__).resolve().parent.parent / "style"


@lru_cache(maxsize=None)
def _read(filename: str) -> str:
    return (STYLE_DIR / filename).read_text(encoding="utf-8")


def load(*filenames: str) -> None:
    """style/ 안의 CSS 파일을 읽어 <style>로 주입한다."""
    css = "\n".join(_read(name) for name in filenames)
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
