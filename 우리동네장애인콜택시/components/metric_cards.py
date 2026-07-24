"""KPI 카드 그리드. st.columns는 좁은(모바일) 화면에서 자동으로 세로로 쌓여
버튼/카드가 잘리지 않는다."""
from __future__ import annotations

import streamlit as st


def render_metric_cards(metrics: list[dict], columns_per_row: int = 4) -> None:
    """metrics: [{"label": str, "value": str, "help": str | None}, ...]"""
    for start in range(0, len(metrics), columns_per_row):
        row = metrics[start:start + columns_per_row]
        cols = st.columns(len(row))
        for col, item in zip(cols, row):
            with col:
                st.metric(label=item["label"], value=item["value"], help=item.get("help"))
