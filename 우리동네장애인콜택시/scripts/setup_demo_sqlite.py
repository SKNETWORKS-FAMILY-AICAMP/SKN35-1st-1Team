"""[로컬 데모 전용] MySQL 없이 화면을 빠르게 확인하기 위해 SQLite 파일에
area + 집계 7종 + FAQ를 적재한다. 운영 배포에는 사용하지 않는다.

실제 MySQL이 준비되면 scripts/create_tables.py + scripts/load_aggregates.py +
collectors/collect_faq.py 를 사용하고, .env의 DB_DRIVER를 mysql로 되돌린다.

사용 예:
    uv run python preprocessing/clean_taxi_data.py --input data/sample/dummy_taxi_raw.csv
    uv run python preprocessing/build_aggregates.py
    uv run python scripts/setup_demo_sqlite.py
"""
from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
from sqlalchemy import create_engine

from collectors.collect_faq import FALLBACK_ANSWERS, FAQ_SOURCES
from config import DB
from districts import DISTRICT_CENTROIDS, SEOUL_DISTRICTS
from preprocessing.config import PROCESSED_DIR

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

AGGREGATE_TABLES = [
    "district_daily_stat", "district_hourly_stat", "weekday_hour_stat",
    "monthly_stat", "od_flow_stat", "purpose_stat", "disability_vehicle_stat",
]

NEWS_COLUMNS = [
    "news_id", "title", "description", "publisher", "published_at", "original_url",
    "naver_url", "search_keyword", "collected_at", "title_hash", "is_active",
]


def build_engine():
    return create_engine(f"sqlite:///{DB.sqlite_path}")


def seed_area(engine) -> None:
    df = pd.DataFrame([
        {"district_id": d, "district_name": d, "sido": "서울특별시",
         "latitude": DISTRICT_CENTROIDS[d][0], "longitude": DISTRICT_CENTROIDS[d][1]}
        for d in SEOUL_DISTRICTS
    ])
    df.to_sql("area", engine, if_exists="replace", index=False)
    logger.info("area 시드 완료(%d개 자치구)", len(df))


def load_aggregates(engine) -> None:
    aggregates_dir = Path(PROCESSED_DIR) / "aggregates"
    for table in AGGREGATE_TABLES:
        path = aggregates_dir / f"{table}.parquet"
        if not path.exists():
            logger.warning("%s: 집계 파일이 없어 건너뜁니다(%s). 먼저 build_aggregates.py 실행 필요", table, path)
            continue
        df = pd.read_parquet(path)
        df.to_sql(table, engine, if_exists="replace", index=False)
        logger.info("%s 적재 완료(%d행)", table, len(df))


def seed_faq(engine) -> None:
    now = datetime.now()
    rows = []
    for faq_id, (category, question, url) in enumerate(FAQ_SOURCES, start=1):
        answer = FALLBACK_ANSWERS.get(category)
        if not answer:
            continue
        rows.append({
            "faq_id": faq_id, "category": category, "question": question, "answer": answer,
            "source_url": url, "source_name": "서울시설공단 장애인콜택시",
            "collected_at": now, "updated_at": now, "display_order": faq_id, "is_active": 1,
        })
    pd.DataFrame(rows).to_sql("faq", engine, if_exists="replace", index=False)
    logger.info("faq 시드 완료(%d건)", len(rows))


def seed_empty_news(engine) -> None:
    pd.DataFrame(columns=NEWS_COLUMNS).to_sql("news", engine, if_exists="replace", index=False)
    logger.info("news 테이블 생성 완료(0건, 네이버 API 키 등록 후 collect_news.py로 수집)")


def main() -> None:
    if DB.driver != "sqlite":
        logger.warning(".env의 DB_DRIVER가 'sqlite'가 아닙니다. 그래도 %s 파일로 데모 DB를 만듭니다. "
                       "Streamlit이 이 데이터를 읽게 하려면 .env에 DB_DRIVER=sqlite 를 설정하세요.", DB.sqlite_path)
    engine = build_engine()
    seed_area(engine)
    load_aggregates(engine)
    seed_faq(engine)
    seed_empty_news(engine)
    logger.info("데모 SQLite DB 준비 완료: %s", DB.sqlite_path)


if __name__ == "__main__":
    main()
