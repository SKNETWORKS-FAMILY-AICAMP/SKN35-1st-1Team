import streamlit as st
from views.useStatus import show_useStatus
from views.reserve import show_reserve

st.set_page_config(page_title="우리동네 장애인콜택시", layout="wide")


def load_css(file_path):
    with open(file_path, encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


load_css("style/style.css")  # 여기서 한 번만 불러오면 어느 페이지에서든 적용됨

if "page" not in st.session_state:
    st.session_state.page = "home"


def show_home():
    st.title("🚕 우리동네 장애인 콜택시")
    st.subheader("서울시 장애인콜택시 이용현황 분석 및 조회 시스템")
    st.write("")

    if st.button("이용현황", use_container_width=True, type="primary"):
        st.session_state.page = "useStatus"
        st.rerun()
    if st.button("예약하기", use_container_width=True, type="primary"):
        st.session_state.page = "reserve"
        st.rerun()


if st.session_state.page == "home":
    show_home()
elif st.session_state.page == "reserve":
    if st.button("⬅ 메인으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
    show_reserve()
else:
    if st.button("⬅ 메인으로 돌아가기"):
        st.session_state.page = "home"
        st.rerun()
    show_useStatus()