"""
전처리 파이프라인 — 원본(raw) → 정제(processed)
------------------------------------------------
수집 원본 JSON 3종을 읽어 DB 적재용 정제 데이터셋(CSV)으로 변환한다.

처리 단계
  STEP 1. 원본 로드          : 게시판(BS4) / 안내페이지(BS4) / 게시판(Selenium)
  STEP 2. 텍스트 정규화       : 엔티티·공백·개행 정리, 질문 말미 물음표 보정
  STEP 3. 섹션 병합          : 앱접수 화면설명 22건 → '앱 이용방법' 1건으로 통합
  STEP 4. 결측·이상치 제거    : 질문/답변 결측, 답변 30자 미만 제거
  STEP 5. 중복 제거          : 정규화 질문키 + 내용해시(content_hash) 기준
  STEP 6. 카테고리 자동분류   : 규칙(키워드) 기반 7개 카테고리 매핑
  STEP 7. 키워드 추출        : 조사 제거 후 빈도 상위 5개 (검색용)
  STEP 8. 교차검증           : BS4 상세본 vs Selenium 렌더링본 길이/일치율 비교
  STEP 9. 산출물 저장         : faq_clean.csv / faq_keyword_clean.csv /
                              faq_source_clean.csv / quality_report.json

실행 : python preprocess/build_faq_dataset.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from collections import Counter
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config                          # noqa: E402
from crawler.common import clean_text, load_raw   # noqa: E402

MIN_ANSWER_LEN = 30

# --------------------------------------------------------------------------- #
# 카테고리 분류 규칙 — 위에서부터 먼저 일치하는 규칙을 채택한다
# --------------------------------------------------------------------------- #
#   ※ 키워드는 '변별력'이 있어야 한다.
#     예) '콜'은 모든 문서에 있는 '장애인콜택시'에 걸려 대부분을 한 분류로 몰아버린다.
#         '이용' 역시 거의 모든 문장에 등장하므로 키워드로 쓰지 않는다.
CATEGORIES: list[tuple[str, list[str]]] = [
    ("가입·등록", ["가입", "등록제", "고객등록", "신규등록", "복지카드", "증빙서류",
                  "제출서류", "처음"]),
    ("이용대상·자격", ["이용대상", "이용자격", "자격", "누가", "중증", "보행상",
                     "장애정도", "단독탑승", "동승", "탑승", "탑승인원"]),
    ("요금·결제", ["요금", "운임", "결제", "비용", "감면"]),
    ("배차·대기", ["배차", "대기", "연결", "지연"]),
    ("운행지역·시간", ["운행지역", "운행시간", "운행", "지역", "광역", "수도권", "첫차"]),
    ("이용방법·접수", ["접수", "신청", "예약", "취소", "전일접수", "이용방법",
                     "앱", "문자", "인터넷", "전화"]),
    ("준수사항·기타", ["준수", "금지", "매각", "취업", "운전원", "채용", "성희롱"]),
]
DEFAULT_CATEGORY = config.DEFAULT_CATEGORY

# 분류 규칙이 표준 카테고리 목록과 어긋나지 않는지 로드 시점에 검증
_unknown = [name for name, _ in CATEGORIES if name not in config.FAQ_CATEGORIES]
if _unknown:
    raise ValueError(f"CATEGORIES에 표준 분류 밖의 값이 있습니다: {_unknown}")

# 키워드 추출용 불용어 및 조사
STOPWORDS = {
    "장애인콜택시", "장애인", "콜택시", "경우", "관련", "내용", "안내", "이용", "가능",
    "필요", "확인", "신청", "다음", "아래", "위해", "대해", "대한", "따라", "통해",
    "합니다", "입니다", "있습니다", "됩니다", "습니다", "하시기", "바랍니다", "주시기",
    "어떻게", "무엇", "알고", "싶습니다", "궁금합니다", "하나요", "되나요", "인가요",
}
JOSA = ("으로서", "에서는", "에게서", "이라고", "으로", "에서", "에게", "부터", "까지",
        "이나", "라도", "처럼", "만큼", "보다", "와의", "과의", "은", "는", "이", "가",
        "을", "를", "의", "에", "로", "와", "과", "도", "만", "및")


# 의문형 어미 — 이 형태로 끝나는 문장에만 물음표를 보정한다
INTERROGATIVE_END = re.compile(r"(나요|가요|까요|는가|는지|무엇|어디|얼마|언제|어떻게)$")


def normalize_question(text: str) -> str:
    """
    질문 문장을 다듬는다.

    공백·개행을 정리하고 끝의 마침표를 제거한 뒤,
    의문형 어미로 끝나는 문장에만 물음표를 붙인다.
    ('~알고 싶습니다' 같은 평서형 제목에는 물음표를 붙이지 않는다)
    """
    q = clean_text(text).replace("\n", " ")
    q = re.sub(r"\s+", " ", q).strip()
    q = q.rstrip(" .·-")
    if q and not q.endswith("?") and INTERROGATIVE_END.search(q):
        q += "?"
    return q


def content_hash(question: str, answer: str) -> str:
    """질문+답변의 내용 해시 (중복 판정 및 변경 감지용)."""
    key = re.sub(r"\s+", "", f"{question}|{answer}")
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def classify(question: str, answer: str) -> str | None:
    """
    규칙 기반으로 FAQ 카테고리를 판정한다. 일치 규칙이 없으면 None.

    '먼저 일치하는 규칙 채택' 방식은 규칙 순서에 결과가 좌우된다.
    (예: '운전원 취업' 문의가 '자격' 한 단어 때문에 이용대상으로 분류됨)
    따라서 카테고리별 키워드 적중 수를 점수로 집계해 최고점을 채택한다.

    또한 FAQ에서 주제를 가장 잘 나타내는 것은 '질문'이다.
    본문에는 부수적 단어가 많이 섞여 있으므로 질문으로 먼저 판정하고,
    질문에서 아무 규칙도 걸리지 않을 때만 본문 앞부분으로 재판정한다.
    """
    for text in (question, answer[:300]):
        scores = {name: sum(1 for k in keywords if k in text)
                  for name, keywords in CATEGORIES}
        scores = {name: sc for name, sc in scores.items() if sc > 0}
        if not scores:
            continue
        best = max(scores.values())
        # 동점이면 CATEGORIES에 먼저 정의된 카테고리를 채택 (규칙 우선순위)
        for name, _ in CATEGORIES:
            if scores.get(name) == best:
                return name
    return None


def strip_josa(token: str) -> str:
    """토큰 끝의 조사를 제거한다 (제거 후 2글자 미만이면 원형 유지)."""
    for j in JOSA:
        if token.endswith(j) and len(token) - len(j) >= 2:
            return token[: -len(j)]
    return token


def extract_keywords(question: str, answer: str, top_n: int = 5) -> list[str]:
    """한글 명사형 토큰의 빈도를 세어 검색용 키워드를 뽑는다."""
    text = f"{question} {answer}"
    tokens = re.findall(r"[가-힣]{2,}", text)
    cleaned = [strip_josa(t) for t in tokens]
    counter = Counter(
        t for t in cleaned if len(t) >= 2 and t not in STOPWORDS
    )
    return [w for w, _ in counter.most_common(top_n)]


# --------------------------------------------------------------------------- #
# STEP 1~3 : 로드 및 레코드 정규화
# --------------------------------------------------------------------------- #
def load_board_records() -> list[dict]:
    """게시판(BS4) 원본을 표준 레코드로 변환한다."""
    rows = []
    for r in load_raw(config.RAW_BOARD_JSON):
        rows.append({
            "question": normalize_question(r["question"]),
            "answer": clean_text(r["answer"]),
            "source_code": r["source_code"],
            "source_name": r["source_name"],
            "source_url": r["source_url"],
            "collect_method": r["collect_method"],
            "orig_msg_seq": r.get("orig_msg_seq"),
            "view_count": r.get("view_count"),
            "department": r.get("department", ""),
            "category_hint": "",
        })
    return rows


def load_guide_records() -> list[dict]:
    """
    안내페이지(BS4) 원본을 표준 레코드로 변환한다.

    앱접수(guide_app) 페이지는 화면 캡처 설명이 20건 이상으로 잘게 쪼개져 있어
    개별 FAQ로서 의미가 약하다 → 하나의 '앱 이용방법' 절차 안내로 병합한다.
    """
    raw = load_raw(config.RAW_GUIDE_JSON)

    app_sections = [r for r in raw if r["source_code"] == "guide_app"]
    others = [r for r in raw if r["source_code"] != "guide_app"]

    rows = []
    for r in others:
        rows.append({
            "question": normalize_question(r["question"]),
            "answer": clean_text(r["answer"]),
            "source_code": r["source_code"],
            "source_name": r["source_name"],
            "source_url": r["source_url"],
            "collect_method": r["collect_method"],
            "orig_msg_seq": None,
            "view_count": None,
            "department": "",
            "category_hint": r.get("category_hint", ""),
        })

    if app_sections:
        steps = [
            f"{i}. [{s['section_title']}] {s['answer']}"
            for i, s in enumerate(sorted(app_sections, key=lambda x: x["section_index"]), 1)
        ]
        merged = ("모바일 앱으로 장애인콜택시를 접수하는 절차는 다음과 같습니다.\n\n"
                  + "\n".join(steps))
        first = app_sections[0]
        rows.append({
            "question": "모바일 앱으로 장애인콜택시를 접수하는 방법은 무엇인가요?",
            "answer": clean_text(merged),
            "source_code": "guide_app",
            "source_name": first["source_name"],
            "source_url": first["source_url"],
            "collect_method": "BeautifulSoup",
            "orig_msg_seq": None,
            "view_count": None,
            "department": "",
            "category_hint": first.get("category_hint", ""),
            "merged_section_count": len(app_sections),
        })
        print(f"  STEP 3 섹션 병합: 앱접수 화면설명 {len(app_sections)}건 → 1건")

    return rows


# --------------------------------------------------------------------------- #
# STEP 8 : 교차검증
# --------------------------------------------------------------------------- #
def cross_validate(board_rows: list[dict]) -> dict:
    """BS4 상세 수집본과 Selenium 렌더링본을 질문 기준으로 대조한다."""
    sel_rows = load_raw(config.RAW_SELENIUM_JSON)
    if not sel_rows:
        return {"checked": 0, "note": "Selenium 원본 없음 — 검증 생략"}

    sel_map = {normalize_question(r["question"]): r.get("answer_rendered", "")
               for r in sel_rows}

    matched, details = 0, []
    for row in board_rows:
        rendered = sel_map.get(row["question"])
        if rendered is None:
            continue
        matched += 1
        ratio = SequenceMatcher(None, row["answer"][:200], rendered[:200]).ratio()
        details.append({
            "question": row["question"][:40],
            "bs4_len": len(row["answer"]),
            "selenium_len": len(rendered),
            "prefix_similarity": round(ratio, 3),
        })

    avg_ratio = round(sum(d["prefix_similarity"] for d in details) / len(details), 3) \
        if details else 0.0
    return {
        "checked": matched,
        "selenium_total": len(sel_rows),
        "avg_prefix_similarity": avg_ratio,
        "conclusion": ("Selenium 렌더링본은 목록 요약(축약)이고 BS4 상세본이 전문이므로 "
                       "최종 적재는 BS4 상세 수집본을 채택"),
        "details": details,
    }


# --------------------------------------------------------------------------- #
# 메인 파이프라인
# --------------------------------------------------------------------------- #
def build() -> pd.DataFrame:
    """전체 전처리 파이프라인을 실행하고 정제 CSV를 생성한다."""
    print("=" * 62)
    print("전처리 파이프라인 시작")
    print("=" * 62)

    # STEP 1~3
    board = load_board_records()
    guide = load_guide_records()
    records = board + guide
    print(f"  STEP 1 원본 로드: 게시판 {len(board)}건 + 안내페이지 {len(guide)}건 "
          f"= {len(records)}건")

    df = pd.DataFrame(records)
    before = len(df)

    # STEP 4 결측·이상치 제거
    df = df[df["question"].str.len() > 0]
    df = df[df["answer"].str.len() >= MIN_ANSWER_LEN]
    print(f"  STEP 4 결측·짧은답변 제거: {before} → {len(df)}건 "
          f"(답변 {MIN_ANSWER_LEN}자 미만 제외)")

    # STEP 5 중복 제거
    df["content_hash"] = [content_hash(q, a) for q, a in zip(df["question"], df["answer"])]
    df["question_key"] = df["question"].str.replace(r"\s+", "", regex=True)
    before = len(df)
    df = df.drop_duplicates(subset=["content_hash"])
    df = df.drop_duplicates(subset=["question_key"], keep="first")
    print(f"  STEP 5 중복 제거: {before} → {len(df)}건")

    # STEP 6 카테고리 분류
    #   1순위 내용 기반 규칙 분류 → 2순위 출처 페이지 힌트 → 3순위 기본값
    #   (한 페이지 안에 서로 다른 주제의 섹션이 섞여 있어 힌트를 우선하면 오분류된다.
    #    예: '이용기준' 페이지의 '이용요금' 섹션 → 요금·결제로 가야 함)
    categories = []
    for hint, q, a in zip(df["category_hint"], df["question"], df["answer"]):
        rule = classify(q, a)
        if rule:
            categories.append(rule)
        elif hint in config.FAQ_CATEGORIES:
            categories.append(hint)
        else:
            categories.append(DEFAULT_CATEGORY)
    df["category"] = categories
    # 표준 분류(7종)를 벗어난 값이 남지 않도록 최종 방어
    off_taxonomy = set(df["category"]) - set(config.FAQ_CATEGORIES)
    if off_taxonomy:
        raise ValueError(f"표준 분류 밖의 카테고리가 생성되었습니다: {off_taxonomy}")
    print(f"  STEP 6 카테고리 분류: {df['category'].nunique()}/"
          f"{len(config.FAQ_CATEGORIES)}개 카테고리 사용")
    for cat, cnt in df["category"].value_counts().items():
        print(f"          - {cat}: {cnt}건")

    # STEP 7 키워드 추출
    df["keywords"] = [extract_keywords(q, a) for q, a in zip(df["question"], df["answer"])]
    print(f"  STEP 7 키워드 추출: 건당 최대 5개")

    # STEP 8 교차검증
    report = cross_validate(board)
    print(f"  STEP 8 교차검증: {report.get('checked')}건 대조, "
          f"평균 유사도 {report.get('avg_prefix_similarity')}")

    # STEP 9 저장 --------------------------------------------------------- #
    df = df.reset_index(drop=True)
    df.insert(0, "faq_id", range(1, len(df) + 1))
    df["answer_length"] = df["answer"].str.len()
    df["collected_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    faq_cols = ["faq_id", "category", "question", "answer", "answer_length",
                "source_code", "source_name", "source_url", "collect_method",
                "orig_msg_seq", "view_count", "department", "content_hash",
                "collected_at"]
    faq_df = df[faq_cols]
    faq_df.to_csv(config.PROCESSED_FAQ_CSV, index=False, encoding="utf-8-sig")

    kw_rows = [{"faq_id": fid, "keyword": kw, "keyword_order": i}
               for fid, kws in zip(df["faq_id"], df["keywords"])
               for i, kw in enumerate(kws, start=1)]
    kw_df = pd.DataFrame(kw_rows)
    kw_df.to_csv(config.PROCESSED_KEYWORD_CSV, index=False, encoding="utf-8-sig")

    src_df = (df[["source_code", "source_name", "source_url", "collect_method"]]
              .drop_duplicates(subset=["source_code"])
              .reset_index(drop=True))
    src_df.insert(0, "source_id", range(1, len(src_df) + 1))
    src_df.to_csv(config.PROCESSED_SOURCE_CSV, index=False, encoding="utf-8-sig")

    quality = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "faq_count": int(len(faq_df)),
        "keyword_count": int(len(kw_df)),
        "source_count": int(len(src_df)),
        "category_distribution": df["category"].value_counts().to_dict(),
        "answer_length": {
            "min": int(df["answer_length"].min()),
            "max": int(df["answer_length"].max()),
            "mean": round(float(df["answer_length"].mean()), 1),
        },
        "null_check": {c: int(faq_df[c].isna().sum()) for c in faq_cols},
        "cross_validation": report,
    }
    config.QUALITY_REPORT_JSON.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8")

    print("-" * 62)
    print(f"  STEP 9 저장 완료")
    for p in (config.PROCESSED_FAQ_CSV, config.PROCESSED_KEYWORD_CSV,
              config.PROCESSED_SOURCE_CSV, config.QUALITY_REPORT_JSON):
        print(f"          → {p.relative_to(config.BASE_DIR)}")
    print(f"\n최종 정제 데이터: FAQ {len(faq_df)}건 / 키워드 {len(kw_df)}건 / "
          f"출처 {len(src_df)}건")
    return faq_df


if __name__ == "__main__":
    build()
