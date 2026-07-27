"""
수집 ① 게시판형 FAQ — BeautifulSoup (정적 페이지)
------------------------------------------------
대상 : 서울시설공단 장애인콜택시 > 참여·알림 > 자주하는 질문
        https://www.sisul.or.kr/open_content/calltaxi/community/faq.jsp

수집 방식 (2단계 크롤링)
  1단계) 목록 페이지 : <div id="contents"> 안의 <dl> 반복 구조에서
                       <dt><a>Q.질문</a></dt> / <dd>요약 답변</dd> 추출
                       - <a href>의 msg_seq 파라미터가 원본 게시글 고유번호
  2단계) 상세 페이지 : bbsMsgDetail.do?msg_seq=... 로 이동해
                       잘리지 않은 전체 답변 + 메타데이터(작성자·조회수·부서) 추출

실행 : python crawler/faq_board_bs4.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config                                            # noqa: E402
from crawler.common import (build_session, clean_text,   # noqa: E402
                            fetch_soup, save_raw, strip_q_prefix)


def extract_msg_seq(href: str) -> str | None:
    """상세 링크 href에서 게시글 고유번호(msg_seq)를 뽑아낸다."""
    if not href:
        return None
    query = urlparse(href).query
    seq = parse_qs(query).get("msg_seq")
    return seq[0] if seq else None


def parse_list_page(soup) -> list[dict]:
    """
    목록 페이지의 <dl> 아코디언에서 Q/A 쌍을 추출한다.

    페이지 하단 '컨텐츠 담당자' 영역에도 <dl>이 존재하므로,
    <dt><a>가 있는 <dl>만 FAQ 항목으로 인정한다.
    """
    items: list[dict] = []
    contents = soup.select_one("#contents")
    if contents is None:
        return items

    for dl in contents.find_all("dl"):
        link = dl.select_one("dt a")
        if link is None:
            continue                       # 담당자 정보 등 FAQ가 아닌 dl → 제외

        question = strip_q_prefix(clean_text(link.get_text(" ", strip=True)))
        dd = dl.find("dd")
        summary = ""
        if dd:
            # 답변 안의 '[더 보기]' 링크 텍스트는 본문이 아니므로 제거
            for more in dd.find_all("a"):
                more.decompose()
            summary = clean_text(dd.get_text("\n", strip=True))

        if not question:
            continue

        items.append({
            "msg_seq": extract_msg_seq(link.get("href", "")),
            "question": question,
            "answer_summary": summary,
            "detail_href": link.get("href", ""),
        })
    return items


def parse_detail_page(soup) -> dict:
    """
    상세 페이지에서 전체 답변과 메타데이터를 추출한다.

    구조: #contents > table
        1행 th        = 제목
        2행 th/td     = 작성자 / 조회수
        3행 th/td     = 등록 부서
        4행 th/td     = 질문구분 / FAQ 유형
        본문 셀        = colspan="4" 인 td (표가 포함된 답변은 중첩 table로 들어옴)

    ※ 답변 안에 표(예: 장애유형별 단독탑승 기준)가 중첩된 게시글이 있어
      '행 단위'로 본문을 찾으면 중첩 표 때문에 행 구조가 어긋난다.
      따라서 행이 아니라 colspan 속성으로 본문 셀을 직접 지목한다.
    """
    result = {"answer": "", "writer": "", "view_count": None,
              "department": "", "question_type": "", "faq_type": ""}

    table = soup.select_one("#contents table")
    if table is None:
        return result

    label_map = {
        "작성자": "writer", "조회수": "view_count", "등록 부서": "department",
        "등록부서": "department", "질문구분": "question_type", "FAQ 유형": "faq_type",
    }

    # 1) 메타데이터: th(라벨) ↔ td(값) 쌍으로 매핑
    for tr in table.find_all("tr"):
        ths, tds = tr.find_all("th"), tr.find_all("td")
        if ths and tds and len(ths) == len(tds):
            for th, td in zip(ths, tds):
                key = label_map.get(clean_text(th.get_text(strip=True)))
                if key:
                    result[key] = clean_text(td.get_text(" ", strip=True))

    # 2) 본문: colspan >= 4 인 td를 우선 채택, 없으면 가장 긴 td로 대체
    body_cells = [
        td for td in table.find_all("td")
        if str(td.get("colspan", "")).isdigit() and int(td["colspan"]) >= 4
    ]
    if not body_cells:
        body_cells = table.find_all("td")
    if body_cells:
        result["answer"] = max(
            (clean_text(td.get_text("\n", strip=True)) for td in body_cells),
            key=len, default="",
        )

    # 조회수는 숫자만 남겨 정수로 변환
    if result["view_count"]:
        digits = re.sub(r"[^0-9]", "", str(result["view_count"]))
        result["view_count"] = int(digits) if digits else None

    return result


def crawl() -> list[dict]:
    """게시판 FAQ를 목록 → 상세 순으로 수집한다."""
    print("[1/3] 게시판형 FAQ 수집 (BeautifulSoup)")
    session = build_session()

    print("  - 목록 페이지 요청 …")
    list_soup = fetch_soup(session, config.BOARD_LIST_URL,
                           params={**config.BOARD_PARAMS, "pageIndex": 1})
    items = parse_list_page(list_soup)
    print(f"  - 목록에서 {len(items)}건 발견")

    records: list[dict] = []
    for i, item in enumerate(items, start=1):
        detail = {}
        if item["msg_seq"]:
            print(f"  - 상세 {i}/{len(items)} (msg_seq={item['msg_seq']}) …")
            detail_soup = fetch_soup(
                session, config.BOARD_DETAIL_URL,
                params={**config.BOARD_PARAMS, "msg_seq": item["msg_seq"]},
            )
            detail = parse_detail_page(detail_soup)

        # 상세 본문이 비면 목록의 요약 답변으로 대체 (수집 누락 방지)
        answer = detail.get("answer") or item["answer_summary"]

        records.append({
            "source_code": "board_faq",
            "source_name": "서울시설공단 장애인콜택시 자주하는질문 게시판",
            "source_url": f"{config.BOARD_DETAIL_URL}?bcd=faq&cate1=calltaxi"
                          f"&msg_seq={item['msg_seq']}",
            "collect_method": "BeautifulSoup",
            "orig_msg_seq": item["msg_seq"],
            "question": item["question"],
            "answer": answer,
            "answer_summary": item["answer_summary"],
            "writer": detail.get("writer", ""),
            "department": detail.get("department", ""),
            "question_type": detail.get("question_type", ""),
            "view_count": detail.get("view_count"),
        })

    save_raw(records, config.RAW_BOARD_JSON,
             meta={"target": config.BOARD_PAGE_URL, "method": "BeautifulSoup",
                   "stage": "list+detail"})
    return records


if __name__ == "__main__":
    rows = crawl()
    print(f"\n완료: 게시판 FAQ {len(rows)}건 수집")
    for r in rows[:3]:
        print(f"  · [{r['orig_msg_seq']}] {r['question'][:45]} "
              f"(답변 {len(r['answer'])}자)")
