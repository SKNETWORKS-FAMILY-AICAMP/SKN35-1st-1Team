"""관련뉴스 페이지 서비스 계층. 공개 데이터만 다루므로 st.cache_data를 사용한다."""
from __future__ import annotations

import streamlit as st

from config import NAVER
from repositories import news_repository as repo

CACHE_TTL_SECONDS = 1800


def naver_api_configured() -> bool:
    return NAVER.is_configured


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_news_list(search_keyword: str | None = None, limit: int = 30):
    return repo.get_news(search_keyword=search_keyword, limit=limit)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_keywords() -> list[str]:
    return repo.get_keywords()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_last_collected_at() -> str | None:
    return repo.get_last_collected_at()
