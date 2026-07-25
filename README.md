# SKN35-1st-1Team

# 🚕 우리동네 장애인 콜택시

서울시 장애인콜택시 이용현황 분석 및 조회 시스템

> SK Networks Family AI Camp 1차 팀 프로젝트 (5인)

---

## 📌 프로젝트 소개

서울시 장애인콜택시 관련 공공데이터를 분석·조회하고, 실제 이용(예약 준비, FAQ 확인, 관련 정보 파악)에 실질적으로 도움을 주는 시스템입니다. 장애인 당사자와 보호자가 접근성 높게 이용할 수 있도록, 큰 버튼과 직관적인 메뉴 구성으로 설계했습니다.

## 🖥️ 화면 구성

메인 화면 하단에 4개의 대형 메뉴 버튼을 배치했습니다.

| 메뉴 | 설명 |
|---|---|
| **이용현황** | 서울시 25개 자치구 지도 클릭 조회, 시간대별 예약 빈도 통계, 혼잡도 추이 |
| **예약하기** | 예약 전 체크리스트 입력 → 요약 정보 생성 → 전화/문자/인터넷접수 안내, 실시간 혼잡 시간대 안내문구 |
| **FAQ** | 서울시설공단 공식 안내(가입/이용기준/접수방법) 기반 Q&A |
| **관련뉴스** | 네이버뉴스 "장애인콜택시" 검색결과 크롤링 |

## 🛠 기술 스택

| 구분 | 기술 |
|---|---|
| 언어 | Python (uv 패키지 매니저) |
| 데이터 수집 | BeautifulSoup |
| 데이터베이스 | - |
| DB 연동 | - |
| 프론트엔드 | Streamlit, streamlit-folium, Altair |
| 배포 | Streamlit Community Cloud |

## 📂 폴더 구조

```
projects/                # 레포 루트
├── .streamlit/
│   └── config.toml          # 테마 설정 (색상, 폰트)
├── data/
│   └── seoul_gu_boundary.json  # 서울 25개 자치구 경계 GeoJSON
├── views/                   # 페이지별 화면 코드
│   ├── __init__.py
│   ├── useStatus.py         # 이용현황 페이지
│   └── reserve.py           # 예약하기 페이지
├── common/                  # 공용 유틸 함수 (크롤링 등)
├── db/                      # DB 연결 및 조회 함수
├── style/
│   └── style.css            # 공용 스타일시트 (최소 커스텀 CSS)
├── main.py                  # 진입점, 페이지 라우팅
├── .gitignore
├── .python-version
├── pyproject.toml
├── README.md
└── uv.lock
```

## 🗃 데이터 출처

| 데이터 | 출처 | 형태 |
|---|---|---|
| 탑승내역 (2023~2025) | 공공데이터포털 (서울시설공단) | CSV |
| 서울 자치구 경계 GeoJSON | GitHub (southkorea/seoul-maps) | JSON |
| FAQ | - | - |
| 관련뉴스 | 네이버뉴스 검색결과 | 웹크롤링 |

## ERD


## 실행 방법

```bash
# 1. 레포 루트(project01_car)에서 의존성 설치
uv add streamlit folium streamlit-folium altair

# 2. 실행
uv run streamlit run main.py
```


## 역할 분담

| 역할 | 담당 영역 |
|---|---|
