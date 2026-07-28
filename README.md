# 햬치타GO

> 서울시 장애인콜택시 이용현황 분석 및 조회 시스템

## 프로젝트 소개

서울시 장애인콜택시 관련 공공데이터를 분석·조회하고, 실제 이용(예약 준비, FAQ 확인, 관련 정보 파악)에 실질적으로 도움을 주는 시스템입니다. 장애인 당사자와 보호자가 접근성 높게 이용할 수 있도록, 큰 버튼과 직관적인 메뉴 구성으로 설계했습니다.

## 팀 소개
| 이름 | 역할 |
|---|---|
| 최우석 | PM(팀장) / 코드 검토 및 취합 / 배포 테스트 |
| 박수휘 | Git 형상관리 / Streamlit 시각화 구현 |
| 심성욱 | 데이터 크롤링 / 수집 데이터 정제 / 발표 |
| 이세희 | 데이터 크롤링 / Streamlit UI 설계 및 구현 |
| 이형밍 | API 데이터 정제 / 데이터베이스 스키마 설계 |

## 시스템 구성도
![시스템 구성도](./docs/system_architecture)

## 화면 구성

메인 화면 하단에 4개의 대형 메뉴 버튼을 배치했습니다.

| 메뉴 | 설명 |
|---|---|
| **이용현황** | 서울시 25개 자치구 지도 클릭 조회, 시간대별 예약 빈도 통계, 혼잡도 추이 |
| **예약하기** | 예약 전 체크리스트 입력 → 요약 정보 생성 → 전화/문자/인터넷접수 안내, 실시간 혼잡 시간대 안내문구 |
| **FAQ** | 서울시설공단 공식 안내(가입/이용기준/접수방법) 기반 Q&A |
| **관련뉴스** | 네이버뉴스 "장애인콜택시" 검색결과 크롤링 |

## 기술 스택

| 구분 | 기술 |
|---|---|
| 언어 | Python (uv 패키지 매니저) |
| 데이터 수집 | BeautifulSoup |
| 데이터베이스 | MySQL |
| 프론트엔드 | Streamlit, streamlit-folium, Altair |
| 배포 | Streamlit Community Cloud, TiDB |

## 폴더 구조

```
SKN35-1ST-1TEAM/
│  .env
│  .env.example
│  .gitignore
│  .python-version
│  config.py                    
│  main.py                      # 진입점, 페이지 라우팅
│  pyproject.toml               # uv 설정 정보
│  README.md
│  uv.lock
│  
├─.streamlit
│      config.toml              # 테마 설정 (색상, 폰트)
│      
├─common                        # 공용 유틸 함수
│  │  assets.py
│  │  brand.py
│  │  layout.py
│  │  news_data.py
│  │  styles.py
│  └─ text.py
│          
├─crawler                       # 데이터 수집 모듈
│      common.py
│      faq_board_bs4.py
│      faq_board_selenium.py
│      guide_pages_bs4.py
│      뉴스크롤링.ipynb
│      
├─data
│  │  seoul_gu_boundary.json    # 서울 25개 자치구 경계 GeoJSON
│  │  
│  ├─processed                  # 전처리 데이터
│  │      disability_news_20260727_165559.csv
│  │      faq_clean.csv
│  │      faq_keyword_clean.csv
│  │      faq_source_clean.csv
│  │      quality_report.json
│  │      
│  └─raw                        # 수집 데이터
│          faq_board_raw.json
│          faq_board_selenium.json
│          faq_guide_raw.json
│          
├─db                            # DB 연결 및 조회 함수
│  │  db.py
│  │  loader.py
│  │  repository.py
│  └─ schema.sql
│          
├─docs
│      system_architecture.png  # 시스템 아키텍쳐
│      
├─preprocess                    # 전처리 코드 (faq)
│      build_faq_dataset.py
│      
├─style                         # 화면 css 스타일
│      faq.css
│      home.css
│      news.css
│      style.css
│      useStatus.css
│      
├─views                         # 메뉴별 화면 페이지
│  │  faq.py
│  │  home.py
│  │  news.py
│  │  placeholder.py
│  │  reserve.py
│  └─ useStatus.py
```
## 데이터 출처

| 데이터 | 출처 | 형태 |
|---|---|---|
| 탑승내역 (2023~2025) | 공공데이터포털 (서울시설공단) | CSV |
| 서울 자치구 경계 GeoJSON | GitHub (southkorea/seoul-maps) | JSON |
| FAQ | 서울시설공단 장애인콜택시 공식 홈페이지 | CSV |
| 관련뉴스 | 네이버뉴스 검색결과 | 웹크롤링 |

## ERD
-

## 실행 방법

```bash
# 1. pyproject.toml 패키지 의존성 설치
uv pip install -r pyproject.toml

# 2. 실행
uv run streamlit run main.py
```