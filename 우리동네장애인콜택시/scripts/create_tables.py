"""MySQL 테이블 생성 스크립트.

sql/schema.sql 은 전부 CREATE TABLE IF NOT EXISTS 로 작성되어 있어
기존 테이블을 DROP하지 않는다. 실행 전 기존 테이블 목록을 먼저 출력해서
어떤 테이블이 이미 있는지 확인할 수 있게 한다.

사용 예:
    uv run python scripts/create_tables.py
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import inspect, text
from sqlalchemy.exc import SQLAlchemyError

from districts import DISTRICT_CENTROIDS, SEOUL_DISTRICTS
from services.database import create_db_engine

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
SCHEMA_SQL = ROOT / "sql" / "schema.sql"
INDEXES_SQL = ROOT / "sql" / "indexes.sql"


def _split_statements(sql_text: str) -> list[str]:
    statements = []
    for raw in sql_text.split(";"):
        stmt = raw.strip()
        if not stmt or stmt.startswith("--"):
            continue
        # 순수 주석 블록만 있는 조각은 건너뛴다.
        lines = [ln for ln in stmt.splitlines() if not ln.strip().startswith("--")]
        cleaned = "\n".join(lines).strip()
        if cleaned:
            statements.append(cleaned)
    return statements


def seed_area_table(conn) -> None:
    for district in SEOUL_DISTRICTS:
        lat, lon = DISTRICT_CENTROIDS[district]
        conn.execute(
            text(
                """
                INSERT INTO area (district_id, district_name, sido, latitude, longitude)
                VALUES (:district_id, :district_name, '서울특별시', :lat, :lon)
                ON DUPLICATE KEY UPDATE district_name = VALUES(district_name),
                    latitude = VALUES(latitude), longitude = VALUES(longitude)
                """
            ),
            {"district_id": district, "district_name": district, "lat": lat, "lon": lon},
        )


def main() -> None:
    try:
        engine = create_db_engine()
        with engine.connect() as conn:
            existing_tables = inspect(engine).get_table_names()
            logger.info("기존 테이블(%d개): %s", len(existing_tables), existing_tables)

            schema_sql = SCHEMA_SQL.read_text(encoding="utf-8")
            with conn.begin():
                for stmt in _split_statements(schema_sql):
                    conn.execute(text(stmt))
                seed_area_table(conn)
            logger.info("스키마 생성 및 area 테이블 시드 완료")

            if INDEXES_SQL.exists():
                for stmt in _split_statements(INDEXES_SQL.read_text(encoding="utf-8")):
                    try:
                        with conn.begin():
                            conn.execute(text(stmt))
                    except SQLAlchemyError as e:
                        # 이미 존재하는 인덱스 등은 무시하고 계속 진행한다.
                        logger.warning("인덱스 구문 건너뜀(%s): %s", type(e).__name__, stmt[:80])

            final_tables = inspect(engine).get_table_names()
            logger.info("최종 테이블(%d개): %s", len(final_tables), final_tables)
    except SQLAlchemyError as e:
        logger.error("DB에 연결할 수 없습니다. .env의 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME을 확인하세요. (%s)", type(e).__name__)
        raise SystemExit(1) from e


if __name__ == "__main__":
    main()
