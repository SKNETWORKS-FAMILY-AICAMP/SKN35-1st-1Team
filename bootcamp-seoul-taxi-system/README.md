# 우리동네 장애인 콜택시 — FAQ 파트

서울시 장애인콜택시 이용현황 분석 및 조회 시스템 (부트캠프 팀 프로젝트)
이 저장소 폴더는 **팀 4개 메뉴 중 `FAQ` 파트**의 전체 구현을 담고 있다.

| 메뉴 | 담당 | 상태 |
|---|---|---|
| 📊 이용현황 | 팀원 | 미구현 (자리표시 화면) |
| 📝 예약하기 | 팀원 | 미구현 (자리표시 화면) |
| ❓ **FAQ** | **본인** | ✅ **완료** |
| 📰 관련뉴스 | 팀원 | 화면만 구현 (데이터는 예시) |

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
| ③ | 데이터 조회 프로그램 | [`views/faq.py`](views/faq.py) (Streamlit) · [`db/repository.py`](db/repository.py) (조회 계층) |

산출물 ①②를 **화면으로** 보려면 [`필수산출물/`](필수산출물/) 폴더를 단독 실행한다.

---

## 3. 폴더 구조

역할별로 계층을 나눴다. `main.py`는 라우팅만 하고, 화면은 `views/`, 공통 요소는 `common/`, 스타일은 `style/`에 둔다.

```
bootcamp-seoul-taxi-system/
├── main.py                        # ★ 앱 진입점 — 라우팅만 담당
├── config.py                      # 공통 설정 (경로·DB·크롤링 대상)
├── .env.example                   # DB 접속 정보 템플릿 (.env로 복사해 사용)
├── requirements.txt
│
├── views/                         # 화면 (UI) — 파일 하나가 페이지 하나, render() 제공
│   ├── home.py                    #   브랜드 히어로 + 바로가기 카드 4개
│   ├── faq.py                     #   ★ 담당 파트 — FAQ 아코디언
│   ├── news.py                    #   관련뉴스 (탭·검색·페이지네이션)
│   └── placeholder.py             #   미구현 파트 자리표시 (이용현황·예약하기)
│
├── common/                        # 공통 모듈
│   ├── brand.py                   #   브랜드 상수 · 페이지 정의(PAGES)
│   ├── assets.py                  #   SVG 일러스트 → data URI
│   ├── styles.py                  #   style/ CSS 로더
│   ├── layout.py                  #   사이드바
│   ├── news_data.py               #   뉴스 데이터 + 검색 로직
│   └── text.py                    #   텍스트 유틸
│
├── style/                         # CSS — 색상은 style.css의 CSS 변수로 통일
│   ├── style.css                  #   공통 (전역 · 사이드바)
│   ├── home.css                   #   홈 전용
│   ├── faq.css                    #   FAQ 전용
│   └── news.css                   #   관련뉴스 전용
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
├── db/                            # DB 계층
│   ├── schema.sql                 #   MySQL DDL (테이블 5종 + 카테고리 기준값)
│   ├── loader.py                  #   PyMySQL 적재 (UPSERT, 트랜잭션)
│   └── repository.py              #   조회 계층 (MySQL / CSV 자동 전환)
│
├── data/
│   ├── raw/                       # 수집 원본 JSON
│   └── processed/                 # 정제 CSV + 품질 리포트
│
├── docs/                          # 산출물 문서 3종
│
└── 필수산출물/                     # 부트캠프 제출용 화면 (독립 실행 · 폴더째 삭제 가능)
    └── app.py                     #   DB설계 · 수집데이터 · 프로젝트소개
```

**의존 방향은 한 방향이다.** `main.py → views/ → common/ · db/`. 역참조가 없어 순환 임포트가 발생하지 않는다.

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
streamlit run main.py                   # 팀 통합 화면
streamlit run views/faq.py              # FAQ 파트만 단독 확인
streamlit run 필수산출물/app.py          # 필수산출물 화면 (DB설계·수집데이터·소개)
```

자세한 실행·문제해결은 [`docs/03_실행가이드.md`](docs/03_실행가이드.md) 참고.

---

## 5. 팀장 병합 가이드

통합 앱에서 이 파트를 연결하는 방법은 **두 줄**이다.

```python
from views.faq import render as render_faq

if menu == "faq":
    render_faq()
```

**병합 시 지켜진 규칙**

- 화면 코드(`views/`)와 데이터 접근 코드(`db/`)가 분리되어 있어 다른 파트와 충돌하지 않는다.
- 테이블명은 모두 `faq_` 접두어를 사용한다.
- DB 접속 설정은 `config.get_db_config()` 하나로 통일 — 다른 파트도 그대로 재사용 가능.
- MySQL이 준비되지 않은 환경에서는 정제 CSV로 자동 전환되어 발표 중 화면이 깨지지 않는다.

**팀 저장소와 파일명이 겹치는 것들** — 합칠 때 아래 3개만 조율하면 된다. 나머지는 이름이 겹치지 않는다.

| 파일 | 조율 방법 |
|---|---|
| `main.py` | 팀 라우터를 기준으로 삼고, 이쪽 `RENDERERS`의 `faq`·`news` 항목만 옮긴다 |
| `style/style.css` | 공통 스타일이라 양쪽 내용을 합친다. 페이지 전용은 `faq.css`·`news.css`에 있어 충돌하지 않는다 |
| `db/` | 팀은 `db/db.py`, 이쪽은 `db/repository.py`로 파일명이 달라 그대로 공존한다 |

`필수산출물/`이 필요 없으면 **폴더째 삭제**한다. 본 앱은 이 폴더를 참조하지 않는다.

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

- 초기 목업 `streamlit_app.py`(루트)는 기획 확정 이전에 만든 것으로, 현재 기획(4개 메뉴)과
  구성이 달라 제거했다. 그중 부트캠프 제출용 화면 3종(DB설계·수집데이터·프로젝트소개)만
  [`필수산출물/`](필수산출물/)로 옮겨 살렸다. 나머지(보조기구·지원정책 화면)는
  기획에서 빠진 내용이라 함께 정리했으며, 필요하면 커밋 `c875722`에서 되살릴 수 있다.
- 구조 개편 전 코드는 커밋 `a9b3d4a`의 `app/main_app.py`·`app/faq_page.py`에 있다.
  개편은 **동작 변경 없이 파일 분리만** 했고, 홈·FAQ 화면은 렌더링 결과가 개편 전과 동일함을
  Streamlit `AppTest`로 대조 확인했다.
