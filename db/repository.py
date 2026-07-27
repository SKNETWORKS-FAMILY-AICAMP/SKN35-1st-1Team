"""
FAQ 조회 계층 (Repository / DAO)
--------------------------------
Streamlit 화면은 SQL을 직접 다루지 않고 이 모듈의 함수만 호출한다.
→ 화면 코드와 데이터 접근 코드를 분리해 팀 병합·유지보수를 쉽게 한다.

두 가지 구현을 제공한다.
  · MySqlFaqRepository : MySQL(PyMySQL) 조회 — 정식 경로
  · CsvFaqRepository   : 정제 CSV 조회 — DB가 준비되지 않은 환경(발표/시연)용 대체

get_repository()가 MySQL 접속을 먼저 시도하고, 실패하면 CSV로 자동 전환한다.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config  # noqa: E402


# --------------------------------------------------------------------------- #
# MySQL 구현
# --------------------------------------------------------------------------- #
class MySqlFaqRepository:
    """MySQL seoul_calltaxi 스키마를 조회한다."""

    backend = "MySQL"

    def __init__(self) -> None:
        import pymysql  # 지연 임포트 — CSV 모드에서는 필요 없음
        self._pymysql = pymysql

    def _query(self, sql: str, params: tuple = ()) -> pd.DataFrame:
        """SQL을 실행해 DataFrame으로 반환한다.

        pandas.read_sql은 SQLAlchemy 연결이 아니면 경고를 내므로
        커서로 직접 조회한 뒤 DataFrame으로 변환한다.
        """
        conn = self._pymysql.connect(**config.get_db_config(),
                                     cursorclass=self._pymysql.cursors.DictCursor)
        try:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
                columns = [d[0] for d in cur.description]
            return pd.DataFrame(rows, columns=columns)
        finally:
            conn.close()

    def list_categories(self) -> list[str]:
        """실제 FAQ가 1건 이상 존재하는 카테고리만 순서대로 반환한다."""
        sql = """
            SELECT c.category_name
            FROM faq_category c
            JOIN faq f ON f.category_id = c.category_id
            GROUP BY c.category_id, c.category_name, c.sort_order
            ORDER BY c.sort_order
        """
        return self._query(sql)["category_name"].tolist()

    def search(self, keyword: str = "", category: str = "전체") -> pd.DataFrame:
        """
        키워드/카테고리로 FAQ를 조회한다.

        키워드는 질문·답변 본문과 faq_keyword 테이블을 함께 검색한다.
        """
        sql = """
            SELECT DISTINCT
                   f.faq_id, c.category_name AS category, f.question, f.answer,
                   f.answer_length, s.source_name, s.source_url, s.collect_method,
                   f.view_count, f.department, f.collected_at, c.sort_order
            FROM faq f
            JOIN faq_category c ON c.category_id = f.category_id
            JOIN faq_source  s ON s.source_id  = f.source_id
            LEFT JOIN faq_keyword k ON k.faq_id = f.faq_id
            WHERE 1 = 1
        """
        params: list = []
        if category and category != "전체":
            sql += " AND c.category_name = %s"
            params.append(category)
        if keyword.strip():
            like = f"%{keyword.strip()}%"
            sql += " AND (f.question LIKE %s OR f.answer LIKE %s OR k.keyword LIKE %s)"
            params += [like, like, like]
        sql += " ORDER BY c.sort_order, f.faq_id"
        return self._query(sql, tuple(params))

    def keywords_of(self, faq_id: int) -> list[str]:
        """특정 FAQ의 검색 키워드를 순위대로 반환한다."""
        sql = ("SELECT keyword FROM faq_keyword WHERE faq_id = %s "
               "ORDER BY keyword_order")
        return self._query(sql, (faq_id,))["keyword"].tolist()

    def stats(self) -> dict:
        """대시보드용 요약 통계."""
        total = self._query("SELECT COUNT(*) AS c FROM faq")["c"].iloc[0]
        cats = self._query("SELECT COUNT(DISTINCT category_id) AS c FROM faq")["c"].iloc[0]
        srcs = self._query("SELECT COUNT(*) AS c FROM faq_source")["c"].iloc[0]
        kws = self._query("SELECT COUNT(*) AS c FROM faq_keyword")["c"].iloc[0]
        by_cat = self._query("""
            SELECT c.category_name AS category, COUNT(*) AS cnt
            FROM faq f JOIN faq_category c ON c.category_id = f.category_id
            GROUP BY c.category_id, c.category_name, c.sort_order
            ORDER BY c.sort_order
        """)
        return {"faq_count": int(total), "category_count": int(cats),
                "source_count": int(srcs), "keyword_count": int(kws),
                "by_category": by_cat}


# --------------------------------------------------------------------------- #
# CSV 대체 구현
# --------------------------------------------------------------------------- #
class CsvFaqRepository:
    """정제 CSV를 읽어 MySQL과 동일한 인터페이스로 조회한다."""

    backend = "CSV(대체)"

    def __init__(self) -> None:
        self.faq = pd.read_csv(config.PROCESSED_FAQ_CSV, encoding="utf-8-sig")
        self.kw = pd.read_csv(config.PROCESSED_KEYWORD_CSV, encoding="utf-8-sig")
        order = {name: i for i, name in enumerate(config.FAQ_CATEGORIES)}
        self.faq["sort_order"] = self.faq["category"].map(order).fillna(99).astype(int)

    def list_categories(self) -> list[str]:
        present = set(self.faq["category"])
        return [c for c in config.FAQ_CATEGORIES if c in present]

    def search(self, keyword: str = "", category: str = "전체") -> pd.DataFrame:
        df = self.faq.copy()
        if category and category != "전체":
            df = df[df["category"] == category]
        if keyword.strip():
            key = keyword.strip()
            hit_ids = set(self.kw.loc[
                self.kw["keyword"].str.contains(key, na=False), "faq_id"])
            mask = (df["question"].str.contains(key, na=False)
                    | df["answer"].str.contains(key, na=False)
                    | df["faq_id"].isin(hit_ids))
            df = df[mask]
        return df.sort_values(["sort_order", "faq_id"]).reset_index(drop=True)

    def keywords_of(self, faq_id: int) -> list[str]:
        rows = self.kw[self.kw["faq_id"] == faq_id].sort_values("keyword_order")
        return rows["keyword"].tolist()

    def stats(self) -> dict:
        by_cat = (self.faq.groupby(["sort_order", "category"], as_index=False)
                  .size().rename(columns={"size": "cnt"})
                  .sort_values("sort_order")[["category", "cnt"]])
        return {"faq_count": len(self.faq),
                "category_count": self.faq["category"].nunique(),
                "source_count": self.faq["source_code"].nunique(),
                "keyword_count": len(self.kw),
                "by_category": by_cat}


# --------------------------------------------------------------------------- #
# 팩토리
# --------------------------------------------------------------------------- #
def get_repository() -> tuple[object, str]:
    """
    사용 가능한 저장소를 선택해 (repository, 상태메시지)로 반환한다.

    MySQL 접속에 성공하고 faq 테이블에 데이터가 있으면 MySQL을,
    그렇지 않으면 정제 CSV를 사용한다.
    """
    try:
        repo = MySqlFaqRepository()
        count = repo.stats()["faq_count"]
        if count > 0:
            return repo, f"MySQL 연결됨 · {config.DB_NAME} · FAQ {count}건"
        reason = "MySQL에 적재된 FAQ가 없습니다 (python db/loader.py 실행 필요)"
    except Exception as exc:                    # noqa: BLE001
        reason = f"MySQL 접속 불가 ({type(exc).__name__})"

    if config.PROCESSED_FAQ_CSV.exists():
        return CsvFaqRepository(), f"{reason} → 정제 CSV로 조회 중"
    raise RuntimeError(
        f"{reason}, 정제 CSV도 없습니다. "
        "먼저 크롤링·전처리를 실행하세요: python preprocess/build_faq_dataset.py"
    )


if __name__ == "__main__":
    repo, status = get_repository()
    print("백엔드:", repo.backend, "|", status)
    print("카테고리:", repo.list_categories())
    s = repo.stats()
    print(f"FAQ {s['faq_count']}건 / 키워드 {s['keyword_count']}건 / 출처 {s['source_count']}종")
    hit = repo.search(keyword="요금")
    print(f"'요금' 검색 결과 {len(hit)}건")
    for _, r in hit.head(3).iterrows():
        print("  ·", r["question"][:50])
