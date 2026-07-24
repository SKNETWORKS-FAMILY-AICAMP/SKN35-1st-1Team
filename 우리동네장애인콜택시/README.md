# 우리동네 장애인 콜택시

서울시 장애인콜택시 이용현황 분석 및 조회 시스템

> ⚠️ **본 서비스는 서울시설공단의 공식 예약·배차 시스템이 아닙니다.**
> 입력한 예약 내용을 정리하고 과거 이용 통계를 기반으로 참고 정보를 제공합니다.
> 실제 예약/배차는 반드시 공식 채널(전화, 공식 홈페이지, 공식 앱)을 이용해 주세요.

## 프로젝트 소개 / 서비스 목적

서울시 장애인콜택시의 과거 이용 데이터를 분석하여, 사용자가 지역별·시간대별
이용현황을 확인하고 실제 예약 전에 필요한 정보를 정리할 수 있도록 돕는
Streamlit 기반 데이터 분석/조회 서비스입니다. 실제 예약·배차 기능은 제공하지
않으며, 통계와 참고 정보 제공에 목적을 한정합니다.

## 주요 사용자

- 장애인 당사자
- 장애인 보호자

## 주요 기능

1. **이용현황**: 기간·자치구·요일·시간대·이용목적·차량구분 필터, KPI 카드, 지도/차트 9종, 자치구 상세정보
2. **예약하기(예약 준비 도우미)**: 예약 정보 요약, 문자 접수용 문장 생성, 과거 데이터 기반 혼잡도 안내, 공식 채널 연결
3. **FAQ**: 공식 홈페이지 기반 자주 묻는 질문(카테고리/키워드 검색, 아코디언 UI)
4. **관련뉴스**: 네이버 뉴스 검색 API 기반 관련 뉴스 모아보기

## 화면 구성

```
app.py                      메인 화면(4대 메뉴 버튼)
pages/1_이용현황.py          필터 + KPI + 시각화 9종 + 자치구 상세정보
pages/2_예약하기.py          예약 준비 도우미(개인정보 비저장)
pages/3_FAQ.py              FAQ 조회(DB 기반, 실행 중 크롤링 없음)
pages/4_관련뉴스.py          관련뉴스 조회(네이버 뉴스 검색 API)
```

## 데이터 출처

- 서울시 장애인콜택시 이용 이력 원본 데이터 (원본 CSV, 팀에서 별도 입수/전처리하여 `data/raw/`에 배치)
- 서울시설공단 장애인콜택시 공식 홈페이지: <https://www.sisul.or.kr/open_content/calltaxi/> (FAQ)
- 네이버 뉴스 검색 API: <https://developers.naver.com> (관련뉴스)

원본 데이터가 아직 없는 개발 단계에서는 `scripts/generate_sample_data.py`가
생성하는 더미 데이터(`data/sample/dummy_taxi_raw.csv`)로 전체 파이프라인을
검증할 수 있습니다. **더미 데이터는 실제 데이터가 아니며 `data/sample/`에만
저장되고, 실제 DB에 자동 삽입되지 않습니다.**

## 데이터 컬럼 설명 (원본 → 정제 컬럼명)

| 원본 컬럼 | 정제 컬럼 | 비고 |
|---|---|---|
| 접수일시 | `request_at` | |
| 예정일시 | `scheduled_at` | |
| 배차일시 | `dispatch_at` | |
| 승차일시 | `pickup_at` | |
| 하차일시 | `dropoff_at` | |
| 취소일시 | `cancel_at` | |
| 출발구 | `origin_district_raw` → `origin_district` | 원본 보존 + 표준 25개 자치구명으로 정규화 |
| 출발동 | `origin_dong` | |
| 목적구 | `destination_district_raw` → `destination_district` | 원본 보존 + 정규화 |
| 목적동 | `destination_dong` | |
| 이용목적 | `purpose_raw` → `purpose_group` | 원본 보존 + 그룹 단순화 |
| 요금 | `fare` | |
| 승차거리 | `distance` | |
| 차량구분 | `vehicle_type_raw` → `vehicle_type_group` | 원본 보존 + 그룹 단순화 |
| 장애유형 | `disability_type_raw` → `disability_type_group` | 원본 보존 + 그룹 단순화 |

날짜 파생 컬럼: `request_date`, `request_year`, `request_month`, `request_day`,
`request_hour`, `weekday_num`(0=월요일~6=일요일), `weekday_name`, `is_weekend`, `time_group`

상태값(`status`): `requested` → `dispatched` → `boarded` → `completed`, 그리고 `cancelled`
(취소일시 존재 시 최우선으로 `cancelled` 처리)

## 전처리 과정

```
원본 CSV(data/raw) --chunksize 읽기--> 컬럼명 변경 --> 날짜 파싱(실패시 NaT)
  --> 자치구명 정규화(실패시 결측, 강제매핑 금지) --> 범주 그룹핑
  --> 상태값 분류 --> 대기시간 계산 --> 이상치 플래그(삭제하지 않음)
  --> data/processed/taxi_processed.parquet 저장
  --> data/rejected/*.csv (이상치·미매핑 자치구 별도 보존)
  --> data/processed/data_quality_summary.csv, processing_summary.json
```

## 대기시간 정의

- **배차 대기시간** = 배차일시 − 접수일시
- **승차 대기시간** = 승차일시 − 접수일시
- **탑승 준비시간** = 승차일시 − 배차일시
- **이동시간** = 하차일시 − 승차일시

모든 값은 분 단위로 계산하며, 화면에는 "평균 대기시간"처럼 뭉뚱그리지 않고
반드시 위 4가지 중 구체적인 명칭을 사용합니다.

## 혼잡도 계산 기준

과거 접수 건수의 분위수를 기준으로 4단계로 분류합니다.

| 분위수 | 등급 |
|---|---|
| 하위 30% | 🟢 비교적 여유 |
| 30% 이상 70% 미만 | 🟡 보통 |
| 70% 이상 90% 미만 | 🟠 다소 혼잡 |
| 상위 10% | 🔴 혼잡 |

예약 준비 도우미는 조건이 일치하는 표본이 부족(5건 미만)하면 아래 순서로
범위를 넓혀 통계를 조회하며, 어떤 기준을 사용했는지 화면에 표시합니다.

1. 출발 자치구 + 요일 + 시간
2. 출발 자치구 + 시간(요일 무관)
3. 요일 + 시간(자치구 무관)
4. 전체 시간(가장 넓은 범위)

## DB 구조

`area`, `district_daily_stat`, `district_hourly_stat`, `weekday_hour_stat`,
`monthly_stat`, `od_flow_stat`, `purpose_stat`, `disability_vehicle_stat`,
`faq`, `news`, `data_collection_log`, `data_quality_summary`

전체 DDL은 [`sql/schema.sql`](sql/schema.sql), 추가 인덱스는 [`sql/indexes.sql`](sql/indexes.sql),
예시 쿼리는 [`sql/sample_queries.sql`](sql/sample_queries.sql)을 참고하세요.
모든 테이블은 `CREATE TABLE IF NOT EXISTS`로 생성되어 기존 테이블을 DROP하지 않습니다.
원본 이용 이력 전체는 DB에 적재하지 않고(원본 CSV → `data/raw`, 정제 데이터 →
Parquet, 분석 집계만 → MySQL), Streamlit은 MySQL 집계 테이블만 조회합니다.

## 프로젝트 폴더 구조

```
app.py                      메인 화면
pages/                      Streamlit 멀티페이지
components/                 헤더, 내비게이션, KPI 카드, 접근성 CSS, 안내문구
services/                   DB 연결, 비즈니스 로직(혼잡도 계산 등)
repositories/                DB 조회 전담 계층(SQL은 여기에만 작성)
collectors/                  FAQ/뉴스 수집 스크립트(Streamlit 실행 중 호출되지 않음)
preprocessing/                원본 데이터 전처리·집계 생성
scripts/                     테이블 생성, 집계 적재, 더미데이터 생성 CLI
sql/                          DDL, 인덱스, 예시 쿼리
tests/                        pytest
assets/                       styles.css(선택적 최소 커스텀 CSS)
data/{raw,external,processed,rejected,sample}/
.streamlit/config.toml
config.py, districts.py, congestion.py   최상위 공통 모듈(설정/자치구/혼잡도)
```

## 설치 방법

### uv 사용(권장)

```bash
uv sync
```

### pip 사용

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate

pip install -e .
```

## 환경변수 설정

`.env.example`을 복사해 `.env`를 만들고 값을 채워 넣습니다. `.env`는 Git에 커밋하지 않습니다.

```bash
# macOS/Linux
cp .env.example .env
```

```powershell
# Windows PowerShell
Copy-Item .env.example .env
```

필수 변수: `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`,
`NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET`, `FAQ_SOURCE_URL`,
`OFFICIAL_RESERVATION_URL`, `OFFICIAL_PHONE_NUMBER`, `OFFICIAL_SMS_NUMBER`.
DB 비밀번호에 한글/특수문자가 있어도 `config.py`의 `URL.create()`가 안전하게
인코딩하므로 별도 처리가 필요 없습니다. 네이버 API 키가 없어도 앱은 정상
실행되며, 관련뉴스 페이지에 안내만 표시됩니다.

## MySQL 생성 방법

MySQL 서버가 켜져 있고 `.env`의 DB 접속정보가 올바른 상태에서 실행합니다.
`sql/schema.sql`은 `CREATE TABLE IF NOT EXISTS`로만 구성되어 있어 여러 번
실행해도 기존 테이블을 DROP하지 않습니다.

```bash
uv run python scripts/create_tables.py
```

## 전처리 실행 방법

```bash
# 더미 데이터 생성(실제 데이터가 없을 때, data/sample/에만 저장됨)
uv run python scripts/generate_sample_data.py

# 전처리(원본 CSV -> data/processed/taxi_processed.parquet)
uv run python preprocessing/clean_taxi_data.py --input data/sample/dummy_taxi_raw.csv
# 실제 데이터가 준비되면:
# uv run python preprocessing/clean_taxi_data.py --input data/raw/<실제파일명>.csv
```

## 집계 생성 방법

```bash
uv run python preprocessing/build_aggregates.py
```

## DB 적재 방법

```bash
uv run python scripts/load_aggregates.py
```

UNIQUE KEY 기준 `INSERT ... ON DUPLICATE KEY UPDATE`로 재실행해도 중복
적재되지 않으며, 테이블 단위 트랜잭션으로 처리되어 실패 시 해당 테이블만 롤백됩니다.

## FAQ 수집 방법

```bash
uv run python collectors/collect_faq.py
```

Streamlit 실행 중에는 크롤링하지 않습니다. 수집 결과가 0건이면 기존 FAQ
데이터를 그대로 유지합니다.

## 뉴스 수집 방법

```bash
uv run python collectors/collect_news.py
```

`NAVER_CLIENT_ID`/`NAVER_CLIENT_SECRET`이 없으면 조용히 건너뜁니다(앱 실행에는 영향 없음).

## Streamlit 실행 방법

```bash
uv run streamlit run app.py
```

## 테스트 실행 방법

```bash
uv run pytest
```

DB/네이버 API 연결 없이도 전체 테스트가 통과하도록 설계되어 있습니다
(DB/외부 API 호출부는 monkeypatch로 대체).

## 개인정보 비저장 원칙

예약하기(예약 준비 도우미) 페이지에서 입력받는 **연락처, 출발 상세 위치,
목적 상세 위치**는 어떤 형태로도 DB/CSV/파일/로그/캐시에 저장하지 않습니다.
`st.cache_data`/`st.cache_resource`는 이 페이지에서 전혀 사용하지 않으며,
`tests/test_reservation_privacy.py`가 이를 정적으로 검증합니다.

## 서비스 한계 / 실제 예약 시스템이 아니라는 안내

- 본 서비스는 **서울시설공단의 공식 예약·배차 시스템이 아닙니다.** 실제 배차,
  탑승 확정, 취소 접수는 처리하지 않습니다.
- 혼잡도/대기시간 안내는 과거 통계 기반 참고 정보이며, 실제 대기시간을
  예측·보장하지 않습니다. 실제 대기시간은 당일 차량 운영 상황에 따라 달라집니다.
- 표본이 매우 적은 장애유형×차량구분 조합은 화면에 개별 노출하지 않고
  '기타(소규모)'로 묶어 표시합니다.
- FAQ의 이용 기준/요금 등은 변경될 수 있으므로 실제 이용 전 공식 홈페이지에서
  다시 확인해야 합니다.
- 실제 예약은 반드시 공식 전화(`.env`의 `OFFICIAL_PHONE_NUMBER`), 공식
  홈페이지(`OFFICIAL_RESERVATION_URL`) 또는 공식 앱을 이용해 주세요.
