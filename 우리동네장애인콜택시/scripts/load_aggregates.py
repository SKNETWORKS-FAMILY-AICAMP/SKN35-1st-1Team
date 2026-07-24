"""data/processed/aggregates/*.parquet 를 MySQL 집계 테이블로 적재한다.

- 테이블별로 하나의 트랜잭션으로 처리하며, 실패 시 해당 테이블은 롤백된다(중복 적재 방지).
- UNIQUE KEY 기준 INSERT ... ON DUPLICATE KEY UPDATE 로 재실행해도 안전하다(idempotent).
- DataFrame에 실제 테이블에 없는 컬럼이 있으면 자동으로 무시한다(스키마 불일치에도 죽지 않음).

사용 예:
    uv run python scripts/load_aggregates.py
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from preprocessing.config import PROCESSED_DIR
from services.database import create_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

TABLE_NAMES = [
    "district_daily_stat",
    "district_hourly_stat",
    "weekday_hour_stat",
    "monthly_stat",
    "od_flow_stat",
    "purpose_stat",
    "disability_vehicle_stat",
]


def _build_upsert_sql(table: str, columns: list[str]) -> str:
    cols = ", ".join(columns)
    placeholders = ", ".join(f":{c}" for c in columns)
    update_clause = ", ".join(f"{c} = VALUES({c})" for c in columns)
    return f"INSERT INTO {table} ({cols}) VALUES ({placeholders}) ON DUPLICATE KEY UPDATE {update_clause}"


def load_table(engine, table_name: str, df: pd.DataFrame) -> int:
    if df.empty:
        logger.warning("%s: 적재할 집계 데이터가 없어 건너뜁니다.", table_name)
        return 0

    db_columns = {c["name"] for c in inspect(engine).get_columns(table_name)}
    usable_columns = [c for c in df.columns if c in db_columns and c != "id"]
    if not usable_columns:
        logger.warning("%s: DataFrame 컬럼과 일치하는 DB 컬럼이 없어 건너뜁니다.", table_name)
        return 0

    records = df[usable_columns].astype(object).where(pd.notna(df[usable_columns]), None).to_dict("records")
    upsert_sql = _build_upsert_sql(table_name, usable_columns)

    with engine.connect() as conn:
        with conn.begin():
            conn.execute(text(upsert_sql), records)
    return len(records)


def log_collection(engine, job_name: str, status: str, message: str, count: int, started_at: datetime) -> None:
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(
                    text(
                        """
                        INSERT INTO data_collection_log (job_name, status, message, collected_count, started_at, finished_at)
                        VALUES (:job_name, :status, :message, :count, :started_at, :finished_at)
                        """
                    ),
                    {
                        "job_name": job_name, "status": status, "message": message[:500],
                        "count": count, "started_at": started_at, "finished_at": datetime.now(),
                    },
                )
    except SQLAlchemyError:
        logger.exception("data_collection_log 기록 실패(무시하고 계속 진행)")


def main() -> None:
    started_at = datetime.now()
    aggregates_dir = Path(PROCESSED_DIR) / "aggregates"

    try:
        engine = create_db_engine()
    except SQLAlchemyError as e:
        logger.error("DB에 연결할 수 없어 집계 적재를 중단합니다: %s", type(e).__name__)
        raise SystemExit(1) from e

    total_loaded = 0
    failed_tables = []
    for table_name in TABLE_NAMES:
        parquet_path = aggregates_dir / f"{table_name}.parquet"
        if not parquet_path.exists():
            logger.warning("집계 파일이 없습니다(먼저 build_aggregates.py 실행 필요): %s", parquet_path)
            continue
        try:
            df = pd.read_parquet(parquet_path)
            loaded = load_table(engine, table_name, df)
            logger.info("%s: %d행 적재 완료", table_name, loaded)
            total_loaded += loaded
        except SQLAlchemyError as e:
            logger.error("%s 적재 실패, 롤백됨: %s", table_name, type(e).__name__)
            failed_tables.append(table_name)

    status = "success" if not failed_tables else ("partial" if total_loaded else "failed")
    message = "정상 적재" if not failed_tables else f"실패한 테이블: {failed_tables}"
    log_collection(engine, "aggregate_load", status, message, total_loaded, started_at)
    logger.info("집계 적재 완료. 총 %d행, 실패 테이블: %s", total_loaded, failed_tables or "없음")


if __name__ == "__main__":
    main()
