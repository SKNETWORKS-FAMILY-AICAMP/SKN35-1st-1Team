"""
import_csv_to_db.py
크롤링한 CSV를 disability_news 테이블에 삽입한다.
실행 전 반드시 TRUNCATE로 기존 데이터를 비울 것 (PK/UNIQUE 없어 재실행 시 중복됨).
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pymysql

from common.news_data import DB_CONFIG, TABLE_NAME


def import_csv(csv_path: str) -> None:
    path = Path(csv_path)
    if not path.exists():
        print(f"파일을 찾을 수 없습니다: {csv_path}")
        sys.exit(1)

    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    conn = pymysql.connect(**DB_CONFIG)
    inserted, failed = 0, 0
    try:
        with conn.cursor() as cur:
            for row in rows:
                try:
                    cur.execute(
                        f"""
                        INSERT INTO {TABLE_NAME}
                            (category, keyword, headline, body, press, url, crawled_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            row["category"],
                            row["keyword"],
                            row["headline"],
                            row["body"],
                            row["press"],
                            row["url"],
                            row["crawled_at"],
                        ),
                    )
                    inserted += 1
                except Exception as e:
                    failed += 1
                    print(f"삽입 실패 (url={row.get('url')}): {e}")
        conn.commit()
    finally:
        conn.close()

    print(f"완료 - 삽입 {inserted}건 / 실패 {failed}건 / 전체 {len(rows)}건")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python import_csv_to_db.py <csv경로>")
        sys.exit(1)
    import_csv(sys.argv[1])
