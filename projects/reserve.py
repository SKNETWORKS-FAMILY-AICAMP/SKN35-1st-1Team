"""
예약하기 페이지 (reserve.py)
"""

import datetime
import streamlit as st

# 현재 시간 기반으로 콜택시 이용 안내문구 노출
def get_congestion_message() -> tuple[str, bool]:
    """
        현재 시각 기준, 과거 데이터상 혼잡한 시간대인지 확인해서 안내문구 반환
        TODO: 실제 탑승내역 기반 시간대별 통계로 교체 (이용현황 페이지와 동일 로직 사용 ??)
        peak_hours -> 임시 기준, 실데이터 연동되면 상위 N개 시간대로 교체 필요 !!!
    """
    peak_hours = {7, 8, 9, 17, 18, 19}
    now_hour = datetime.datetime.now().hour

    if now_hour in peak_hours:
        return f"⚠️ 현재 {now_hour}시는 콜택시 이용이 많은 시간대입니다. 대기시간이 평소보다 길 수 있어요.", True
    return f"✅ 현재 {now_hour}시는 비교적 원활한 시간대입니다.", False

# 입력폼 검증
def validate_form(data: dict) -> list[str]:
    """필수 입력 체크 + 연락처 숫자 검증, 문제 있으면 에러 메시지 리스트 반환"""
    errors = []

    if not data["depart"]:
        errors.append("출발지를 입력해주세요.")
    if not data["dest"]:
        errors.append("목적지를 입력해주세요.")
    if not data["phone"]:
        errors.append("연락처를 입력해주세요.")
    elif not data["phone"].replace("-", "").isdigit():
        errors.append("연락처는 숫자만 입력해주세요. (예: 01012345678 또는 010-1234-5678)")

    return errors




# 입력 정보 요약형태로 변환
def generate_summary(data: dict) -> str:
    lines = [
        f"■ 출발지: {data['depart'] or '-'}",
        f"■ 목적지: {data['dest'] or '-'}",
        f"■ 희망 탑승일시: {data['date']} {data['time']}",
        f"■ 연락처: {data['phone'] or '-'}",
        f"■ 휠체어 이용: {data['wheelchair']}",
        f"■ 탑승 인원: {data['passengers']}",
        f"■ 왕복 여부: {'예' if data['round_trip'] else '아니오'}",
    ]
    return "\n".join(lines)

# 예약하기
def show_reserve():
    st.title("예약하기")
    st.markdown("아래 체크리스트를 작성하면 전화·문자 접수 시 바로 활용할 수 있는 요약문을 만들어드려요.")

    col_form, col_side = st.columns([2, 1])

    # ---------------- 좌측: 입력폼 ----------------
    with col_form:
        with st.container(border=True):

            c1, c2 = st.columns(2)
            with c1:
                depart = st.text_input(
                    "출발지 (Departure)",
                    value=st.session_state.get("prefill_depart", ""), # 이용현황에서 선택한 "구"의 값을 가지고 와서 자동 입력해줌
                    placeholder="출발지를 입력하세요",
                )
            with c2:
                dest = st.text_input("목적지", placeholder="목적지를 입력하세요")

            c3, c4 = st.columns(2)
            with c3:
                date = st.date_input("희망 날짜", value=datetime.date.today())
            with c4:
                time = st.time_input("탑승 시간", value=datetime.time(9, 0))

            phone = st.text_input(
                "연락처 (Contact Number)",
                placeholder="010-0000-0000",
                help="숫자만 입력해주세요 (하이픈은 있어도, 없어도 됩니다)",
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
                passengers = st.selectbox("탑승 인원", ["1명", "2명", "3명", "4명"])
            with c6:
                st.write("")
                st.write("")
                round_trip = st.checkbox("왕복 예약")

            submitted = st.button("예약정보 요약하기", use_container_width=True, type="primary")

    # ---------------- 우측: 상태 안내 + 예약정보 요약 ----------------
    with col_side:
        message, is_peak = get_congestion_message()
        if is_peak:
            st.warning(message)
        else:
            st.success(message)

        if submitted:
            # 폼 입력 검증
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
                st.error("정보를 모두 입력해주세요.\n\n" + "\n".join(f"- {e}" for e in errors))
            else:
                summary_text = generate_summary(form_data)
                st.divider()
                st.subheader("**예약정보 요약**")
                st.markdown("아래 내용을 복사해서 문자 접수하시거나, 전화로 그대로 말씀하시면 됩니다.")
                st.code(summary_text, language=None)

                st.link_button("📞 콜센터로 전화하기", "tel:15884388", use_container_width=True)
                st.link_button("💬 문자로 접수하기", "sms:15884388", use_container_width=True)
                st.link_button("🌐 인터넷 접수 페이지로 이동", "https://www.sisul.or.kr/open_content/calltaxi/", use_container_width=True)


if __name__ == "__main__":
    st.set_page_config(page_title="예약하기 - 우리동네 장애인콜택시", layout="wide")
    show_reserve()