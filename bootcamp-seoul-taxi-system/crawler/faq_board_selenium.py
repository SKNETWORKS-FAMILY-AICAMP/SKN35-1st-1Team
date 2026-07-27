"""
수집 ③ 게시판 FAQ 아코디언 — Selenium (동적 페이지)
--------------------------------------------------
BeautifulSoup만으로도 목록 HTML은 읽히지만, 자주하는질문 페이지의 답변(<dd>)은
`style="display:none"` 상태로 숨겨져 있고 JavaScript 토글로 펼쳐진다.
따라서 "실제 사용자가 보는 화면"을 기준으로 한 번 더 수집해
BeautifulSoup 수집 결과와 대조(교차검증)하는 것이 이 스크립트의 목적이다.

수행 내용
  1) Chrome(headless)으로 자주하는질문 페이지 접속
  2) 각 질문(dt > a)을 순서대로 클릭해 아코디언을 펼침
  3) 펼쳐진 dd 요소에서 화면에 실제 렌더링된 답변 텍스트 수집
  4) 결과를 JSON으로 저장 → 전처리 단계에서 BS4 결과와 정합성 비교

실행 : python crawler/faq_board_selenium.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import config                                             # noqa: E402
from crawler.common import clean_text, save_raw, strip_q_prefix   # noqa: E402

from selenium import webdriver                            # noqa: E402
from selenium.common.exceptions import WebDriverException  # noqa: E402
from selenium.webdriver.chrome.options import Options     # noqa: E402
from selenium.webdriver.common.by import By               # noqa: E402
from selenium.webdriver.support import expected_conditions as EC  # noqa: E402
from selenium.webdriver.support.ui import WebDriverWait   # noqa: E402


def build_driver(headless: bool = True) -> webdriver.Chrome:
    """크롤링용 Chrome 드라이버를 생성한다 (드라이버는 Selenium Manager가 자동 준비)."""
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,1000")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--log-level=3")
    options.add_argument(f"user-agent={config.USER_AGENT}")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    return webdriver.Chrome(options=options)


def crawl(headless: bool = True) -> list[dict]:
    """아코디언을 클릭해 펼친 뒤 렌더링된 답변을 수집한다."""
    print("[3/3] 게시판 FAQ 아코디언 수집 (Selenium)")
    driver = build_driver(headless)
    records: list[dict] = []

    try:
        driver.get(config.BOARD_PAGE_URL)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#contents dl dt a"))
        )

        links = driver.find_elements(By.CSS_SELECTOR, "#contents dl dt a")
        print(f"  - 질문 링크 {len(links)}개 확인")

        for idx in range(len(links)):
            # 클릭 후 DOM이 갱신될 수 있으므로 매 회차 요소를 다시 찾는다
            links = driver.find_elements(By.CSS_SELECTOR, "#contents dl dt a")
            if idx >= len(links):
                break
            link = links[idx]
            question = strip_q_prefix(clean_text(link.text))
            detail_id = link.get_attribute("aria-controls")

            try:
                # a 태그의 기본 이동(href)을 막고 아코디언 토글만 발생시킨다
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", link)
                driver.execute_script("arguments[0].click();", link)

                answer = ""
                if detail_id:
                    dd = WebDriverWait(driver, 5).until(
                        EC.visibility_of_element_located((By.ID, detail_id))
                    )
                    answer = clean_text(dd.text)
                    # 답변 말미의 '[더 보기]' 안내 문구는 본문이 아니므로 제거
                    answer = answer.replace("[더 보기]", "").strip()

                records.append({
                    "list_index": idx,
                    "question": question,
                    "answer_rendered": answer,
                    "detail_id": detail_id,
                    "collect_method": "Selenium",
                })
                print(f"    · {idx + 1}/{len(links)} {question[:38]} "
                      f"→ {len(answer)}자")

            except Exception as exc:                       # noqa: BLE001
                print(f"    · {idx + 1} 펼치기 실패: {type(exc).__name__}")
                records.append({
                    "list_index": idx, "question": question,
                    "answer_rendered": "", "detail_id": detail_id,
                    "collect_method": "Selenium", "error": type(exc).__name__,
                })

            # 페이지가 상세로 이동해버린 경우 목록으로 복귀
            if "bbsMsgDetail" in driver.current_url:
                driver.back()
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#contents dl dt a"))
                )

    except WebDriverException as exc:
        print(f"  ! Selenium 실행 실패: {exc.__class__.__name__} — {exc}")
    finally:
        driver.quit()

    save_raw(records, config.RAW_SELENIUM_JSON,
             meta={"target": config.BOARD_PAGE_URL, "method": "Selenium",
                   "purpose": "동적 아코디언 렌더링 결과 수집 및 BS4 교차검증"})
    return records


if __name__ == "__main__":
    rows = crawl()
    ok = sum(1 for r in rows if r.get("answer_rendered"))
    print(f"\n완료: Selenium {len(rows)}건 중 답변 확보 {ok}건")
