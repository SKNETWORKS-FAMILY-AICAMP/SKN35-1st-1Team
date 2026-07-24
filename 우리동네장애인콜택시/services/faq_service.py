"""FAQ 페이지 서비스 계층. 공개 데이터만 다루므로 st.cache_data를 사용한다."""
from __future__ import annotations

import streamlit as st

from repositories import faq_repository as repo

CACHE_TTL_SECONDS = 1800


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_faq_list(category: str | None = None, keyword: str | None = None):
    return repo.get_faqs(category=category, keyword=keyword)


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_categories() -> list[str]:
    return repo.get_categories()


@st.cache_data(ttl=CACHE_TTL_SECONDS, show_spinner=False)
def get_last_collected_at() -> str | None:
    return repo.get_last_collected_at()
