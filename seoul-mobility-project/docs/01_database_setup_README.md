# MySQL 데이터베이스 생성 순서

## 목표

이번 단계에서는 아래까지만 완료합니다.

1. `seoul_mobility_db` 데이터베이스 생성
2. 서울 25개 자치구 기준정보 생성
3. 장애인콜택시 집계용 테이블 생성
4. 데이터 품질 점검 결과 입력
5. 테이블 정상 생성 확인

아직 CSV는 넣지 않습니다.

## MySQL Workbench에서 실행

1. MySQL Workbench를 실행합니다.
2. `Local instance MySQL` 또는 기존 로컬 연결을 엽니다.
3. 비밀번호를 입력해 접속합니다.
4. 상단 메뉴에서 `File → Open SQL Script`를 선택합니다.
5. `01_create_seoul_mobility_db.sql` 파일을 엽니다.
6. 번개 모양 실행 버튼을 누릅니다.
7. 왼쪽 `SCHEMAS` 영역에서 새로고침 버튼을 누릅니다.
8. `seoul_mobility_db`가 나타나는지 확인합니다.

## 확인 쿼리

```sql
USE seoul_mobility_db;
SHOW TABLES;
SELECT * FROM district;
SELECT * FROM data_quality_log;
```

## 만들어지는 테이블

- `district`
- `district_daily_stat`
- `weekday_hour_stat`
- `od_flow_stat`
- `purpose_stat`
- `disability_vehicle_stat`
- `data_quality_log`

## 오류가 날 때

### MySQL 서버 접속 자체가 안 되는 경우

Windows 검색에서 `서비스`를 열고 `MySQL80` 또는 유사한 MySQL 서비스를 확인합니다.

### 권한 오류가 나는 경우

관리자 계정 또는 데이터베이스 생성 권한이 있는 계정으로 접속해야 합니다.

### 데이터베이스가 왼쪽에 안 보이는 경우

Workbench의 `SCHEMAS` 옆 새로고침 아이콘을 누릅니다.
