"""
MySQL 적재기 (PyMySQL)
----------------------
정제 CSV(data/processed/*.csv)를 MySQL seoul_calltaxi 스키마에 적재한다.

수행 순서
  1) 스키마 생성      : db/schema.sql 실행 (DB·테이블·카테고리 기준값)
  2) faq_source 적재  : 출처 마스터 (source_code 기준 UPSERT)
  3) faq 적재         : content_hash 기준 UPSERT — 재실행해도 중복되지 않음
  4) faq_keyword 적재 : FAQ별 키워드 (faq_id + keyword 기준 UPSERT)
  5) crawl_log 기록   : 실행 결과 이력 저장

실행 : python db/loader.py
전제 : 프로젝트 루트에 .env 파일이 있고 MySQL 접속 정보가 채워져 있어야 한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pymysql

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402

SCHEMA_PATH = config.DB_DIR / "schema.sql"


# --------------------------------------------------------------------------- #
# 접속
# --------------------------------------------------------------------------- #
def connect(with_database: bool = True) -> pymysql.connections.Connection:
    """MySQL 커넥션을 생성한다. with_database=False면 DB 미지정으로 접속."""
    cfg = config.get_db_config()
    if not with_database:
        cfg.pop("database", None)
    return pymysql.connect(**cfg, autocommit=False,
                           cursorclass=pymysql.cursors.DictCursor)


def check_connection() -> tuple[bool, str]:
    """접속 가능 여부를 (성공여부, 메시지)로 반환한다."""
    try:
        conn = connect(with_database=False)
        with conn.cursor() as cur:
            cur.execute("SELECT VERSION() AS v")
            version = cur.fetchone()["v"]
        conn.close()
        return True, f"MySQL {version} 접속 성공"
    except Exception as exc:                    # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


# --------------------------------------------------------------------------- #
# 1) 스키마 생성
# --------------------------------------------------------------------------- #
def split_statements(sql_text: str) -> list[str]:
    """주석을 제거하고 세미콜론 기준으로 SQL 문을 분리한다."""
    lines = [ln for ln in sql_text.splitlines() if not ln.strip().startswith("--")]
    body = "\n".join(lines)
    return [s.strip() for s in body.split(";") if s.strip()]


def create_schema() -> None:
    """schema.sql을 실행해 DB와 테이블을 새로 만든다."""
    print("[1/5] 스키마 생성 (db/schema.sql)")
    sql_text = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = connect(with_database=False)
    try:
        with conn.cursor() as cur:
            for stmt in split_statements(sql_text):
                cur.execute(stmt)
        conn.commit()
        print("      → DB·테이블 5종 및 카테고리 기준값 생성 완료")
    finally:
        conn.close()


# --------------------------------------------------------------------------- #
# 2~4) 데이터 적재
# --------------------------------------------------------------------------- #
def load_sources(conn, src_df: pd.DataFrame) -> dict[str, int]:
    """출처 마스터를 적재하고 {source_code: source_id} 매핑을 돌려준다."""
    sql = """
        INSERT INTO faq_source (source_code, source_name, source_url, collect_method)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            source_name = VALUES(source_name),
            source_url  = VALUES(source_url),
            collect_method = VALUES(collect_method)
    """
    with conn.cursor() as cur:
        cur.executemany(sql, [
            (r.source_code, r.source_name, r.source_url, r.collect_method)
            for r in src_df.itertuples()
        ])
        cur.execute("SELECT source_code, source_id FROM faq_source")
        mapping = {row["source_code"]: row["source_id"] for row in cur.fetchall()}
    print(f"[2/5] faq_source 적재: {len(src_df)}건 → 테이블 총 {len(mapping)}건")
    return mapping


def load_categories(conn) -> dict[str, int]:
    """카테고리 기준값을 읽어 {category_name: category_id} 매핑을 돌려준다."""
    with conn.cursor() as cur:
        cur.execute("SELECT category_name, category_id FROM faq_category")
        return {row["category_name"]: row["category_id"] for row in cur.fetchall()}


def load_faqs(conn, faq_df: pd.DataFrame,
              cat_map: dict[str, int], src_map: dict[str, int]) -> dict[int, int]:
    """FAQ 본문을 적재하고 {CSV상 faq_id: DB상 faq_id} 매핑을 돌려준다."""
    sql = """
        INSERT INTO faq (category_id, source_id, question, answer, answer_length,
                         orig_msg_seq, view_count, department, content_hash, collected_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            category_id   = VALUES(category_id),
            source_id     = VALUES(source_id),
            question      = VALUES(question),
            answer        = VALUES(answer),
            answer_length = VALUES(answer_length),
            view_count    = VALUES(view_count)
    """
    rows = []
    for r in faq_df.itertuples():
        rows.append((
            cat_map[r.category],
            src_map[r.source_code],
            r.question,
            r.answer,
            int(r.answer_length),
            int(r.orig_msg_seq) if pd.notna(r.orig_msg_seq) else None,
            int(r.view_count) if pd.notna(r.view_count) else None,
            r.department if pd.notna(r.department) else None,
            r.content_hash,
            r.collected_at,
        ))
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
        cur.execute("SELECT faq_id, content_hash FROM faq")
        hash_to_id = {row["content_hash"]: row["faq_id"] for row in cur.fetchall()}

    csv_to_db = {int(r.faq_id): hash_to_id[r.content_hash]
                 for r in faq_df.itertuples() if r.content_hash in hash_to_id}
    print(f"[3/5] faq 적재: {len(rows)}건 → 테이블 총 {len(hash_to_id)}건")
    return csv_to_db


def load_keywords(conn, kw_df: pd.DataFrame, id_map: dict[int, int]) -> int:
    """FAQ 키워드를 적재한다."""
    sql = """
        INSERT INTO faq_keyword (faq_id, keyword, keyword_order)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE keyword_order = VALUES(keyword_order)
    """
    rows = [(id_map[int(r.faq_id)], r.keyword, int(r.keyword_order))
            for r in kw_df.itertuples() if int(r.faq_id) in id_map]
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
        cur.execute("SELECT COUNT(*) AS c FROM faq_keyword")
        total = cur.fetchone()["c"]
    print(f"[4/5] faq_keyword 적재: {len(rows)}건 → 테이블 총 {total}건")
    return total


def write_log(conn, status: str, collected: int, loaded: int, message: str) -> None:
    """수집·적재 실행 이력을 남긴다."""
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO crawl_log (source_id, status, collected_count, loaded_count, message)"
            " VALUES (NULL, %s, %s, %s, %s)",
            (status, collected, loaded, message),
        )
    print(f"[5/5] crawl_log 기록: {status} (수집 {collected} / 적재 {loaded})")


# --------------------------------------------------------------------------- #
# 메인
# --------------------------------------------------------------------------- #
def run() -> None:
    """전체 적재 파이프라인을 실행한다."""
    for path in (config.PROCESSED_FAQ_CSV, config.PROCESSED_KEYWORD_CSV,
                 config.PROCESSED_SOURCE_CSV):
        if not path.exists():
            raise FileNotFoundError(
                f"정제 데이터가 없습니다: {path.relative_to(config.BASE_DIR)}\n"
                f"  먼저 실행: python preprocess/build_faq_dataset.py"
            )

    faq_df = pd.read_csv(config.PROCESSED_FAQ_CSV, encoding="utf-8-sig")
    kw_df = pd.read_csv(config.PROCESSED_KEYWORD_CSV, encoding="utf-8-sig")
    src_df = pd.read_csv(config.PROCESSED_SOURCE_CSV, encoding="utf-8-sig")

    print("=" * 62)
    print(f"MySQL 적재 시작 — DB: {config.DB_NAME}")
    print("=" * 62)

    create_schema()

    conn = connect(with_database=True)
    try:
        src_map = load_sources(conn, src_df)
        cat_map = load_categories(conn)
        id_map = load_faqs(conn, faq_df, cat_map, src_map)
        kw_total = load_keywords(conn, kw_df, id_map)
        write_log(conn, "SUCCESS", len(faq_df), len(id_map),
                  f"FAQ {len(id_map)}건 / 키워드 {kw_total}건 적재")
        conn.commit()
        print("-" * 62)
        print("적재 완료 (커밋됨)")
    except Exception as exc:                    # noqa: BLE001
        conn.rollback()
        print(f"적재 실패 — 롤백함: {type(exc).__name__}: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    ok, msg = check_connection()
    print(msg)
    if not ok:
        print("\n.env 파일의 MySQL 접속 정보를 확인하세요 "
              "(.env.example 참고).")
        sys.exit(1)
    run()
