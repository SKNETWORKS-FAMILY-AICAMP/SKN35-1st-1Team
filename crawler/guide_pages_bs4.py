"""
수집 ② 안내 페이지 → Q&A 재구성 — BeautifulSoup (정적 페이지)
------------------------------------------------------------
대상 : 서울시설공단 장애인콜택시 > 소개 및 안내
        · 가입안내      introduce/join.jsp
        · 이용기준      introduce/receipt.jsp
        · 이용방법      introduce/guide.jsp  (인터넷접수)
                        introduce/guide4.jsp (문자접수)
                        introduce/guide5.jsp (앱접수)
        · 전일접수제 / 이용자 준수사항 (데이터 보강용)

재구성 규칙
  · 페이지 본문은 <h4> 소제목 단위로 나뉜다 → h4 하나 = FAQ 한 건
  · 답변 본문 = 해당 h4 이후 다음 h4/h3 직전까지의 형제 노드 텍스트
  · 질문 문장 = 소제목을 자연어 질문으로 변환
      - 사전에 정의한 템플릿이 있으면 그것을 사용
      - 없으면 한글 받침 유무로 조사(은/는)를 골라 자동 생성
  · 본문이 40자 미만인 소제목(이미지 캡션 등)은 FAQ로 부적합 → 제외
  · 유효한 h4가 하나도 없으면 페이지 전체를 1건으로 대체 수집

실행 : python crawler/guide_pages_bs4.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config                                            # noqa: E402
from crawler.common import (build_session, clean_text,   # noqa: E402
                            fetch_soup, save_raw)

MIN_BODY_LEN = 40      # 이보다 짧은 섹션은 FAQ로 쓰지 않는다

# 소제목 → 자연어 질문 템플릿 (기획서 지정 항목 위주)
QUESTION_TEMPLATES: dict[str, str] = {
    "가입안내": "장애인콜택시는 어떻게 가입하나요?",
    "이용대상": "장애인콜택시는 누가 이용할 수 있나요?",
    "운행지역": "장애인콜택시는 어느 지역까지 운행하나요?",
    "탑승인원": "장애인콜택시에 몇 명까지 함께 탑승할 수 있나요?",
    "신청접수": "장애인콜택시는 어떤 방법으로 신청·접수하나요?",
    "이용요금": "장애인콜택시 이용요금은 어떻게 산정되나요?",
    "차량연결기준": "장애인콜택시 차량은 어떤 기준으로 연결되나요?",
    "콜접수하기": "인터넷으로 콜을 접수하는 방법은 무엇인가요?",
    "콜접수 내역 확인 및 취소": "접수한 콜 내역은 어떻게 확인하고 취소하나요?",
    "문자접수방법": "문자로 장애인콜택시를 접수하는 방법은 무엇인가요?",
    "모바일 앱 사용방법": "모바일 앱으로 장애인콜택시를 접수하는 방법은 무엇인가요?",
    "장애인콜택시 이용고객 준수사항": "장애인콜택시 이용 시 지켜야 할 준수사항은 무엇인가요?",
    "전일접수제": "전일접수제는 무엇이며 어떻게 이용하나요?",
    "전일접수제이용안내": "전일접수제는 무엇이며 어떻게 이용하나요?",
}


def has_batchim(word: str) -> bool:
    """한글 단어의 마지막 글자에 받침이 있는지 판별한다 (조사 선택용)."""
    if not word:
        return False
    last = word[-1]
    if not ("가" <= last <= "힣"):
        return False
    return (ord(last) - 0xAC00) % 28 != 0


def to_question(section_title: str, page_title: str) -> str:
    """소제목을 자연어 질문 문장으로 변환한다."""
    title = section_title.strip()
    if title in QUESTION_TEMPLATES:
        return QUESTION_TEMPLATES[title]
    if page_title in QUESTION_TEMPLATES:
        return QUESTION_TEMPLATES[page_title]
    particle = "은" if has_batchim(title) else "는"
    return f"장애인콜택시 {title}{particle} 어떻게 되나요?"


def section_body(heading) -> str:
    """h4 태그 이후 다음 소제목 직전까지의 텍스트를 이어붙인다."""
    parts: list[str] = []
    for sib in heading.next_siblings:
        if getattr(sib, "name", None) in ("h3", "h4"):
            break
        text = sib.get_text("\n", strip=True) if hasattr(sib, "get_text") else str(sib)
        text = clean_text(text)
        if text:
            parts.append(text)
    return clean_text("\n".join(parts))


def parse_guide_page(soup, page: dict) -> list[dict]:
    """안내 페이지 하나를 여러 건의 Q&A 레코드로 변환한다."""
    contents = soup.select_one("#contents")
    if contents is None:
        return []

    h3 = contents.select_one("h3")
    page_title = clean_text(h3.get_text(strip=True)) if h3 else page["title"]

    records: list[dict] = []
    for idx, h4 in enumerate(contents.select("h4")):
        title = clean_text(h4.get_text(" ", strip=True))
        body = section_body(h4)
        if len(body) < MIN_BODY_LEN:
            continue                       # 이미지 캡션 등 실질 내용 없는 섹션 제외
        records.append({
            "section_index": idx,
            "section_title": title,
            "question": to_question(title, page_title),
            "answer": body,
        })

    # 유효 섹션이 없으면 페이지 전체를 한 건으로 대체 수집
    if not records:
        body = clean_text(contents.get_text("\n", strip=True))
        if len(body) >= MIN_BODY_LEN:
            records.append({
                "section_index": 0,
                "section_title": page_title,
                "question": to_question(page_title, page_title),
                "answer": body,
            })

    for r in records:
        r.update({
            "source_code": page["code"],
            "source_name": f"서울시설공단 장애인콜택시 {page['title']}",
            "source_url": config.SISUL_BASE + page["path"],
            "collect_method": "BeautifulSoup",
            "category_hint": page["group"],
            "page_title": page_title,
        })
    return records


def crawl() -> list[dict]:
    """설정에 등록된 모든 안내 페이지를 수집한다."""
    print("[2/3] 안내 페이지 FAQ 재구성 수집 (BeautifulSoup)")
    session = build_session()

    all_records: list[dict] = []
    for page in config.GUIDE_PAGES:
        print(f"  - {page['title']} ({page['path']}) …")
        soup = fetch_soup(session, config.SISUL_BASE + page["path"])
        rows = parse_guide_page(soup, page)
        print(f"      섹션 {len(rows)}건 추출")
        all_records.extend(rows)

    save_raw(all_records, config.RAW_GUIDE_JSON,
             meta={"page_count": len(config.GUIDE_PAGES), "method": "BeautifulSoup",
                   "rule": "h4 소제목 단위 Q&A 재구성"})
    return all_records


if __name__ == "__main__":
    rows = crawl()
    print(f"\n완료: 안내 페이지 FAQ {len(rows)}건 재구성")
    for r in rows:
        print(f"  · [{r['source_code']}] {r['question'][:50]} (답변 {len(r['answer'])}자)")
