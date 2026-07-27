"""필수산출물 ② 수집 데이터 — 크롤링으로 확보할 원본 데이터의 형태."""

from __future__ import annotations

import streamlit as st

import sample_data


def render() -> None:
    """수집 데이터 화면 — 원본 데이터 형태와 출처를 탭으로 보여준다."""
    st.header("📁 수집 데이터 (원본)")
    st.caption("필수 산출물 ② · BeautifulSoup/Selenium으로 수집 예정인 원본 형태 예시입니다.")

    sources = {
        "🚕 콜택시 이용현황": (
            sample_data.make_taxi_usage(), "서울시설공단 / 서울 열린데이터광장 (예시)"),
        "🦽 자동차 보조기구": (
            sample_data.make_devices(), "보조기구 제조사·복지몰 상세페이지 (예시)"),
        "🏛 지원정책": (
            sample_data.make_policies(), "각 기관 복지정책 안내 페이지 (예시)"),
    }

    tabs = st.tabs(list(sources.keys()))
    for tab, (label, (df, source)) in zip(tabs, sources.items()):
        with tab:
            c1, c2 = st.columns(2)
            c1.metric("수집 행 수", f"{len(df):,} 행")
            c2.metric("컬럼 수", f"{df.shape[1]} 개")
            st.markdown(f"**데이터 출처:** {source}")
            st.dataframe(df.head(50), use_container_width=True, hide_index=True)
            st.download_button(
                "⬇ CSV 다운로드",
                df.to_csv(index=False).encode("utf-8-sig"),
                file_name=f"{label}.csv",
                mime="text/csv",
                use_container_width=False,
            )
