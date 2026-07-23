# 장애인콜택시 집계 CSV → MySQL 적재

## 0. 사전 확인

DBeaver에서 아래 테이블 7개가 생성되어 있어야 합니다.

- district
- district_daily_stat
- weekday_hour_stat
- od_flow_stat
- purpose_stat
- disability_vehicle_stat
- data_quality_log

## 1. DBeaver에서 지역 테이블 확장

`02_expand_district_table.sql`을 DBeaver에서 열어 전체 실행합니다.

원본에는 김포시 등 서울 밖 출발지역도 있으므로, 서울 여부와 지역 유형을 함께 저장하기 위한 수정입니다.

## 2. 파일을 프로젝트 폴더에 배치

아래 파일을 `C:\Users\tommy\sk-encore`에 넣습니다.

- `load_taxi_aggregates.py`
- `.env.example`

`.env.example`은 파일명을 `.env`로 변경합니다.

최종 구조 예시:

```text
C:\Users\tommy\sk-encore
├─ load_taxi_aggregates.py
├─ .env
└─ taxi_processed
   ├─ district_daily_stat.csv
   ├─ weekday_hour_stat.csv
   ├─ od_flow_stat.csv
   ├─ purpose_stat.csv
   └─ disability_vehicle_stat.csv
```

## 3. .env 설정

```env
DB_HOST=localhost
DB_PORT=3306
DB_NAME=seoul_mobility_db
DB_USER=root
DB_PASSWORD=본인의_MySQL_비밀번호
```

`.env` 파일은 GitHub에 올리지 않습니다.

`.gitignore`에 다음을 추가합니다.

```text
.env
taxi_processed/
서울시설공단_장애인콜택시 탑승내역_20251231.csv
```

## 4. 패키지 설치

```powershell
cd C:\Users\tommy\sk-encore
uv add pymysql python-dotenv
```

`pandas`가 없다면 함께 설치합니다.

```powershell
uv add pandas pymysql python-dotenv
```

## 5. 적재 실행

```powershell
uv run python .\load_taxi_aggregates.py --input-dir ".\taxi_processed"
```

정상 실행 예시:

```text
지역 기준정보 준비 완료: CSV 내 고유 지역 00개
기존 집계 테이블 데이터 삭제 완료
district_daily_stat: 12,868행 적재 완료
weekday_hour_stat: 168행 적재 완료
od_flow_stat: 2,101행 적재 완료
purpose_stat: 17행 적재 완료
disability_vehicle_stat: 36행 적재 완료
```

## 6. DBeaver 검증 쿼리

```sql
USE seoul_mobility_db;

SELECT COUNT(*) FROM district_daily_stat;
SELECT COUNT(*) FROM weekday_hour_stat;
SELECT COUNT(*) FROM od_flow_stat;
SELECT COUNT(*) FROM purpose_stat;
SELECT COUNT(*) FROM disability_vehicle_stat;
```

예상 결과:

- district_daily_stat: 12,868
- weekday_hour_stat: 168
- od_flow_stat: 2,101
- purpose_stat: 17
- disability_vehicle_stat: 36

## 7. 분석 쿼리 예시

### 자치구별 완료 운행 수

```sql
SELECT
    d.district_name,
    SUM(s.trip_count) AS total_trips
FROM district_daily_stat s
JOIN district d
    ON s.origin_district_id = d.district_id
WHERE d.is_seoul = 1
GROUP BY d.district_id, d.district_name
ORDER BY total_trips DESC;
```

### 시간대별 운행 수

```sql
SELECT
    hour_of_day,
    SUM(trip_count) AS total_trips
FROM weekday_hour_stat
GROUP BY hour_of_day
ORDER BY hour_of_day;
```

### 출발지-목적지 상위 이동 경로

```sql
SELECT
    origin.district_name AS origin_name,
    flow.destination_name,
    flow.trip_count
FROM od_flow_stat flow
JOIN district origin
    ON flow.origin_district_id = origin.district_id
WHERE origin.is_seoul = 1
ORDER BY flow.trip_count DESC
LIMIT 20;
```
