"""장애인콜택시 예약 준비 도우미.

중요(개인정보 처리 원칙): 연락처, 출발/목적 상세 위치는 어떤 형태로도
DB/CSV/파일/로그/캐시에 저장하지 않는다. 이 페이지 내에서 요약 문장을
만드는 용도로만, 현재 세션 메모리에서만 사용한다.
"""
from __future__ import annotations

import datetime

import streamlit as st

from components.accessibility import apply_accessibility_css
from components.disclaimer import render_service_disclaimer
from components.header import render_page_header
from components.navigation import render_home_link
from config import OFFICIAL
from districts import SEOUL_DISTRICTS
from services import congestion_service as congestion_svc

st.set_page_config(page_title="예약하기 | 우리동네 장애인 콜택시", page_icon="📝", layout="wide")
apply_accessibility_css()
render_home_link()
render_page_header("장애인콜택시 예약 준비 도우미", "실제 예약을 접수하지 않습니다. 예약에 필요한 내용을 미리 정리해 드립니다.")
render_service_disclaimer()

PURPOSE_CHOICES = ["의료", "복지시설", "교육", "직장", "공공업무", "여가", "기타"]


def _format_time_kr(t: datetime.time) -> str:
    period = "오전" if t.hour < 12 else "오후"
    hour_12 = t.hour % 12
    hour_12 = 12 if hour_12 == 0 else hour_12
    if t.minute == 0:
        return f"{period} {hour_12}시"
    return f"{period} {hour_12}시 {t.minute}분"


def _format_date_kr(d: datetime.date) -> str:
    return f"{d.year}년 {d.month}월 {d.day}일"


st.subheader("① 예약 정보 입력")
with st.form("reservation_form", clear_on_submit=False):
    col1, col2 = st.columns(2)
    with col1:
        origin_district = st.selectbox("출발 자치구 *", SEOUL_DISTRICTS, key="origin_district")
        origin_detail = st.text_input("출발 상세 위치 (예: ○○병원, ○○아파트)", key="origin_detail")
    with col2:
        destination_district = st.selectbox("목적 자치구 *", SEOUL_DISTRICTS, index=1, key="destination_district")
        destination_detail = st.text_input("목적 상세 위치", key="destination_detail")

    col3, col4 = st.columns(2)
    with col3:
        ride_date = st.date_input("희망 탑승 날짜 *", value=datetime.date.today(), key="ride_date")
    with col4:
        ride_time = st.time_input("희망 탑승 시간 *", value=datetime.time(9, 0), key="ride_time")

    col5, col6, col7 = st.columns(3)
    with col5:
        use_wheelchair = st.radio("휠체어 사용 여부 *", ["사용", "미사용"], horizontal=True, key="use_wheelchair")
    with col6:
        max_companions = 3 if use_wheelchair == "사용" else 2
        companion_count = st.number_input(
            "동승자 수", min_value=0, max_value=max_companions, value=0, step=1, key="companion_count",
            help=f"공식 기준상 {'휠체어 이용 시 고객 외 최대 3명' if use_wheelchair == '사용' else '휠체어 미이용 시 고객 외 최대 2명'}까지 동승 가능합니다.",
        )
    with col7:
        trip_type = st.radio("편도 / 왕복 *", ["편도", "왕복"], horizontal=True, key="trip_type")

    purpose = st.selectbox("이용 목적 *", PURPOSE_CHOICES, key="purpose")
    contact = st.text_input("연락처 *", placeholder="010-0000-0000", key="contact")

    submitted = st.form_submit_button("예약 준비 정보 생성", use_container_width=True)

if not submitted:
    st.info("항목을 입력하고 '예약 준비 정보 생성' 버튼을 눌러주세요.", icon="📝")
    st.stop()

if not contact.strip():
    st.warning("연락처를 입력해 주세요.", icon="⚠️")
    st.stop()

st.divider()

# ---------------------------------------------------------------------
# 1) 예약정보 요약 (개인정보는 이 세션 화면 표시 용도로만 사용, 어디에도 저장하지 않음)
# ---------------------------------------------------------------------
st.subheader("② 예약정보 요약")
summary_col1, summary_col2 = st.columns(2)
with summary_col1:
    st.markdown(
        f"- **출발지**: {origin_district} {origin_detail or '(상세 위치 미입력)'}\n"
        f"- **목적지**: {destination_district} {destination_detail or '(상세 위치 미입력)'}\n"
        f"- **희망 탑승 날짜**: {_format_date_kr(ride_date)}\n"
        f"- **희망 탑승 시간**: {_format_time_kr(ride_time)}\n"
    )
with summary_col2:
    st.markdown(
        f"- **휠체어 사용 여부**: {use_wheelchair}\n"
        f"- **동승자 수**: {companion_count}명\n"
        f"- **편도/왕복**: {trip_type}\n"
        f"- **이용 목적**: {purpose}\n"
        f"- **연락처**: {contact}\n"
    )

# ---------------------------------------------------------------------
# 2) 문자 접수용 문장
# ---------------------------------------------------------------------
st.subheader("③ 문자 접수용 문장 (복사해서 사용하세요)")
wheelchair_phrase = "휠체어를 사용하며" if use_wheelchair == "사용" else "휠체어를 사용하지 않으며"
sms_text = (
    f"출발지는 {origin_district} {origin_detail or ''}이며 목적지는 {destination_district} {destination_detail or ''}입니다. "
    f"희망 탑승시간은 {_format_date_kr(ride_date)} {_format_time_kr(ride_time)}이고 {wheelchair_phrase} "
    f"동승자는 {companion_count}명입니다. 이용 목적은 {purpose}이며 {trip_type} 이용입니다. 연락처는 {contact}입니다."
)
st.text_area("아래 내용을 길게 눌러 전체 선택 후 복사하세요", value=sms_text, height=120, key="sms_text_area")

st.divider()

# ---------------------------------------------------------------------
# 3) 과거 데이터 기반 안내 (개인정보 없이 자치구/요일/시간만 사용, 결과는 캐시 가능한 공개 통계)
# ---------------------------------------------------------------------
st.subheader("④ 과거 데이터 기반 참고 안내")
st.caption(
    "아래 안내는 실제 배차/대기시간을 예측하거나 보장하지 않습니다. "
    "과거 통계를 바탕으로 한 참고 정보이며, 실제 대기시간은 당일 차량 운영 상황에 따라 달라질 수 있습니다."
)

weekday_num = ride_date.weekday()
info = congestion_svc.get_congestion_info(origin_district, weekday_num, ride_time.hour)

if info["tier"] == "no_data" or not info["request_count"]:
    st.info("해당 조건의 과거 통계가 아직 충분하지 않습니다.", icon="📭")
else:
    badge_col, detail_col = st.columns([1, 2])
    with badge_col:
        st.markdown(f"## {info['congestion_icon']} {info['congestion_level']}")
        st.caption(f"산정 기준: {info['tier_label']}")
    with detail_col:
        st.markdown(f"**{info['guidance_text']}**")
        wait_text = "정보없음" if info["avg_dispatch_wait_min"] is None else f"{info['avg_dispatch_wait_min']:.0f}분"
        median_text = "정보없음" if info["median_dispatch_wait_min"] is None else f"{info['median_dispatch_wait_min']:.0f}분"
        st.markdown(
            f"- 과거 동일 조건 접수 건수: **{info['request_count']:,}건**\n"
            f"- 과거 평균 배차 대기시간: **{wait_text}**\n"
            f"- 과거 중앙값 배차 대기시간: **{median_text}**"
        )

st.divider()

# ---------------------------------------------------------------------
# 하단: 공식 채널 안내
# ---------------------------------------------------------------------
st.subheader("📞 공식 예약 채널 안내")
st.markdown(
    "본 도우미는 실제 접수를 처리하지 않습니다. 아래 공식 채널을 통해 실제 예약을 진행해 주세요."
)
contact_col1, contact_col2, contact_col3 = st.columns(3)
with contact_col1:
    st.markdown(f"**☎️ 공식 전화번호**\n\n{OFFICIAL.phone_number}")
    st.link_button("전화 걸기", f"tel:{OFFICIAL.phone_number}", use_container_width=True)
with contact_col2:
    st.markdown(f"**💬 문자 접수**\n\n{OFFICIAL.sms_number}")
    st.caption("위 ③ 문자 접수용 문장을 복사해 보내주세요.")
with contact_col3:
    st.markdown("**🌐 공식 예약 페이지 / 앱**")
    st.link_button("공식 홈페이지에서 접수", OFFICIAL.reservation_url, use_container_width=True)
    st.caption("모바일 앱 스토어에서 '장애인콜택시'를 검색해 앱으로도 접수할 수 있습니다.")
