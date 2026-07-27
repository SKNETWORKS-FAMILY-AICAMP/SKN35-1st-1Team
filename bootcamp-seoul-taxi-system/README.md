# 우리동네 장애인 콜택시 — FAQ 파트

서울시 장애인콜택시 이용현황 분석 및 조회 시스템 (부트캠프 팀 프로젝트)
이 저장소 폴더는 **팀 4개 메뉴 중 `FAQ` 파트**의 전체 구현을 담고 있다.

| 메뉴 | 담당 | 상태 |
|---|---|---|
| 📊 이용현황 | 팀원 | 미구현 (자리표시 화면) |
| 📝 예약하기 | 팀원 | 미구현 (자리표시 화면) |
| ❓ **FAQ** | **본인** | ✅ **완료** |
| 📰 관련뉴스 | 팀원 | 미구현 (자리표시 화면) |

---

## 1. 담당 파트 요약

서울시설공단 장애인콜택시 공식 홈페이지(가입안내 · 이용기준 · 이용방법 ·
자주하는질문 게시판)를 크롤링해 **Q&A 형태로 재구성**하고, MySQL에 적재한 뒤
Streamlit **아코디언(`st.expander`)** 화면으로 조회한다.

```
크롤링(BeautifulSoup/Selenium) → 전처리(정규화·분류·키워드) → MySQL 적재 → Streamlit 조회
```

**최종 데이터** FAQ 21건 · 검색 키워드 105건 · 출처 8곳 · 분류 7종

---

## 2. 필수 산출물

| # | 산출물 | 위치 |
|---|---|---|
| ① | 데이터베이스 설계 문서 | [`docs/01_DB설계문서.md`](docs/01_DB설계문서.md) · DDL [`db/schema.sql`](db/schema.sql) |
| ② | 수집 데이터 | [`docs/02_수집데이터_명세.md`](docs/02_수집데이터_명세.md) · 원본 `data/raw/` · 정제 `data/processed/` |
| ③ | 데이터 조회 프로그램 | [`app/faq_page.py`](app/faq_page.py) (Streamlit) · [`db/repository.py`](db/repository.py) (조회 계층) |

---

## 3. 폴더 구조

```
bootcamp-seoul-taxi-system/
├── config.py                      # 공통 설정 (경로·DB·크롤링 대상)
├── .env.example                   # DB 접속 정보 템플릿 (.env로 복사해 사용)
├── requirements.txt
│
├── crawler/                       # 데이터 수집
│   ├── common.py                  #   세션·재시도·텍스트 정규화 유틸
│   ├── faq_board_bs4.py           #   ① 게시판 FAQ (BeautifulSoup, 목록→상세)
│   ├── guide_pages_bs4.py         #   ② 안내페이지 → Q&A 재구성 (BeautifulSoup)
│   └── faq_board_selenium.py      #   ③ 동적 아코디언 (Selenium) + 교차검증
│
├── preprocess/
│   └── build_faq_dataset.py       # 전처리 9단계 파이프라인
│
├── db/
│   ├── schema.sql                 # MySQL DDL (테이블 5종 + 카테고리 기준값)
│   ├── loader.py                  # PyMySQL 적재 (UPSERT, 트랜잭션)
│   └── repository.py              # 조회 계층 (MySQL / CSV 자동 전환)
│
├── app/
│   ├── faq_page.py                # ★ 담당 파트 화면 (render() 제공)
│   └── main_app.py                # 팀 통합 셸 (4개 메뉴 라우팅)
│
├── data/
│   ├── raw/                       # 수집 원본 JSON
│   └── processed/                 # 정제 CSV + 품질 리포트
│
└── docs/                          # 산출물 문서 3종
```

---

## 4. 실행 방법

```bash
# 0) 의존성 설치
pip install -r requirements.txt

# 1) DB 접속 정보 설정 — .env.example을 .env로 복사한 뒤 비밀번호 입력
copy .env.example .env

# 2) 데이터 수집
python crawler/faq_board_bs4.py         # 게시판 FAQ
python crawler/guide_pages_bs4.py       # 안내 페이지
python crawler/faq_board_selenium.py    # 동적 아코디언 (교차검증용)

# 3) 전처리
python preprocess/build_faq_dataset.py

# 4) MySQL 적재 (스키마 생성 + 데이터 적재)
python db/loader.py

# 5) 앱 실행
streamlit run app/main_app.py           # 팀 통합 화면
streamlit run app/faq_page.py           # FAQ 파트만 단독 확인
```

자세한 실행·문제해결은 [`docs/03_실행가이드.md`](docs/03_실행가이드.md) 참고.

---

## 5. 팀장 병합 가이드

통합 앱에서 이 파트를 연결하는 방법은 **두 줄**이다.

```python
from app.faq_page import render as render_faq

if menu == "FAQ":
    render_faq()
```

**병합 시 지켜진 규칙**

- 화면 코드(`app/`)와 데이터 접근 코드(`db/`)가 분리되어 있어 다른 파트와 충돌하지 않는다.
- 테이블명은 모두 `faq_` 접두어를 사용한다.
- DB 접속 설정은 `config.get_db_config()` 하나로 통일 — 다른 파트도 그대로 재사용 가능.
- MySQL이 준비되지 않은 환경에서는 정제 CSV로 자동 전환되어 발표 중 화면이 깨지지 않는다.

---

## 6. 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 수집 | Python · BeautifulSoup4 · Selenium (Chrome headless) · requests |
| 전처리 | pandas · re · hashlib · difflib |
| DB | MySQL 8.x · PyMySQL |
| 조회 GUI | Streamlit |
| ERD | DBeaver ER Diagram · Mermaid |

---

## 7. 참고

- `streamlit_app.py`(루트)는 기획 확정 **이전에 만든 초기 목업**이다.
  현재 기획(4개 메뉴)과 구성이 다르므로 팀 통합에는 `app/main_app.py`를 사용한다.
