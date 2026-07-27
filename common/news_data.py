"""
common/news_data.py
관련뉴스 데이터 소스 - MySQL DB 조회.
UI가 참조하는 인터페이스는 기존과 100% 동일하게 유지한다.
"""
from __future__ import annotations
import pymysql
import pymysql.cursors
import streamlit as st

DB_CONFIG = dict(
    host="localhost",
    port=3306,
    user="root",
    password="1234",
    database="newsdb",
    charset="utf8mb4",
)
TABLE_NAME = "disability_news"

PER_PAGE = 6
TABS = [
    ("전체", "전체"),
    ("복지사업", "복지사업"),
    ("지원사업", "지원사업"),
    ("택시소식", "택시소식"),
]
CATEGORY_CLASS = {
    "복지사업": "welfare",
    "지원사업": "support",
    "택시소식": "taxi",
}


def _map_category(keyword: str) -> str:
    if "콜택시" in keyword:
        return "택시소식"
    if "지원" in keyword:
        return "지원사업"
    if "복지" in keyword:
        return "복지사업"
    return "기타"


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_all() -> list[dict]:
    conn = pymysql.connect(cursorclass=pymysql.cursors.DictCursor, **DB_CONFIG)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT category, keyword, headline, body, press, url, crawled_at "
                f"FROM {TABLE_NAME} ORDER BY crawled_at DESC"
            )
            rows = cur.fetchall()
    finally:
        conn.close()

    items: list[dict] = []
    for r in rows:
        desc = (r["body"] or "").strip()
        if len(desc) > 90:
            desc = desc[:90] + "..."
        items.append({
            "cat": _map_category(r["keyword"] or ""),
            "date": str(r["crawled_at"])[:10],
            "title": r["headline"],
            "desc": desc,
            "source": r["press"],
            "url": r["url"],
        })
    return items


def search(cat: str, keyword: str) -> list[dict]:
    items = _fetch_all()
    if cat != "전체":
        items = [i for i in items if i["cat"] == cat]
    if keyword:
        kw = keyword.lower()
        items = [i for i in items if kw in i["title"].lower() or kw in i["desc"].lower()]
    return items
