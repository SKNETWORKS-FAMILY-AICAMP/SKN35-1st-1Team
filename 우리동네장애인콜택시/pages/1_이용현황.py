"""서울시 장애인콜택시 이용현황 - 필터, KPI, 시각화, 자치구 상세정보."""
from __future__ import annotations

import datetime

import pandas as pd
import plotly.express as px
import streamlit as st

from components.accessibility import apply_accessibility_css
from components.header import render_page_header
from components.metric_cards import render_metric_cards
from components.navigation import render_home_link
from districts import SEOUL_DISTRICTS, WEEKDAY_NAMES_KO
from services import taxi_service as svc
from services.database import check_connection

st.set_page_config(page_title="이용현황 | 우리동네 장애인 콜택시", page_icon="📊", layout="wide")
apply_accessibility_css()
render_home_link()
render_page_header("서울시 장애인콜택시 이용현황", "지역별·시간대별 과거 통계(참고용)")

if not check_connection():
    st.error(
        "🔌 데이터베이스에 연결할 수 없어 통계를 불러올 수 없습니다. "
        "잠시 후 다시 시도하거나 관리자에게 문의해 주세요.",
        icon="🚨",
    )
    st.stop()

with st.expander("⏱️ 대기시간 용어 설명 (꼭 확인해 주세요)"):
    st.markdown(
        "- **배차 대기시간** = 배차일시 − 접수일시\n"
        "- **승차 대기시간** = 승차일시 − 접수일시\n"
        "- **탑승 준비시간** = 승차일시 − 배차일시\n"
        "- **이동시간** = 하차일시 − 승차일시\n\n"
        "화면의 모든 '배차 대기시간'/'승차 대기시간'은 위 정의를 따릅니다."
    )

# ---------------------------------------------------------------------
# 필터
# ---------------------------------------------------------------------
st.subheader("🔎 조회 조건")

monthly_all = svc.get_monthly_trend()
if not monthly_all.empty:
    first, last = monthly_all.iloc[0], monthly_all.iloc[-1]
    default_start = datetime.date(int(first["year"]), int(first["month"]), 1)
    default_end = (pd.Timestamp(int(last["year"]), int(last["month"]), 1) + pd.offsets.MonthEnd(0)).date()
else:
    default_end = datetime.date.today()
    default_start = default_end - datetime.timedelta(days=90)

filter_col1, filter_col2 = st.columns(2)
with filter_col1:
    start_date = st.date_input("조회 시작일", value=default_start)
with filter_col2:
    end_date = st.date_input("조회 종료일", value=default_end)
if start_date > end_date:
    st.warning("조회 시작일이 종료일보다 늦습니다. 시작일과 종료일을 확인해 주세요.")
    start_date, end_date = end_date, start_date

area_options = ["전체"] + SEOUL_DISTRICTS
filter_col3, filter_col4, filter_col5 = st.columns(3)
with filter_col3:
    origin_choice = st.selectbox("출발 자치구", area_options)
with filter_col4:
    destination_choice = st.selectbox("도착 자치구", area_options)
with filter_col5:
    weekday_choice = st.selectbox("요일", ["전체"] + WEEKDAY_NAMES_KO)

filter_col6, filter_col7, filter_col8 = st.columns(3)
with filter_col6:
    time_group_choice = st.selectbox("시간대", ["전체", "새벽(00-06시)", "오전(06-12시)", "오후(12-18시)", "저녁/야간(18-24시)"])
with filter_col7:
    purpose_options = ["전체"] + svc.get_purpose_options()
    purpose_choice = st.selectbox("이용 목적", purpose_options)
with filter_col8:
    vehicle_options = ["전체"] + svc.get_vehicle_type_options()
    vehicle_choice = st.selectbox("차량 구분", vehicle_options)

origin_district = None if origin_choice == "전체" else origin_choice
destination_district = None if destination_choice == "전체" else destination_choice
purpose_group = None if purpose_choice == "전체" else purpose_choice
vehicle_type = None if vehicle_choice == "전체" else vehicle_choice

st.caption("요일·시간대는 시간대 차트에, 이용목적·차량구분은 해당 분포 차트에 적용됩니다.")

st.divider()

# ---------------------------------------------------------------------
# KPI
# ---------------------------------------------------------------------
st.subheader("📌 핵심 지표")
kpi = svc.get_kpi_summary(start_date, end_date, origin_district)

if not kpi["has_data"]:
    st.info("선택하신 조건에 해당하는 데이터가 없습니다. 조회 기간이나 자치구를 조정해 보세요.", icon="📭")
else:
    def _fmt_min(v):
        return "정보없음" if v is None else f"{v:.1f}분"

    def _fmt_count(v):
        return f"{v:,}건"

    render_metric_cards([
        {"label": "전체 접수 건수", "value": _fmt_count(kpi["request_count"])},
        {"label": "실제 이용 건수", "value": _fmt_count(kpi["ride_count"]), "help": "승차 이후(승차+완료) 건수"},
        {"label": "완료 건수", "value": _fmt_count(kpi["completed_count"])},
        {"label": "취소 건수", "value": _fmt_count(kpi["cancel_count"])},
    ])
    render_metric_cards([
        {"label": "취소율", "value": "정보없음" if kpi["cancel_rate"] is None else f"{kpi['cancel_rate']:.1f}%"},
        {"label": "평균 배차 대기시간", "value": _fmt_min(kpi["avg_dispatch_wait_min"]), "help": "배차일시-접수일시"},
        {"label": "중앙값 배차 대기시간", "value": _fmt_min(kpi["median_dispatch_wait_min"])},
        {"label": "평균 승차 대기시간", "value": _fmt_min(kpi["avg_pickup_wait_min"]), "help": "승차일시-접수일시"},
    ])
    render_metric_cards([
        {"label": "중앙값 승차 대기시간", "value": _fmt_min(kpi["median_pickup_wait_min"])},
        {"label": "평균 이동거리", "value": "정보없음" if kpi["avg_distance"] is None else f"{kpi['avg_distance']:.1f}km"},
        {"label": "평균 요금", "value": "정보없음" if kpi["avg_fare"] is None else f"{kpi['avg_fare']:,.0f}원"},
    ])

st.divider()

# ---------------------------------------------------------------------
# 1) 지도 + 2) 자치구별 출발 이용 건수 (표/선택상자 병행 제공)
# ---------------------------------------------------------------------
st.subheader("🗺️ 자치구별 이용 현황")

map_df = svc.get_district_map_data(start_date, end_date)
if map_df.empty:
    st.info("선택하신 기간에 자치구별 데이터가 없습니다.", icon="📭")
else:
    map_col, table_col = st.columns([3, 2])
    with map_col:
        try:
            fig_map = px.scatter_map(
                map_df, lat="latitude", lon="longitude", size="request_count",
                color="request_count", hover_name="district_id",
                hover_data={"request_count": True, "ride_count": True, "latitude": False, "longitude": False},
                zoom=9.3, height=480, color_continuous_scale="Blues",
                title="자치구별 출발 접수 건수(원 크기·색이 진할수록 건수가 많음)",
            )
            fig_map.update_layout(map_style="open-street-map", margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_map, use_container_width=True)
        except Exception:
            st.warning("지도를 표시할 수 없어 막대차트로 대체합니다.", icon="⚠️")
            bar_df = map_df.sort_values("request_count", ascending=True)
            fig_bar_fallback = px.bar(
                bar_df, x="request_count", y="district_id", orientation="h",
                title="자치구별 출발 접수 건수", labels={"request_count": "접수 건수", "district_id": "자치구"},
            )
            st.plotly_chart(fig_bar_fallback, use_container_width=True)

    with table_col:
        st.markdown("**표로 보기 + 자치구 선택**")
        selected_district = st.selectbox(
            "상세정보를 볼 자치구를 선택하세요", sorted(map_df["district_id"].unique().tolist()),
        )
        st.dataframe(
            map_df[["district_id", "request_count", "ride_count", "cancel_count"]]
            .sort_values("request_count", ascending=False)
            .rename(columns={"district_id": "자치구", "request_count": "접수건수", "ride_count": "이용건수", "cancel_count": "취소건수"}),
            hide_index=True, use_container_width=True, height=300,
        )

    bar_df2 = map_df.sort_values("request_count", ascending=True)
    fig_bar = px.bar(
        bar_df2, x="request_count", y="district_id", orientation="h",
        title="자치구별 출발 이용 건수", labels={"request_count": "접수 건수", "district_id": "자치구"},
        height=520,
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    # -------------------------------------------------------------
    # 자치구 선택 상세정보
    # -------------------------------------------------------------
    st.markdown(f"### 📍 {selected_district} 상세정보")
    detail = svc.get_district_detail(selected_district, start_date, end_date)
    render_metric_cards([
        {"label": f"{selected_district} 출발 이용 건수", "value": f"{detail['origin_request_count']:,}건"},
        {"label": f"{selected_district} 도착 이용 건수", "value": f"{detail['destination_request_count']:,}건"},
        {"label": "평균 배차 대기시간", "value": "정보없음" if detail["avg_dispatch_wait_min"] is None else f"{detail['avg_dispatch_wait_min']:.1f}분"},
        {"label": "중앙값 배차 대기시간", "value": "정보없음" if detail["median_dispatch_wait_min"] is None else f"{detail['median_dispatch_wait_min']:.1f}분"},
    ])
    render_metric_cards([
        {"label": "평균 승차 대기시간", "value": "정보없음" if detail["avg_pickup_wait_min"] is None else f"{detail['avg_pickup_wait_min']:.1f}분"},
        {"label": "가장 혼잡한 요일", "value": detail["busiest_weekday_name"] or "정보없음"},
        {"label": "가장 혼잡한 시간", "value": "정보없음" if detail["busiest_hour"] is None else f"{detail['busiest_hour']}시"},
        {"label": "가장 많이 이동한 목적 자치구", "value": detail["top_destination_district"] or "정보없음"},
    ])
    render_metric_cards([
        {"label": "가장 많이 사용한 이용 목적", "value": detail["top_purpose"] or "정보없음"},
    ])

st.divider()

# ---------------------------------------------------------------------
# 3) 시간대별 접수 건수 + 4) 요일x시간대 히트맵
# ---------------------------------------------------------------------
st.subheader("⏰ 시간대별 이용 패턴")
hourly_df = svc.get_heatmap_data(origin_district)
if hourly_df.empty:
    st.info("시간대별 데이터가 없습니다.", icon="📭")
else:
    hour_agg = hourly_df.groupby("request_hour", as_index=False)["request_count"].sum()
    fig_hour = px.bar(
        hour_agg, x="request_hour", y="request_count",
        title="시간대별 접수 건수" + (f" ({origin_district})" if origin_district else " (서울 전체)"),
        labels={"request_hour": "시간(0~23시)", "request_count": "접수 건수"},
    )
    st.plotly_chart(fig_hour, use_container_width=True)

    pivot = hourly_df.pivot_table(index="weekday_num", columns="request_hour", values="request_count", aggfunc="sum", fill_value=0)
    pivot = pivot.reindex(index=range(7), fill_value=0).reindex(columns=range(24), fill_value=0)
    fig_heatmap = px.imshow(
        pivot.values, x=[f"{h}시" for h in pivot.columns], y=[WEEKDAY_NAMES_KO[i] for i in pivot.index],
        color_continuous_scale="Blues", aspect="auto",
        title="요일×시간대 이용량 히트맵" + (f" ({origin_district})" if origin_district else " (서울 전체)"),
        labels={"color": "접수 건수"},
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# 5) 월별 이용 건수 추이 + 6) 월별 평균 배차 대기시간 추이
# ---------------------------------------------------------------------
st.subheader("📈 월별 추이")
monthly_df = svc.get_monthly_trend()
if monthly_df.empty:
    st.info("월별 통계 데이터가 없습니다.", icon="📭")
else:
    fig_month_count = px.line(
        monthly_df, x="year_month", y=["request_count", "ride_count"], markers=True,
        title="월별 접수 건수 및 실제 이용 건수 추이",
        labels={"year_month": "연-월", "value": "건수", "variable": "구분"},
    )
    st.plotly_chart(fig_month_count, use_container_width=True)

    fig_month_wait = px.line(
        monthly_df, x="year_month", y="avg_dispatch_wait_min", markers=True,
        title="월별 평균 배차 대기시간 추이",
        labels={"year_month": "연-월", "avg_dispatch_wait_min": "평균 배차 대기시간(분)"},
    )
    st.plotly_chart(fig_month_wait, use_container_width=True)

st.divider()

# ---------------------------------------------------------------------
# 7) 주요 출발구 -> 목적구 이동 경로
# ---------------------------------------------------------------------
st.subheader("🚏 주요 이동 경로")
od_df = svc.get_od_flows(origin_district, destination_district, top_n=15)
if od_df.empty:
    st.info("선택하신 조건의 이동 경로 데이터가 없습니다.", icon="📭")
else:
    od_df = od_df.copy()
    od_df["route"] = od_df["origin_district_id"] + " → " + od_df["destination_district_id"]
    fig_od = px.bar(
        od_df.sort_values("ride_count"), x="ride_count", y="route", orientation="h",
        title="주요 출발구 → 목적구 이동 경로 (이용 건수 상위)",
        labels={"ride_count": "이용 건수", "route": "이동 경로"}, height=500,
    )
    st.plotly_chart(fig_od, use_container_width=True)
    st.dataframe(
        od_df[["route", "request_count", "ride_count", "avg_distance", "avg_fare"]]
        .rename(columns={"route": "이동 경로", "request_count": "접수건수", "ride_count": "이용건수", "avg_distance": "평균거리(km)", "avg_fare": "평균요금(원)"}),
        hide_index=True, use_container_width=True,
    )

st.divider()

# ---------------------------------------------------------------------
# 8) 이용 목적별 분포 + 9) 차량 구분별 이용 현황
# ---------------------------------------------------------------------
purpose_col, vehicle_col = st.columns(2)
with purpose_col:
    st.subheader("🎯 이용 목적별 분포")
    purpose_df = svc.get_purpose_distribution(origin_district)
    if purpose_group:
        purpose_df = purpose_df[purpose_df["purpose_group"] == purpose_group]
    if purpose_df.empty:
        st.info("이용 목적 데이터가 없습니다.", icon="📭")
    else:
        fig_purpose = px.pie(
            purpose_df, names="purpose_group", values="ride_count",
            title="이용 목적별 이용 건수 비중" + (f" ({origin_district})" if origin_district else ""),
        )
        st.plotly_chart(fig_purpose, use_container_width=True)

with vehicle_col:
    st.subheader("🚐 차량 구분별 이용 현황")
    vehicle_df = svc.get_vehicle_disability_distribution(vehicle_type)
    if vehicle_df.empty:
        st.info("차량 구분 데이터가 없습니다.", icon="📭")
    else:
        vehicle_summary = vehicle_df.groupby("vehicle_type", as_index=False)["ride_count"].sum()
        fig_vehicle = px.bar(
            vehicle_summary, x="vehicle_type", y="ride_count",
            title="차량 구분별 이용 건수", labels={"vehicle_type": "차량 구분", "ride_count": "이용 건수"},
        )
        st.plotly_chart(fig_vehicle, use_container_width=True)
