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

from db.db import get_year_count             # db 스크립트 import

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

def get_dummy_district_stats(gu_name):
    random.seed(hash(gu_name) % 1000)
    return {
        "usage_count": random.randint(300, 1500),
        "avg_wait": round(random.uniform(8, 25), 1),
        "avg_price": random.randint(1700, 50000)
    }


"""연도별 시간대 통계 더미 데이터. TODO: 실제 3개년 탑승내역 기반 함수로 교체"""
def get_dummy_hourly_stats_by_year():
    result = []
    for year in [2023, 2024, 2025]:
        random.seed(year)  # 연도마다 다른 패턴이 나오게
        hour_counter = Counter()
        weights = [1] * 6 + [8, 10, 6, 3, 3, 3, 3, 3, 3, 3, 3] + [9, 10, 5] + [2] * 4

        for _ in range(4000 + (year - 2023) * 500):  # 연도별로 총량도 살짝 다르게
            hour = random.choices(range(24), weights=weights)[0]
            hour_counter[hour] += 1

        for h in range(24):
            result.append({"hour": h, "year": str(year), "count": hour_counter.get(h, 0)})
    return result


"""연도별 총 이용건수 더미. TODO: 실제 탑승내역 집계로 교체"""
def get_dummy_yearly_totals():
    result = get_year_count()

    print(result)
    # print('asdf')

    return pd.DataFrame({
        "연도": ["2023", "2024", "2025"],
        "건수": [42000, 46500, 51200],
    })



"""월별 x 연도별 이용건수 더미. TODO: 실제 탑승내역 집계로 교체"""
def get_dummy_monthly_by_year():
    rows = []
    for year in [2023, 2024, 2025]:
        random.seed(year)
        base = 3000 + (year - 2023) * 300
        for month in range(1, 13):
            rows.append({
                "월": f"{month}월",
                "연도": str(year),
                "건수": base + random.randint(-500, 800),
            })

    return pd.DataFrame(rows)

# ------------------------------------------------------------------
# 메인 페이지
# ------------------------------------------------------------------
def show_useStatus():
    if "selected_gu" not in st.session_state:
        st.session_state.selected_gu = None

    # 타이틀
    st.title("실시간 이용현황 분석")
    st.markdown("서울시 25개 자치구별 콜택시 수요와 대기 시간을 분석하여 투명한 정보를 제공합니다.")

    col_map, col_panel = st.columns([2, 1])

    # ---------- 지도 카드 (기본 container) ----------
    with col_map:
        with st.container(border=True):
            st.subheader("**자치구별 현황 지도**")
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
            stats = get_dummy_district_stats(gu)
            usage_val = f"{stats['usage_count']:,} 건"
            wait_val = f"{stats['avg_wait']} 분"
            price_val = f"{stats['avg_price']:,} 원"
        else:
            usage_val = "- 건"
            wait_val = "- 분"
            price_val = "- 원"

        with st.container(key="panel_dark"):
            st.markdown(
                f"""
                <h4 style="font-size:1.4rem">📍 {gu if gu else '지역을 선택하세요'}</h4>
                <hr style="margin: 1rem 0 2rem;background: #789b37;">
                현재 이용 건수<br>
                <span style="font-size:3rem; font-weight:700;">{usage_val}</span><br><br><br>
                평균 대기 시간<br>
                <span style="font-size:3rem; font-weight:700;">{wait_val}</span><br><br><br>
                평균 이용 요금<br>
                <span style="font-size:3rem; font-weight:700;">{price_val}</span>
                """,
                unsafe_allow_html=True,
            )
            st.write("")

            # 선택한 "구"가 어딘지 값을 session_state에 저장
            def _go_to_reserve():
                st.session_state.page = "reserve"
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
            st.subheader("**시간대별 예약 빈도**")
            st.markdown("출퇴근 시간대(08:00 - 10:00)에 수요가 가장 집중됩니다.")
        with right:
            st.markdown(
                '<span style="color:#F8D6DE;font-weight:700;">● 2023</span> &nbsp; '
                '<span style="color:#A5DAEB;font-weight:700;">● 2024</span> &nbsp; '
                '<span style="color:#CBDD85;font-weight:700;">● 2025</span>',
                unsafe_allow_html=True,
            )

        # TODO: 실제 3개년 탑승내역 기반 함수로 교체
        hourly_data = get_dummy_hourly_stats_by_year()  

        chart = (
            alt.Chart(alt.Data(values=hourly_data))
            .mark_area(opacity=0.55, line={"strokeWidth": 2})
            .encode(
                x=alt.X("hour:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("count:Q", title="예약 건수"),
                color=alt.Color(
                    "year:N",
                    title="연도",
                    scale=alt.Scale(
                        domain=["2023", "2024", "2025"],
                        range=["#F8D6DE", "#A5DAEB", "#CBDD85"],
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
            yearly_df = get_dummy_yearly_totals()  # TODO: 실제 데이터로 교체
            yearly_chart = (
                alt.Chart(yearly_df)
                .mark_bar(size=50, color="#CBDD85")
                .encode(
                    x=alt.X("연도:O", title=None),
                    y=alt.Y("건수:Q", title="건수"),
                    tooltip=["연도", "건수"],
                )
            )
            st.altair_chart(yearly_chart, use_container_width=True)

        with col_month:
            st.markdown("**월별 이용 건수 (연도별 비교)**")
            monthly_df = get_dummy_monthly_by_year()  # TODO: 실제 데이터로 교체
            monthly_chart = (
                alt.Chart(monthly_df)
                .mark_bar()
                .encode(
                    x=alt.X("월:N", title=None, sort=None),
                    xOffset="연도:N",
                    y=alt.Y("건수:Q", title="건수"),
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
    show_useStatus()