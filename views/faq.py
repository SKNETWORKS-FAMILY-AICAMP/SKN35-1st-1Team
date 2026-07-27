"""
FAQ 화면 — 담당: 본인
---------------------
서울시설공단 장애인콜택시 공식 안내를 질문·답변으로 정리해 보여준다.

설계 원칙
  · 이 파일은 화면(View)만 담당한다. 데이터 접근은 db/repository.py에 위임한다.
  · MySQL이 준비되면 자동으로 MySQL을, 아니면 정제 CSV를 사용한다(발표 안전장치).
  · 접근성: 큰 글씨·고대비·아코디언(st.expander) 구조로 스크린리더 탐색을 돕는다.
"""

from __future__ import annotations

# 단독 실행(streamlit run views/faq.py) 시에만 프로젝트 루트를 import 경로에 추가한다.
# main.py에서 views.faq로 임포트될 때는 __package__가 "views"라 아무것도 하지 않는다.
if __package__ in (None, ""):
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

import config
from common import styles
from common.text import to_html
from db.repository import get_repository

# 카테고리별 아이콘 (화면 인지성 향상)
CATEGORY_ICON = {
    "가입·등록": "📝",
    "이용대상·자격": "👥",
    "이용방법·접수": "📱",
    "요금·결제": "💳",
    "배차·대기": "🚕",
    "운행지역·시간": "🗺",
    "준수사항·기타": "📌",
}


@st.cache_resource(show_spinner=False)
def _load_repository():
    """저장소 연결은 한 번만 수행하고 세션 간 재사용한다."""
    return get_repository()


def _render_answer(row: pd.Series, repo) -> None:
    """아코디언 하나의 본문 — 답변·키워드 칩·출처 메타를 그린다."""
    st.markdown(
        f'<div class="faq-answer">{to_html(row["answer"])}</div>',
        unsafe_allow_html=True,
    )

    keywords = repo.keywords_of(int(row["faq_id"]))
    if keywords:
        chips = "".join(f'<span class="kw-chip">#{k}</span>' for k in keywords)
        st.markdown(chips, unsafe_allow_html=True)

    meta = [f"출처: {row['source_name']}"]
    if pd.notna(row.get("department")) and row.get("department"):
        meta.append(f"담당: {row['department']}")
    if pd.notna(row.get("view_count")):
        meta.append(f"원본 조회수: {int(row['view_count']):,}")
    meta.append(f"수집: {str(row['collected_at'])[:10]}")
    st.markdown(
        f'<div class="faq-meta">{" · ".join(meta)}<br>'
        f'<a href="{row["source_url"]}" target="_blank">원문 페이지에서 확인하기 ↗</a>'
        f"</div>",
        unsafe_allow_html=True,
    )


def _render_data_info(repo, status: str) -> None:
    """데이터 출처와 현재 연결 상태를 접이식으로 보여준다."""
    with st.expander("ℹ️ 데이터 출처 및 시스템 정보"):
        s = repo.stats()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("전체 FAQ", f"{s['faq_count']}건")
        m2.metric("분류", f"{s['category_count']}종")
        m3.metric("수집 출처", f"{s['source_count']}곳")
        m4.metric("검색 키워드", f"{s['keyword_count']}개")
        st.dataframe(s["by_category"], use_container_width=True, hide_index=True)
        st.caption(
            "원본: 서울시설공단 장애인콜택시 공식 홈페이지 "
            "(가입안내 · 이용기준 · 이용방법 · 자주하는질문 게시판)  \n"
            f"수집: BeautifulSoup + Selenium · 저장: MySQL `{config.DB_NAME}`  \n"
            f"현재 조회 방식: **{repo.backend}** — {status}"
        )


def render() -> None:
    """FAQ 화면을 그린다. (팀 통합 앱에서 호출하는 진입점)"""
    styles.load("faq.css")

    st.markdown(
        """
        <div class="faq-hero">
            <h2>자주 묻는 질문</h2>
            <p>서울시설공단 장애인콜택시 공식 안내를 질문·답변 형태로 정리했습니다.
            궁금한 내용을 검색하거나 분류를 선택해 확인하세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    try:
        repo, status = _load_repository()
    except RuntimeError as exc:
        st.error(str(exc))
        return

    # ------------------------------------------------------------------ #
    # 검색 조건
    # ------------------------------------------------------------------ #
    categories = ["전체"] + repo.list_categories()
    c1, c2 = st.columns([2.2, 1])
    keyword = c1.text_input(
        "검색어",
        placeholder="예: 요금, 예약, 휠체어, 대기시간",
        help="질문·답변 본문과 검색 키워드를 함께 찾습니다.",
    )
    category = c2.selectbox("분류", categories)

    results = repo.search(keyword=keyword, category=category)

    # ------------------------------------------------------------------ #
    # 결과 요약
    # ------------------------------------------------------------------ #
    summary = f"**{len(results)}건**의 질문이 조회되었습니다."
    if keyword.strip():
        summary += f" (검색어: `{keyword.strip()}`)"
    if category != "전체":
        summary += f" (분류: {category})"
    st.markdown(summary)

    if results.empty:
        st.warning("검색 결과가 없습니다. 다른 검색어나 분류를 선택해 보세요.")
        st.caption("자주 찾는 검색어: 가입, 요금, 접수, 대기, 운행지역")
        return

    # ------------------------------------------------------------------ #
    # 아코디언 목록 (기획서 요구사항: st.expander 형태)
    # ------------------------------------------------------------------ #
    st.write("")
    for _, row in results.iterrows():
        icon = CATEGORY_ICON.get(row["category"], "❔")
        with st.expander(f"{icon} [{row['category']}] {row['question']}"):
            _render_answer(row, repo)

    # ------------------------------------------------------------------ #
    # 데이터 출처 및 연결 상태
    # ------------------------------------------------------------------ #
    st.write("")
    _render_data_info(repo, status)


# 단독 실행용 — 내 파트만 따로 확인할 때 사용
if __name__ == "__main__":
    st.set_page_config(page_title="FAQ · 우리동네 장애인 콜택시",
                       page_icon="❓", layout="wide")
    styles.load("style.css")
    render()
