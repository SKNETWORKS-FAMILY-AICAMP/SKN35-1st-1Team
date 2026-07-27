"""
예약하기 페이지 (reserve.py)
"""

import datetime

import streamlit as st

from db.db import get_weekday_hour_stats


# ---------------------------------------------------------
# DB 데이터 조회
# ---------------------------------------------------------

@st.cache_data(ttl=3600, show_spinner=False)
def load_weekday_hour_stats(weekday_no):
    """
    같은 요일의 시간대별 이용 통계를 조회합니다.

    동일한 요일 데이터는 1시간 동안 캐시에 저장하여
    화면을 조작할 때마다 DB를 반복 조회하지 않도록 합니다.
    """

    return get_weekday_hour_stats(weekday_no)


def get_congestion_message(selected_date, selected_time):
    """
    선택한 날짜의 요일과 탑승 시간을 DB 통계와 비교합니다.

    반환값:
        안내 수준, 안내 문구, 추천 시간 목록
    """

    weekday_no = selected_date.weekday()
    selected_hour = selected_time.hour

    try:
        stats = load_weekday_hour_stats(weekday_no)

    except Exception as error:
        print(f"혼잡도 조회 오류: {error}")

        return (
            "info",
            "과거 이용 데이터를 불러오지 못했습니다. "
            "잠시 후 다시 확인해주세요.",
            [],
        )

    if not stats:
        return (
            "info",
            "선택한 요일의 과거 이용 데이터가 없습니다.",
            [],
        )

    selected_stat = next(
        (
            row
            for row in stats
            if int(row["request_hour"]) == selected_hour
        ),
        None,
    )

    if selected_stat is None:
        return (
            "info",
            "선택한 시간대의 과거 이용 데이터가 없습니다.",
            [],
        )

    # 같은 요일의 24시간 평균 이용 건수
    average_count = sum(
        int(row["request_count"])
        for row in stats
    ) / len(stats)

    selected_count = int(selected_stat["request_count"])

    if average_count > 0:
        congestion_ratio = selected_count / average_count
    else:
        congestion_ratio = 0

    weekday_name = selected_stat["weekday_name"]
    avg_wait = selected_stat["avg_wait_minutes"]

    if avg_wait is not None:
        wait_text = f" 평균 대기시간은 약 {float(avg_wait):.0f}분이었습니다."
    else:
        wait_text = ""

    # 선택 시간 전후 3시간 안에서 추천 시간 탐색
    nearby_stats = [
        row
        for row in stats
        if 6 <= int(row["request_hour"]) <= 22
        and int(row["request_hour"]) != selected_hour
        and abs(int(row["request_hour"]) - selected_hour) <= 3
    ]

    # 전후 3시간 안에 추천할 데이터가 부족할 경우
    # 오전 6시부터 오후 10시까지 전체 시간에서 탐색
    if len(nearby_stats) < 3:
        nearby_stats = [
            row
            for row in stats
            if 6 <= int(row["request_hour"]) <= 22
            and int(row["request_hour"]) != selected_hour
        ]

    # 이용 건수가 적고 평균 대기시간이 짧은 순서
    nearby_stats.sort(
        key=lambda row: (
            int(row["request_count"]),
            float(row["avg_wait_minutes"])
            if row["avg_wait_minutes"] is not None
            else float("inf"),
        )
    )

    recommended_hours = nearby_stats[:3]

    detail = (
        f"2023~2025년 {weekday_name}요일 {selected_hour}시의 "
        f"누적 이용 건수는 {selected_count:,}건입니다."
        f"{wait_text}"
    )

    if congestion_ratio <= 0.8:
        level = "success"
        message = (
            f"✅ 선택하신 {weekday_name}요일 {selected_hour}시는 "
            f"과거 데이터상 비교적 원활한 시간대입니다. {detail}"
        )

    elif congestion_ratio >= 1.2:
        level = "warning"
        message = (
            f"⚠️ 선택하신 {weekday_name}요일 {selected_hour}시는 "
            f"과거 데이터상 이용이 많은 시간대입니다. {detail}"
        )

    else:
        level = "info"
        message = (
            f"ℹ️ 선택하신 {weekday_name}요일 {selected_hour}시는 "
            f"과거 데이터상 평균적인 이용 시간대입니다. {detail}"
        )

    return level, message, recommended_hours


def show_congestion_message(level, message):
    """혼잡도에 맞는 색상의 안내 상자를 표시합니다."""

    if level == "success":
        st.success(message)

    elif level == "warning":
        st.warning(message)

    else:
        st.info(message)


def show_recommended_hours(recommended_hours):
    """DB 분석 결과를 바탕으로 추천 시간대를 표시합니다."""

    if not recommended_hours:
        return

    recommendation_texts = []

    for row in recommended_hours:
        hour = int(row["request_hour"])
        request_count = int(row["request_count"])
        avg_wait = row["avg_wait_minutes"]

        if avg_wait is not None:
            text = (
                f"**{hour:02d}:00** "
                f"· 이용 {request_count:,}건 "
                f"· 평균 대기 {float(avg_wait):.0f}분"
            )
        else:
            text = (
                f"**{hour:02d}:00** "
                f"· 이용 {request_count:,}건"
            )

        recommendation_texts.append(text)

    st.markdown("#### 비교적 원활한 추천 시간")

    for text in recommendation_texts:
        st.markdown(f"- {text}")


# ---------------------------------------------------------
# 입력폼 검증
# ---------------------------------------------------------

def validate_form(data):
    """필수 입력값과 연락처를 검사합니다."""

    errors = []

    if not data["depart"].strip():
        errors.append("출발지를 입력해주세요.")

    if not data["dest"].strip():
        errors.append("목적지를 입력해주세요.")

    phone_number = data["phone"].replace("-", "").replace(" ", "")

    if not phone_number:
        errors.append("연락처를 입력해주세요.")

    elif not phone_number.isdigit():
        errors.append(
            "연락처는 숫자와 하이픈만 입력해주세요. "
            "(예: 010-1234-5678)"
        )

    elif len(phone_number) not in (10, 11):
        errors.append("연락처를 10자리 또는 11자리로 입력해주세요.")

    selected_datetime = datetime.datetime.combine(
        data["date"],
        data["time"],
    )

    if selected_datetime < datetime.datetime.now():
        errors.append("희망 탑승일시는 현재 이후로 선택해주세요.")

    return errors


# ---------------------------------------------------------
# 예약정보 요약
# ---------------------------------------------------------

def generate_summary(data):
    """전화 및 문자 접수에 사용할 요약문을 생성합니다."""

    lines = [
        f"■ 출발지: {data['depart'] or '-'}",
        f"■ 목적지: {data['dest'] or '-'}",
        (
            f"■ 희망 탑승일시: "
            f"{data['date']:%Y-%m-%d} "
            f"{data['time']:%H:%M}"
        ),
        f"■ 연락처: {data['phone'] or '-'}",
        f"■ 휠체어 이용: {data['wheelchair']}",
        f"■ 탑승 인원: {data['passengers']}",
        f"■ 왕복 여부: {'예' if data['round_trip'] else '아니오'}",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------
# 예약하기 페이지
# ---------------------------------------------------------

def show_reserve():
    st.title("예약하기")

    st.markdown(
        "아래 체크리스트를 작성하면 전화·문자 접수 시 "
        "바로 활용할 수 있는 요약문을 만들어드려요."
    )

    st.caption(
        "이 페이지에서는 실제 예약이나 배차가 완료되지 않습니다. "
        "정보를 확인한 후 전화·문자·인터넷으로 접수해주세요."
    )

    col_form, col_side = st.columns([2, 1])

    # ---------------- 좌측 입력폼 ----------------
    with col_form:
        with st.container(border=True):

            c1, c2 = st.columns(2)

            with c1:
                depart = st.text_input(
                    "출발지 (Departure)",
                    value=st.session_state.get(
                        "prefill_depart",
                        "",
                    ),
                    placeholder="출발지를 입력하세요",
                )

            with c2:
                dest = st.text_input(
                    "목적지",
                    placeholder="목적지를 입력하세요",
                )

            c3, c4 = st.columns(2)

            with c3:
                date = st.date_input(
                    "희망 날짜",
                    value=datetime.date.today(),
                    min_value=datetime.date.today(),
                )

            with c4:
                time = st.time_input(
                    "탑승 시간",
                    value=datetime.time(9, 0),
                    step=datetime.timedelta(minutes=10),
                )

            phone = st.text_input(
                "연락처 (Contact Number)",
                placeholder="010-0000-0000",
                help="숫자와 하이픈을 입력할 수 있습니다.",
            )

            st.divider()

            st.markdown("**휠체어 이용 여부**")

            wheelchair = st.radio(
                "휠체어 이용 여부",
                ["예", "아니오"],
                horizontal=True,
                label_visibility="collapsed",
            )

            c5, c6 = st.columns(2)

            with c5:
                passengers = st.selectbox(
                    "탑승 인원",
                    ["1명", "2명", "3명", "4명"],
                )

            with c6:
                st.write("")
                st.write("")

                round_trip = st.checkbox("왕복 예약")

            submitted = st.button(
                "예약정보 요약하기",
                use_container_width=True,
                type="primary",
            )

    # ---------------- 우측 DB 안내 ----------------
    with col_side:
        with st.spinner("과거 이용 데이터를 분석하고 있습니다."):
            level, message, recommended_hours = (
                get_congestion_message(date, time)
            )

        show_congestion_message(level, message)
        show_recommended_hours(recommended_hours)

        st.caption(
            "2023~2025년 동일 요일·시간대의 이용 통계를 "
            "바탕으로 한 참고 정보이며 실제 배차시간을 보장하지 않습니다."
        )

        # ---------------- 예약정보 요약 ----------------
        if submitted:
            form_data = {
                "depart": depart,
                "dest": dest,
                "date": date,
                "time": time,
                "phone": phone,
                "wheelchair": wheelchair,
                "passengers": passengers,
                "round_trip": round_trip,
            }

            errors = validate_form(form_data)

            if errors:
                st.error(
                    "입력 내용을 확인해주세요.\n\n"
                    + "\n".join(
                        f"- {error}"
                        for error in errors
                    )
                )

            else:
                summary_text = generate_summary(form_data)

                st.divider()
                st.subheader("예약정보 요약")

                st.markdown(
                    "아래 내용을 복사해서 문자로 접수하거나, "
                    "전화로 그대로 말씀하시면 됩니다."
                )

                st.code(
                    summary_text,
                    language=None,
                )

                st.warning(
                    "아직 예약이 완료되지 않았습니다. "
                    "아래 공식 접수 방법 중 하나를 이용해주세요."
                )

                st.link_button(
                    "📞 콜센터로 전화하기",
                    "tel:15884388",
                    use_container_width=True,
                )

                st.link_button(
                    "💬 문자로 접수하기",
                    "sms:15884388",
                    use_container_width=True,
                )

                st.link_button(
                    "🌐 인터넷 접수 페이지로 이동",
                    "https://calltaxi.sisul.or.kr/member/login.asp",
                    use_container_width=True,
                )


if __name__ == "__main__":
    st.set_page_config(
        page_title="예약하기 - 우리동네 장애인콜택시",
        layout="wide",
    )

    show_reserve()