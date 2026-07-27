"""
[담당 파트] FAQ 화면 — 우리동네 장애인 콜택시
---------------------------------------------
팀 통합 앱의 4개 메뉴 중 'FAQ' 하나를 담당하는 모듈이다.

팀장 병합 방법
    from app.faq_page import render as render_faq
    ...
    if menu == "FAQ":
        render_faq()

설계 원칙
  · 이 파일은 화면(View)만 담당한다. 데이터 접근은 db/repository.py에 위임한다.
  · MySQL이 준비되면 자동으로 MySQL을, 아니면 정제 CSV를 사용한다(발표 안전장치).
  · 접근성: 큰 글씨·고대비·아코디언(st.expander) 구조로 스크린리더 탐색을 돕는다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config                                # noqa: E402
from db.repository import get_repository     # noqa: E402

PRIMARY = "#1a365d"
PRIMARY_DARK = "#0f2440"

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


def _inject_style() -> None:
    """FAQ 화면 전용 스타일 — 접근성을 위해 본문 글씨를 키운다."""
    st.markdown(
        f"""
        <style>
        .faq-hero {{
            background: linear-gradient(135deg, {PRIMARY} 0%, {PRIMARY_DARK} 100%);
            color:#fff; padding:24px 28px; border-radius:16px; margin-bottom:18px;
        }}
        .faq-hero h2 {{ color:#fff; margin:0 0 6px 0; font-size:1.7rem; }}
        .faq-hero p  {{ color:#e3ecff; margin:0; font-size:1.02rem; }}
        div[data-testid="stExpander"] details summary p {{
            font-size:1.12rem; font-weight:700;
        }}
        .faq-answer {{ font-size:1.05rem; line-height:1.85; }}
        .faq-meta {{
            color:#6b7280; font-size:0.86rem; border-top:1px dashed #d1d5db;
            margin-top:14px; padding-top:10px;
        }}
        .kw-chip {{
            display:inline-block; background:#eef4ff; color:{PRIMARY_DARK};
            border-radius:12px; padding:2px 10px; margin:2px 4px 2px 0;
            font-size:0.82rem; font-weight:600;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render() -> None:
    """FAQ 화면을 그린다. (팀 통합 앱에서 호출하는 진입점)"""
    _inject_style()

    st.markdown(
        """
        <div class="faq-hero">
            <h2>❓ 자주 묻는 질문</h2>
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
            st.markdown(
                f'<div class="faq-answer">{_to_html(row["answer"])}</div>',
                unsafe_allow_html=True,
            )

            kws = repo.keywords_of(int(row["faq_id"]))
            if kws:
                chips = "".join(f'<span class="kw-chip">#{k}</span>' for k in kws)
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

    # ------------------------------------------------------------------ #
    # 데이터 출처 및 연결 상태
    # ------------------------------------------------------------------ #
    st.write("")
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


def _to_html(text: str) -> str:
    """답변 본문의 개행을 HTML 줄바꿈으로 바꾼다 (태그는 이스케이프)."""
    import html as _html
    return _html.escape(str(text)).replace("\n", "<br>")


# 단독 실행용 — 내 파트만 따로 확인할 때 사용
if __name__ == "__main__":
    st.set_page_config(page_title="FAQ · 우리동네 장애인 콜택시",
                       page_icon="❓", layout="wide")
    render()
