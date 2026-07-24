"""원본 장애인콜택시 CSV를 정제하여 Parquet으로 저장하는 전처리 스크립트.

사용 예:
    uv run python preprocessing/clean_taxi_data.py --input data/sample/dummy_taxi_raw.csv

원본 CSV는 절대 수정하지 않는다(입력 경로와 출력 경로를 분리).
"""
from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from preprocessing.config import CHUNK_SIZE, PROCESSED_DIR, REJECTED_DIR
from preprocessing.transforms import run_all_transforms
from preprocessing.validate_data import save_quality_report, save_rejected_rows, save_unmapped_areas

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def load_raw_csv(input_path: str) -> pd.DataFrame:
    """chunksize를 사용해 원본 CSV를 읽는다. 대용량 파일에서도 메모리 사용량을 제한한다."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"원본 CSV 파일을 찾을 수 없습니다: {input_path}")

    chunks = []
    for chunk in pd.read_csv(path, chunksize=CHUNK_SIZE, encoding="utf-8-sig", low_memory=False):
        chunks.append(chunk)
    if not chunks:
        return pd.DataFrame()
    return pd.concat(chunks, ignore_index=True)


def process(input_path: str, processed_dir: str = PROCESSED_DIR, rejected_dir: str = REJECTED_DIR) -> pd.DataFrame:
    logger.info("원본 CSV 로드 시작: %s", input_path)
    raw_df = load_raw_csv(input_path)
    logger.info("원본 로드 완료: %d행", len(raw_df))

    df = run_all_transforms(raw_df)

    processed_path = Path(processed_dir)
    processed_path.mkdir(parents=True, exist_ok=True)
    parquet_path = processed_path / "taxi_processed.parquet"
    df.to_parquet(parquet_path, index=False)
    logger.info("정제 데이터 저장 완료: %s (%d행)", parquet_path, len(df))

    save_unmapped_areas(df, rejected_dir)
    save_rejected_rows(df, rejected_dir)

    from preprocessing.validate_data import build_quality_summary
    summary = build_quality_summary(df)
    run_at = datetime.now().isoformat(timespec="seconds")
    save_quality_report(summary, processed_dir, run_at)
    logger.info("데이터 품질 보고서 저장 완료: %s", summary)

    return df


def main() -> None:
    parser = argparse.ArgumentParser(description="장애인콜택시 원본 CSV 전처리")
    parser.add_argument("--input", type=str, required=True, help="원본 CSV 경로 (예: data/raw/xxx.csv 또는 data/sample/dummy_taxi_raw.csv)")
    parser.add_argument("--processed-dir", type=str, default=PROCESSED_DIR)
    parser.add_argument("--rejected-dir", type=str, default=REJECTED_DIR)
    args = parser.parse_args()

    try:
        process(args.input, args.processed_dir, args.rejected_dir)
    except FileNotFoundError as e:
        logger.error("전처리 중단: %s", e)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
