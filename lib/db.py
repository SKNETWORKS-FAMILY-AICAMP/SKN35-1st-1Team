# -*- coding: utf-8 -*-
"""
db.py — 데이터 접근 계층 (Data Access Layer)
------------------------------------------------
설계 의도:
  · 화면(pages/*)은 이 모듈의 함수만 호출한다. (DB인지 샘플인지 몰라도 됨)
  · st.secrets 에 [mysql] 이 있고 연결에 성공하면 → MySQL 조회
  · 없거나 실패하면 → lib/sample_data.py 의 샘플로 폴백
  · 팀원은 아래 각 함수의 '# TODO(DB)' 부분에 실제 SQL 만 채우면 된다.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from lib import sample_data as sd


# --------------------------------------------------------------------- #
# 연결 관리
# --------------------------------------------------------------------- #
@st.cache_resource(show_spinner=False)
def _get_conn():
    """MySQL 연결 시도. 실패하면 None (샘플 모드)."""
    try:
        import pymysql

        cfg = st.secrets["mysql"]
        conn = pymysql.connect(
            host=cfg["host"],
            port=int(cfg.get("port", 3306)),
            user=cfg["user"],
            password=cfg["password"],
            database=cfg["database"],
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
        )
        return conn
    except Exception:
        return None


def using_db() -> bool:
    return _get_conn() is not None


def _query(sql: str, params: tuple = ()) -> pd.DataFrame | None:
    conn = _get_conn()
    if conn is None:
        return None
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
        return pd.DataFrame(rows)
    except Exception as e:  # 조회 실패 시 조용히 샘플로 폴백
        print(f"[db] query 실패 → 샘플 폴백: {e}")
        return None


# --------------------------------------------------------------------- #
# 1) 지원사업 공고
# --------------------------------------------------------------------- #
def get_support_programs(region: str | None = None,
                         targets: list[str] | None = None) -> pd.DataFrame:
    # TODO(DB): SELECT * FROM support_programs WHERE region=%s AND target_type IN (...)
    df = _query("SELECT * FROM support_programs")
    if df is None:
        df = pd.DataFrame(sd.SUPPORT_PROGRAMS)
    if region and region != "전체":
        df = df[df["region"] == region]
    if targets:
        df = df[df["target_type"].isin(targets)]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------- #
# 2) 판매자 / 리뷰
# --------------------------------------------------------------------- #
def get_sellers(region: str | None = None) -> pd.DataFrame:
    df = _query("SELECT * FROM sellers")
    if df is None:
        df = pd.DataFrame(sd.SELLERS)
    if region and region != "전체":
        df = df[df["region"] == region]
    return df.reset_index(drop=True)


def get_reviews(seller_id: int) -> list[dict]:
    df = _query("SELECT * FROM seller_reviews WHERE seller_id=%s", (seller_id,))
    if df is None:
        return sd.SELLER_REVIEWS.get(seller_id, [])
    return df.to_dict("records")


# --------------------------------------------------------------------- #
# 3) 개조/검사
# --------------------------------------------------------------------- #
def get_modification_steps(device_type: str) -> list[dict]:
    df = _query("SELECT * FROM modification_steps WHERE device_type=%s ORDER BY step_no", (device_type,))
    if df is None:
        return sd.MODIFICATION_STEPS.get(device_type, [])
    return df.to_dict("records")


def get_device_types() -> list[str]:
    return list(sd.MODIFICATION_STEPS.keys())


def get_inspection_shops(region: str | None = None) -> pd.DataFrame:
    df = _query("SELECT * FROM inspection_shops")
    if df is None:
        df = pd.DataFrame(sd.INSPECTION_SHOPS)
    if region and region != "전체":
        df = df[df["region"] == region]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------- #
# 4) 등록 통계
# --------------------------------------------------------------------- #
def get_registration_stats() -> pd.DataFrame:
    df = _query("SELECT region, registered FROM registration_stats WHERE year=2024")
    if df is None:
        df = pd.DataFrame(sd.REGISTRATION_STATS)[["region", "registered"]]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------- #
# 5) 편의시설
# --------------------------------------------------------------------- #
def get_facilities(region: str | None = None, kinds: list[str] | None = None) -> pd.DataFrame:
    df = _query("SELECT * FROM facilities")
    if df is None:
        df = pd.DataFrame(sd.FACILITIES)
    if region and region != "전체":
        df = df[df["region"] == region]
    if kinds:
        df = df[df["kind"].isin(kinds)]
    return df.reset_index(drop=True)


# --------------------------------------------------------------------- #
# 6) FAQ / 기관 게시판
# --------------------------------------------------------------------- #
def get_faqs() -> list[dict]:
    df = _query("SELECT * FROM faqs ORDER BY created_at DESC")
    if df is None:
        return list(sd.FAQS)
    return df.to_dict("records")


def get_agency_notices(agency: str) -> list[dict]:
    # 기관별 게시판 (입력 없이 섹션으로만 구분)
    return sd.AGENCY_NOTICES.get(agency, [])
