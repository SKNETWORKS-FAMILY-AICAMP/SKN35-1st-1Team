# 서울 장애인콜택시 1차 전처리

## 1. 설치

PowerShell에서 프로젝트 폴더로 이동한 뒤 실행합니다.

```powershell
uv add pandas numpy
```

## 2. 실행

```powershell
uv run python taxi_etl_stage1.py `
  "C:\Users\tommy\sk-encore\서울시설공단_장애인콜택시_탑승내역_20251231.csv" `
  --output-dir "C:\Users\tommy\sk-encore\taxi_processed"
```

명령어를 한 줄로 작성해도 됩니다.

```powershell
uv run python taxi_etl_stage1.py "C:\Users\tommy\sk-encore\서울시설공단_장애인콜택시_탑승내역_20251231.csv" --output-dir "C:\Users\tommy\sk-encore\taxi_processed"
```

## 3. 생성되는 파일

- `district_daily_stat.csv`: 기준일·출발구별 운행 통계
- `weekday_hour_stat.csv`: 요일·시간대별 통계
- `od_flow_stat.csv`: 출발구·목적구 이동량
- `purpose_stat.csv`: 이용목적별 통계
- `disability_vehicle_stat.csv`: 장애유형·차량구분별 통계
- `processing_summary.json`: 전체·완료·취소 건수와 이상값 요약

## 4. 시간 컬럼의 의미

- `접수후배차_분`: 배차일시 - 접수일시
- `예정대비승차_분`: 승차일시 - 예정일시
- `승차시간_분`: 하차일시 - 승차일시

예약 접수가 포함될 수 있기 때문에 `승차일시 - 접수일시`를 곧바로 대기시간으로 사용하지 않습니다.
