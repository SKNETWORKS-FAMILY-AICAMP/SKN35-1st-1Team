"""데이터 품질 보고서 생성 및 이상치/미매핑 데이터 별도 저장."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_quality_summary(df: pd.DataFrame) -> dict:
    """전처리 결과 DataFrame으로부터 데이터 품질 지표를 계산한다."""
    total_rows = len(df)
    valid_rows = int(df["is_valid_row"].sum()) if total_rows else 0
    negative_time_rows = int(
        (
            df["is_negative_dispatch_wait"]
            | df["is_negative_pickup_wait"]
            | df["is_negative_boarding_delay"]
            | df["is_negative_trip_duration"]
        ).sum()
    ) if total_rows else 0
    abnormal_wait_rows = int(
        (df["is_wait_over_24h"] | df["is_trip_duration_over_24h"]).sum()
    ) if total_rows else 0

    status_counts = df["status"].value_counts().to_dict() if total_rows else {}

    return {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "date_parse_fail_rows": int(df["is_date_parse_fail"].sum()) if total_rows else 0,
        "district_mapping_fail_rows": int(
            (df["is_origin_mapping_fail"] | df["is_destination_mapping_fail"]).sum()
        ) if total_rows else 0,
        "negative_time_rows": negative_time_rows,
        "abnormal_wait_rows": abnormal_wait_rows,
        "duplicate_rows": int(df["is_duplicate"].sum()) if total_rows else 0,
        "request_count": total_rows,
        "dispatch_count": int(status_counts.get("dispatched", 0) + status_counts.get("boarded", 0) + status_counts.get("completed", 0)),
        "ride_count": int(status_counts.get("boarded", 0) + status_counts.get("completed", 0)),
        "completed_count": int(status_counts.get("completed", 0)),
        "cancel_count": int(status_counts.get("cancelled", 0)),
    }


def save_quality_report(summary: dict, out_dir: str, run_at_str: str) -> tuple[Path, Path]:
    """data_quality_summary.csv 와 processing_summary.json 을 저장한다."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    csv_path = out_path / "data_quality_summary.csv"
    row = {"run_at": run_at_str, **summary}
    pd.DataFrame([row]).to_csv(csv_path, index=False, encoding="utf-8-sig")

    json_path = out_path / "processing_summary.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump({"run_at": run_at_str, **summary}, f, ensure_ascii=False, indent=2)

    return csv_path, json_path


def save_unmapped_areas(df: pd.DataFrame, out_dir: str) -> tuple[Path, Path]:
    """자치구 표준명으로 매핑되지 않은 원본값을 별도 CSV로 저장한다(강제 매핑 금지 원칙)."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    origin_path = out_path / "unmapped_origin_area.csv"
    dest_path = out_path / "unmapped_destination_area.csv"

    unmapped_origin = df.loc[df["is_origin_mapping_fail"], ["origin_district_raw"]].value_counts().reset_index(name="count")
    unmapped_dest = df.loc[df["is_destination_mapping_fail"], ["destination_district_raw"]].value_counts().reset_index(name="count")

    unmapped_origin.to_csv(origin_path, index=False, encoding="utf-8-sig")
    unmapped_dest.to_csv(dest_path, index=False, encoding="utf-8-sig")
    return origin_path, dest_path


def save_rejected_rows(df: pd.DataFrame, out_dir: str) -> Path:
    """is_valid_row가 False인(이상치로 플래그된) 행을 rejected 폴더에 별도 보존한다. 원본 행은 삭제하지 않는다."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    rejected_path = out_path / "rejected_rows.csv"
    rejected = df.loc[~df["is_valid_row"]]
    rejected.to_csv(rejected_path, index=False, encoding="utf-8-sig")
    return rejected_path
