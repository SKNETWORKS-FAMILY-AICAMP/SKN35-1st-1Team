"""
관련뉴스 화면
-------------
탭(전체/복지사업/지원사업/택시소식) + 2열 카드 그리드 + 검색 + 페이지네이션.
뉴스 데이터와 검색 로직은 common/news_data.py에 있다.
"""

from __future__ import annotations

import streamlit as st

from common import news_data, styles
from common.news_data import CATEGORY_CLASS, PER_PAGE, TABS
from db.db import get_news_data
import pandas as pd

from html import escape
from pathlib import Path
from urllib.parse import urlparse

PER_PAGE = 6

TABS = [
    ("전체", "전체"),
    ("복지·지원사업", "복지지원사업"),
    ("장애인콜택시", "장애인콜택시"),
]

CATEGORY_CLASS = {
    "복지지원사업": "welfare",
    "장애인콜택시": "taxi",
}

REQUIRED_COLUMNS = {
    "category",
    "keyword",
    "headline",
    "body",
    "press",
    "url",
    "crawled_at",
}

# def _find_csv() -> Path:
#     """실행 위치와 무관하게 프로젝트 안의 CSV 파일을 찾는다."""
#     here = Path(__file__).resolve().parent
#     candidates = [
#         here / CSV_FILE_NAME,
#         here.parent / CSV_FILE_NAME,
#         here / "data" / CSV_FILE_NAME,
#         here.parent / "data" / CSV_FILE_NAME,
#         Path.cwd() / CSV_FILE_NAME,
#         Path.cwd() / "data" / CSV_FILE_NAME,
#     ]

#     for path in candidates:
#         if path.is_file():
#             return path

#     searched = "\n".join(f"- {path}" for path in candidates)
#     raise FileNotFoundError(
#         f"'{CSV_FILE_NAME}' 파일을 찾지 못했습니다.\n"
#         f"다음 위치 중 한 곳에 CSV를 넣어 주세요.\n{searched}"
#     )


@st.cache_data(show_spinner=False)
def _load_news() -> list[dict[str, str]]:
    """
    CSV 컬럼명을 화면에서 사용하는 이름으로 변환한다.

    modified_time은 CSV가 변경됐을 때 Streamlit 캐시를 자동 갱신하기 위한 값이다.
    """
    # del modified_time

    # try:
    #     df = pd.read_csv(csv_path, encoding="utf-8-sig")
    # except UnicodeDecodeError:
    #     df = pd.read_csv(csv_path, encoding="cp949")

    result = get_news_data()
    df = pd.DataFrame(result)

    df.columns = df.columns.astype(str).str.strip()
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "CSV에 필요한 컬럼이 없습니다: "
            + ", ".join(sorted(missing))
            + "\n현재 컬럼: "
            + ", ".join(df.columns)
        )

    # CSV 컬럼 → 기존 뉴스 카드가 사용하는 필드
    news = df.rename(
        columns={
            "category": "cat",
            "headline": "title",
            "body": "desc",
            "press": "source",
            "crawled_at": "date",
        }
    ).copy()

    text_columns = ["cat", "keyword", "title", "desc", "source", "url"]
    for column in text_columns:
        news[column] = news[column].fillna("").astype(str).str.strip()

    parsed_date = pd.to_datetime(news["date"], errors="coerce")
    news["sort_date"] = parsed_date
    news["date"] = parsed_date.dt.strftime("%Y.%m.%d").fillna("")

    news = (
        news.drop_duplicates(subset=["url"], keep="first")
        .sort_values("sort_date", ascending=False, na_position="last")
    )

    return news[
        ["cat", "keyword", "title", "desc", "source", "url", "date"]
    ].to_dict("records")


def _safe_url(url: str) -> str:
    """카드 링크에는 http/https 주소만 허용한다."""
    parsed = urlparse(url)
    return url if parsed.scheme in {"http", "https"} else "#"

# def _card_html(item: dict[str, str]) -> str:
#     """뉴스 카드 한 장. 카테고리 색상은 CSS 클래스(.nbadge.*)로 처리한다."""
#     cate_class = CATEGORY_CLASS.get(item["cat"], "")
#     return f"""
#     <div class="ncard">
#         <div class="ncard-top">
#             <span class="nbadge {cate_class}">{item['cat']}</span>
#             <span class="ndate">{item['date']}</span>
#         </div>
#         <div class="ntitle">{item['title']}</div>
#         <div class="ndesc">{item['desc']}</div>
#         <div class="ndiv"></div>
#         <div class="ncard-bot">
#             <span class="nsource">{item['source']}</span>
#             <a class="nlink" href="{item['url']}" target="_blank" rel="noopener">원문보기 ↗</a>
#         </div>
#     </div>
#     """

def _card_html(item: dict[str, str]) -> str:
    """뉴스 카드 한 장을 HTML로 만든다."""
    cat = escape(item["cat"])
    cate_class = CATEGORY_CLASS.get(item["cat"], "")
    date = escape(item["date"])
    title = escape(item["title"])
    desc = escape(item["desc"])
    source = escape(item["source"])
    url = escape(_safe_url(item["url"]), quote=True)

    return f"""
    <div class="ncard">
        <div class="ncard-top">
            <span class="nbadge {cate_class}">{cat}</span>
            <span class="ndate">{date}</span>
        </div>
        <div class="ntitle">{title}</div>
        <div class="ndesc">{desc}</div>
        <div class="ndiv"></div>
        <div class="ncard-bot">
            <span class="nsource">{source}</span>
            <a class="nlink" href="{url}" target="_blank"
               rel="noopener noreferrer">원문보기 ↗</a>
        </div>
    </div>
    """


def _pagination(cat: str, page: int, pages: int) -> None:
    """페이지가 2개 이상일 때만 ‹ 1 2 3 › 버튼을 그린다."""
    if pages <= 1:
        return
    st.write("")
    _, mid, _ = st.columns([1, 3, 1])
    with mid:
        cols = st.columns(pages + 2)
        if cols[0].button("‹", key=f"pg_{cat}_prev", disabled=(page == 1),
                          use_container_width=True):
            st.session_state[f"npage_{cat}"] = max(1, page - 1)
            st.rerun()
        for i in range(1, pages + 1):
            if cols[i].button(str(i), key=f"pg_{cat}_{i}", use_container_width=True,
                              type="primary" if i == page else "secondary"):
                st.session_state[f"npage_{cat}"] = i
                st.rerun()
        if cols[pages + 1].button("›", key=f"pg_{cat}_next", disabled=(page == pages),
                                  use_container_width=True):
            st.session_state[f"npage_{cat}"] = min(pages, page + 1)
            st.rerun()


# def _grid(cat: str, keyword: str) -> None:
#     """탭 하나의 내용 — 검색 결과를 2열 카드로 그리고 페이지를 나눈다."""
#     items = news_data.search(cat, keyword)

#     # 검색어가 바뀌면 해당 탭을 1페이지로 되돌린다
#     sig_key, page_key = f"nsig_{cat}", f"npage_{cat}"
#     if st.session_state.get(sig_key) != keyword:
#         st.session_state[sig_key] = keyword
#         st.session_state[page_key] = 1

#     total = len(items)
#     pages = max(1, -(-total // PER_PAGE))
#     page = min(st.session_state.get(page_key, 1), pages)
#     st.session_state[page_key] = page

#     st.markdown(f"**{total}건**의 뉴스" + (f"  ·  검색어: `{keyword}`" if keyword else ""))
#     st.write("")
#     if total == 0:
#         st.warning("검색 결과가 없습니다. 다른 검색어나 탭을 선택해 보세요.")
#         return

#     start = (page - 1) * PER_PAGE
#     grid = st.columns(2, gap="medium")
#     for idx, item in enumerate(items[start:start + PER_PAGE]):
#         with grid[idx % 2]:
#             st.markdown(_card_html(item), unsafe_allow_html=True)
#     _pagination(cat, page, pages)

def _search(
    all_items: list[dict[str, str]], cat: str, keyword: str
) -> list[dict[str, str]]:
    """카테고리와 검색어로 뉴스를 필터링한다."""
    normalized_keyword = keyword.casefold()
    searchable_fields = ("title", "desc", "source", "keyword", "cat")

    results = []
    for item in all_items:
        if cat != "전체" and item["cat"] != cat:
            continue
        if normalized_keyword and not any(
            normalized_keyword in item[field].casefold()
            for field in searchable_fields
        ):
            continue
        results.append(item)
    return results

def _grid(
    all_items: list[dict[str, str]], cat: str, keyword: str
) -> None:
    """탭 하나의 검색 결과를 2열 카드와 페이지로 표시한다."""
    items = _search(all_items, cat, keyword)

    # 검색어가 바뀌면 해당 탭을 1페이지로 되돌린다.
    sig_key = f"nsig_{cat}"
    page_key = f"npage_{cat}"
    search_signature = keyword.casefold()
    if st.session_state.get(sig_key) != search_signature:
        st.session_state[sig_key] = search_signature
        st.session_state[page_key] = 1

    total = len(items)
    pages = max(1, (total + PER_PAGE - 1) // PER_PAGE)
    page = min(max(st.session_state.get(page_key, 1), 1), pages)
    st.session_state[page_key] = page

    result_text = f"**{total}건**의 뉴스"
    if keyword:
        result_text += f"  ·  검색어: `{keyword}`"
    st.markdown(result_text)
    st.write("")

    if total == 0:
        st.warning("검색 결과가 없습니다. 다른 검색어나 탭을 선택해 보세요.")
        return

    start = (page - 1) * PER_PAGE
    grid = st.columns(2, gap="medium")
    for index, item in enumerate(items[start : start + PER_PAGE]):
        with grid[index % 2]:
            st.markdown(_card_html(item), unsafe_allow_html=True)

    _pagination(cat, page, pages)


def render() -> None:
    """관련뉴스 화면을 그린다."""
    styles.load("news.css")

    st.header("📰 관련뉴스")
    st.caption("장애인콜택시와 관련된 최신 소식과 정책 변화, 이용 안내 정보를 한눈에 확인하세요.")

    try:
        # csv_path = _find_csv()
        all_items = _load_news()
    except (FileNotFoundError, ValueError, OSError, pd.errors.ParserError) as error:
        st.error("뉴스 데이터를 불러오지 못했습니다.")
        st.code(str(error))
        return

    keyword = st.text_input("검색", placeholder="뉴스 제목이나 키워드를 검색하세요",
                            label_visibility="collapsed").strip()

    # tabs = st.tabs([label for label, _ in TABS])
    # for tab, (_, cat) in zip(tabs, TABS):
    #     with tab:
    #         _grid(cat, keyword)

    tabs = st.tabs([label for label, _ in TABS])
    for tab, (_, category) in zip(tabs, TABS):
        with tab:
            _grid(all_items, category, keyword)

    # loaded_at = datetime.fromtimestamp(csv_path.stat().st_mtime)
    # st.caption(
    #     f"총 {len(all_items)}건 · 데이터 파일 갱신 "
    #     f"{loaded_at:%Y.%m.%d %H:%M}"
    # )

    st.caption("※ 표시된 소식은 UI 예시(Dummy) 콘텐츠입니다.")
