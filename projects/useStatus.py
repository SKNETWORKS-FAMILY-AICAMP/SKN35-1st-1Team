"""
이용현황 페이지 (useStatus.py)
"""

import json
import random
from collections import Counter

import altair as alt
import folium   # 지도
import streamlit as st
from streamlit_folium import st_folium

GEOJSON_PATH = "data/seoul_gu_boundary.json"


# ------------------------------------------------------------------
# 데이터 함수 (지금은 더미, 나중에 실제 DB/CSV 조회로 교체)
# ------------------------------------------------------------------
@st.cache_data
def load_seoul_geojson():
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_dummy_hourly_stats():
    random.seed(42)
    hour_counter = Counter()
    weights = [1] * 6 + [8, 10, 6, 3, 3, 3, 3, 3, 3, 3, 3] + [9, 10, 5] + [2] * 4
    for _ in range(5000):
        hour = random.choices(range(24), weights=weights)[0]
        hour_counter[hour] += 1
    return [{"hour": h, "count": hour_counter.get(h, 0)} for h in range(24)]


def get_dummy_district_stats(gu_name):
    random.seed(hash(gu_name) % 1000)
    return {
        "usage_count": random.randint(300, 1500),
        "avg_wait": round(random.uniform(8, 25), 1),
    }


def build_map(selected_gu=None):
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=10.5, tiles="CartoDB positron")
    geo = load_seoul_geojson()

    def style_function(feature):
        gu_name = feature["properties"]["SIG_KOR_NM"]
        is_selected = gu_name == selected_gu
        return {
            "fillColor": "#002045" if is_selected else "#D2E4FF",
            "color": "#002045",
            "weight": 1.5,
            "fillOpacity": 0.9 if is_selected else 0.4,
        }

    folium.GeoJson(
        geo,
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["SIG_KOR_NM"], aliases=["구"]),
    ).add_to(m)
    return m


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

    # ---------------- 지도 카드 (기본 container) ----------------
    with col_map:
        with st.container(border=True):
            st.subheader("**자치구별 현황 지도**")
            m = build_map(selected_gu=st.session_state.selected_gu)
            map_data = st_folium(m, width=None, height=430, key="seoul_map")

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
        else:
            usage_val = "- 건"
            wait_val = "- 분"
 
        with st.container(key="panel_dark"):
            st.markdown(
                f"""
                <h4 style="font-size:1.4rem">📍 {gu if gu else '지역을 선택하세요'}</h4>
                <hr style="margin: 1rem 0 2rem;background: #38609e;">
                현재 이용 건수<br>
                <span style="font-size:3rem; font-weight:700;">{usage_val}</span><br><br><br>
                평균 대기 시간<br>
                <span style="font-size:3rem; font-weight:700;">{wait_val}</span>
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
                on_click=_go_to_reserve, # session_state에 저장한 내가 선택한 "구" 값을 가지고 이동
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
                '<span style="color:#002045;font-weight:700;">● 피크 시간</span> &nbsp; '
                '<span style="color:#AAB9D2;font-weight:700;">● 일반 시간</span>',
                unsafe_allow_html=True,
            )

        hourly_data = get_dummy_hourly_stats()  # TODO: 실제 탑승내역 기반 함수로 교체
        peak_threshold = sorted(d["count"] for d in hourly_data)[-3]
        for d in hourly_data:
            d["is_peak"] = d["count"] >= peak_threshold

        chart = (
            alt.Chart(alt.Data(values=hourly_data))
            .mark_bar()
            .encode(
                x=alt.X("hour:O", title=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y("count:Q", title="예약 건수"),
                color=alt.condition(
                    alt.datum.is_peak, alt.value("#002045"), alt.value("#AAB9D2")
                ),
                tooltip=["hour:O", "count:Q"],
            )
            .properties(height=320)
        )
        st.altair_chart(chart, use_container_width=True)

    st.write("")

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