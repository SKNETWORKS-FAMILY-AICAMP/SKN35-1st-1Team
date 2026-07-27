"""
이용현황 페이지 (useStatus.py)
"""

import json
import random
from collections import Counter
import pandas as pd

import altair as alt            # 그래프
import folium                   # 지도
import streamlit as st
from streamlit_folium import st_folium


# db 스크립트 import
from db.db import get_year_count, get_month_count, get_hour_count, get_district_summary
from common import styles

GEOJSON_PATH = "data/seoul_gu_boundary.json"


# ------------------------------------------------------------------
# 데이터 함수 (지금은 더미, 나중에 실제 DB/CSV 조회로 교체)
# ------------------------------------------------------------------

@st.cache_data
def load_seoul_geojson():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def build_map(selected_gu=None):
    m = folium.Map(
        location=[37.5665, 126.9780],
        zoom_start=10.5,
        tiles="CartoDB positron",
        min_zoom=11,
        max_bounds=True,
        min_lat=37.30,
        max_lat=37.80,
        min_lon=126.65,
        max_lon=127.30,
    )

    geo = load_seoul_geojson()

    def style_function(feature):
        gu_name = feature["properties"]["SIG_KOR_NM"]
        is_selected = gu_name == selected_gu
        return {
            "fillColor": "#7B8847" if is_selected else "#CBDD85",
            "color": "#3A4122",
            "weight": 1.5,
            "fillOpacity": 0.9 if is_selected else 0.4,
        }

    folium.GeoJson(
        geo,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["SIG_KOR_NM"], aliases=["구"]),
    ).add_to(m)

    return m


"""연도별 시간대 통계 데이터 """
@st.cache_data
def get_hourly_stats_by_year():
    result = get_hour_count()

    return [
        {"hour": int(row["hr"]), "year": str(row["yr"]), "count": row["trip_count"]}
        for row in result
    ]


"""연도별 총 이용건수"""
@st.cache_data
def get_yearly_total():
    result = get_year_count()
    # result 예시: [(2025, 1729476), (2024, 1695539), (2023, 1772364)]

    years = [str(row["source_year"]) for row in result]
    counts = [row["trip_count"] for row in result]


    df = pd.DataFrame({"연도": years, "건수": counts})
    df = df.sort_values("연도").reset_index(drop=True)  # 2023, 2024, 2025 순서로 정렬

    return df


"""월별 x 연도별 이용건수"""
@st.cache_data
def get_monthly_by_year():
    result = get_month_count()  # datetime

    rows = [
        {"월": f"{row['mo']}월", "연도": str(row['yr']), "건수": row['trip_count']}
        for row in result
        if row['yr'] is not None and row['mo'] is not None
    ]

    return pd.DataFrame(rows)

# ------------------------------------------------------------------
# 메인 페이지
# ------------------------------------------------------------------
def render():
    styles.load("useStatus.css")

    if "selected_gu" not in st.session_state:
        st.session_state.selected_gu = None

    # 타이틀
    st.title("실시간 이용현황 분석")
    st.markdown("서울시 25개 자치구별 콜택시 수요와 대기 시간을 분석하여 투명한 정보를 제공합니다.")

    col_map, col_panel = st.columns([2, 1])

    # ---------- 지도 카드 (기본 container) ----------
    with col_map:
        with st.container(border=True):
            st.markdown("**자치구별 현황 지도**")
            m = build_map(selected_gu=st.session_state.selected_gu)
            map_data = st_folium(m, width=None, height=580, key="seoul_map")

            if map_data and map_data.get("last_active_drawing"):
                clicked_gu = map_data["last_active_drawing"]["properties"]["SIG_KOR_NM"]
                if clicked_gu != st.session_state.selected_gu:
                    st.session_state.selected_gu = clicked_gu
                    st.rerun()

    # ---------------- 우측 정보 패널 ----------------
    with col_panel:
        gu = st.session_state.selected_gu
        if gu:
            stats = get_district_summary(gu)

            if stats:
                daily_avg_count = stats["daily_avg_count"]
                avg_wait_minutes = stats["avg_wait_minutes"]
                avg_fare = stats["avg_fare"]

                usage_val = (
                    f"{daily_avg_count:,.1f} 건"
                    if daily_avg_count is not None
                    else "- 건"
                )
                wait_val = (
                    f"{avg_wait_minutes:,.1f} 분"
                    if avg_wait_minutes is not None
                    else "- 분"
                )
                price_val = (
                    f"{avg_fare:,.0f} 원"
                    if avg_fare is not None
                    else "- 원"
                )
            else:
                usage_val = "- 건"
                wait_val = "- 분"
                price_val = "- 원"
        else:
            usage_val = "- 건"
            wait_val = "- 분"
            price_val = "- 원"

        with st.container(key="panel_dark"):
            st.markdown(
                f"""
                <h4 style="font-size:1.4rem">📍 {gu if gu else '지역을 선택하세요'}</h4>
                <hr style="margin: 1rem 0 2rem;background: #789b37;">
                일평균 이용 건수<br>
                <span style="font-size:3rem; font-weight:700;">{usage_val}</span><br><br><br>
                평균 배차 대기시간<br>
                <span style="font-size:3rem; font-weight:700;">{wait_val}</span><br><br><br>
                평균 이용 요금<br>
                <span style="font-size:3rem; font-weight:700;">{price_val}</span>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            # 선택한 "구"가 어딘지 값을 session_state에 저장
            def _go_to_reserve():
                st.session_state.menu = "reserve"
                st.session_state.prefill_depart = gu

            # 해당 버튼 클릭 시 "예약하기"페이지로 이동
            st.button(
                "이 구역 예약하기",
                use_container_width=True,
                type="primary",
                disabled=(gu is None),
                on_click=_go_to_reserve,  # session_state에 저장한 내가 선택한 "구" 값을 가지고 이동
            )

    st.write("")

    # ---------------- 시간대별 예약 빈도 ----------------
    with st.container(border=True):
        left, right = st.columns([3, 1])
        with left:
            st.markdown("**시간대별 예약 빈도**")
            # st.markdown("출퇴근 시간대(08:00 - 10:00)에 수요가 가장 집중됩니다.")
        with right:
            st.markdown(
                '<span style="color:#F8D6DE;font-weight:700;">● 2023</span> &nbsp; '
                '<span style="color:#A5DAEB;font-weight:700;">● 2024</span> &nbsp; '
                '<span style="color:#CBDD85;font-weight:700;">● 2025</span>',
                unsafe_allow_html=True,
            )

        hourly_data = get_hourly_stats_by_year()
        hourly_data = [d for d in hourly_data if 7 <= d["hour"] <= 21]

        chart = (
            alt.Chart(alt.Data(values=hourly_data))
            # .mark_area(opacity=0.55, line={"strokeWidth": 2})
            .mark_line(strokeWidth=3, point={"size": 80})
            .encode(
                x=alt.X(
                    "hour:O",
                    title=None,
                    axis=alt.Axis(labelAngle=0, labelExpr="datum.label + '시'"),
                ),
                y=alt.Y("count:Q", title=None, stack=None),
                color=alt.Color(
                    "year:N",
                    title="연도",
                    scale=alt.Scale(
                        domain=["2023", "2024", "2025"],
                        range=["#F3B7C5", "#8AD4ED", "#B8CC66"],
                    ),
                ),
                tooltip=["year:N", "hour:O", "count:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

    st.write("")

    # ---------------- 연도별 / 월별 이용 건수 ----------------
    with st.container(border=True):
        col_year, col_month = st.columns([1, 3])

        with col_year:
            st.markdown("**연도별 이용 건수**")
            yearly_df = get_yearly_total()
            yearly_chart = (
                alt.Chart(yearly_df)
                .mark_bar(size=50, color="#CBDD85")
                .encode(
                    x=alt.X("연도:O", title=None, axis=alt.Axis(labelAngle=0)),
                    y=alt.Y("건수:Q", title=None),
                    tooltip=["연도", "건수"],
                )
            )
            st.altair_chart(yearly_chart, use_container_width=True)

        with col_month:
            st.markdown("**월별 이용 건수 (연도별 비교)**")
            monthly_df = get_monthly_by_year()  # TODO: 실제 데이터로 교체
            monthly_chart = (
                alt.Chart(monthly_df)
                .mark_bar()
                .encode(
                    x=alt.X("월:N", title=None, sort=None, axis=alt.Axis(labelAngle=0)),
                    xOffset="연도:N",
                    y=alt.Y("건수:Q", title=None),
                    color=alt.Color(
                        "연도:N",
                        title="연도",
                        scale=alt.Scale(
                            domain=["2023", "2024", "2025"],
                            range=["#F8D6DE", "#A5DAEB", "#CBDD85"],
                        ),
                    ),
                    tooltip=["연도", "월", "건수"],
                )
            )
            st.altair_chart(monthly_chart, use_container_width=True)

    # ---------------- 하단 안내 카드 ----------------
    info1, info2 = st.columns(2)

    with info1:
        with st.container(border=True, key="info_box_1"):
            st.markdown("ℹ️ **정기 점검 안내**")
            st.caption("매월 세 번째 일요일 새벽 2시~4시는 시스템 점검 시간입니다.")

    with info2:
        with st.container(border=True, key="info_box_2"):
            st.markdown("🎧 **24시 상담 지원**")
            st.caption("도움이 필요하시면 언제든 1588-4388로 연락주세요.")


if __name__ == "__main__":
    st.set_page_config(page_title="이용현황 - 우리동네 장애인콜택시", layout="wide")
    render()