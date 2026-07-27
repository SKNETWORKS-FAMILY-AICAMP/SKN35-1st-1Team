"""
홈 화면
-------
브랜드 히어로 + 바로가기 카드 4개. 이 화면에서만 사이드바를 숨긴다
(숨김 규칙은 style/home.css에 있다).
"""

from __future__ import annotations

import streamlit as st

from common import styles
from common.assets import SCENE_URI
from common.brand import BRAND_EN, BRAND_KO, PAGES, TAGLINE, TILE_ORDER


def _tile_html(key: str) -> str:
    """홈 바로가기 카드 한 장. 클릭하면 ?nav=<key>로 이동한다."""
    page = PAGES[key]
    sub = page["sub"].replace("\n", "<br>")
    return (
        f'<a class="tilecard" href="?nav={key}" target="_self">'
        f'<div class="tile-ico">{page["icon"]}</div>'
        f'<div class="tile-title">{page["label"]}</div>'
        f'<div class="tile-sub">{sub}</div>'
        f'</a>'
    )


def render() -> None:
    """홈 화면을 그린다."""
    styles.load("home.css")

    st.markdown(
        '<div class="home-hero">'
        f'<img class="hero-illust" src="{SCENE_URI}" alt="해치타GO 캐릭터 일러스트"/>'
        f'<div class="hero-logo">🚕 {BRAND_KO}<span class="en">{BRAND_EN}</span></div>'
        f'<div class="hero-tag">{TAGLINE}</div>'
        '</div>'
        '<div class="home-h2">'
        '<h2>더 쉽고 편리한 이동의 시작</h2>'
        '<p>해치타GO는 교통약자의 안전하고 편리한 이동을 위해<br>'
        '해치와 소울 프렌즈가 함께합니다.</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    cards = "".join(_tile_html(key) for key in TILE_ORDER)
    st.markdown(f'<div class="tilewrap">{cards}</div>', unsafe_allow_html=True)
