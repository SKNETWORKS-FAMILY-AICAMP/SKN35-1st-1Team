-- =====================================================================
-- 우리동네 장애인 콜택시 - MySQL 스키마
-- 원칙: 기존 테이블을 무조건 DROP하지 않는다. 모든 테이블은
--       CREATE TABLE IF NOT EXISTS 로 생성하며, 스키마 변경이 필요하면
--       scripts/create_tables.py 가 기존 컬럼을 먼저 확인한 뒤
--       ALTER TABLE 마이그레이션을 수행한다.
-- 문자셋: utf8mb4 (한글 + 이모지 등 완전 지원)
-- =====================================================================

CREATE TABLE IF NOT EXISTS area (
    district_id   VARCHAR(10)  NOT NULL COMMENT '서울 25개 자치구 표준명(예: 강남구)',
    district_name VARCHAR(20)  NOT NULL,
    sido          VARCHAR(20)  NOT NULL DEFAULT '서울특별시',
    latitude      DECIMAL(9,6) NULL,
    longitude     DECIMAL(9,6) NULL,
    created_at    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (district_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 일자 x 자치구 집계 (이용현황 페이지의 기간별 추이/월별 추이의 기반)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS district_daily_stat (
    id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    stat_date               DATE            NOT NULL,
    district_id             VARCHAR(10)     NOT NULL,
    request_count           INT             NOT NULL DEFAULT 0 COMMENT '전체 접수 건수',
    dispatch_count          INT             NOT NULL DEFAULT 0 COMMENT '배차 건수',
    ride_count              INT             NOT NULL DEFAULT 0 COMMENT '실제 승차(이용) 건수',
    completed_count         INT             NOT NULL DEFAULT 0 COMMENT '완료 건수',
    cancel_count            INT             NOT NULL DEFAULT 0 COMMENT '취소 건수',
    cancel_rate             DECIMAL(5,2)    NULL COMMENT '취소율(%)',
    avg_dispatch_wait_min   DECIMAL(8,2)    NULL COMMENT '평균 배차 대기시간(분) = 배차일시-접수일시',
    median_dispatch_wait_min DECIMAL(8,2)   NULL,
    p75_dispatch_wait_min   DECIMAL(8,2)    NULL,
    p90_dispatch_wait_min   DECIMAL(8,2)    NULL,
    avg_pickup_wait_min     DECIMAL(8,2)    NULL COMMENT '평균 승차 대기시간(분) = 승차일시-접수일시',
    median_pickup_wait_min  DECIMAL(8,2)    NULL,
    avg_distance            DECIMAL(8,2)    NULL,
    avg_fare                DECIMAL(10,2)   NULL,
    valid_wait_count        INT             NOT NULL DEFAULT 0 COMMENT '대기시간 계산에 사용된 정상 표본 수',
    PRIMARY KEY (id),
    UNIQUE KEY uq_daily (stat_date, district_id),
    KEY idx_daily_date (stat_date),
    KEY idx_daily_district (district_id),
    CONSTRAINT fk_daily_district FOREIGN KEY (district_id) REFERENCES area(district_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 자치구 x 요일 x 시간대 집계 (예약 준비 도우미의 핵심 테이블: 혼잡도 조회)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS district_hourly_stat (
    id                       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    district_id              VARCHAR(10)     NOT NULL,
    weekday_num              TINYINT         NOT NULL COMMENT '0=월 ... 6=일',
    request_hour             TINYINT         NOT NULL COMMENT '0~23시',
    request_count            INT             NOT NULL DEFAULT 0,
    ride_count                INT             NOT NULL DEFAULT 0,
    completed_count          INT             NOT NULL DEFAULT 0,
    cancel_count             INT             NOT NULL DEFAULT 0,
    cancel_rate              DECIMAL(5,2)    NULL,
    avg_dispatch_wait_min    DECIMAL(8,2)    NULL,
    median_dispatch_wait_min DECIMAL(8,2)    NULL,
    avg_pickup_wait_min      DECIMAL(8,2)    NULL,
    median_pickup_wait_min   DECIMAL(8,2)    NULL,
    congestion_percentile    DECIMAL(5,2)    NULL COMMENT '접수건수 기준 분위수(0~100)',
    congestion_level         VARCHAR(10)     NULL COMMENT '여유/보통/다소혼잡/혼잡',
    valid_wait_count         INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (id),
    UNIQUE KEY uq_hourly (district_id, weekday_num, request_hour),
    KEY idx_hourly_weekday_hour (weekday_num, request_hour),
    CONSTRAINT fk_hourly_district FOREIGN KEY (district_id) REFERENCES area(district_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 요일 x 시간대 전체 집계 (자치구 무관, 혼잡도 대체조회 3단계에서 사용)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weekday_hour_stat (
    id                       BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    weekday_num              TINYINT         NOT NULL,
    request_hour             TINYINT         NOT NULL,
    request_count            INT             NOT NULL DEFAULT 0,
    ride_count               INT             NOT NULL DEFAULT 0,
    cancel_count             INT             NOT NULL DEFAULT 0,
    avg_dispatch_wait_min    DECIMAL(8,2)    NULL,
    median_dispatch_wait_min DECIMAL(8,2)    NULL,
    congestion_percentile    DECIMAL(5,2)    NULL,
    congestion_level         VARCHAR(10)     NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_weekday_hour (weekday_num, request_hour)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 월별 집계 (연도-월 추이)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS monthly_stat (
    id                     BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    year                   SMALLINT        NOT NULL,
    month                  TINYINT         NOT NULL,
    request_count          INT             NOT NULL DEFAULT 0,
    ride_count             INT             NOT NULL DEFAULT 0,
    completed_count        INT             NOT NULL DEFAULT 0,
    cancel_count           INT             NOT NULL DEFAULT 0,
    cancel_rate            DECIMAL(5,2)    NULL,
    avg_dispatch_wait_min  DECIMAL(8,2)    NULL,
    median_dispatch_wait_min DECIMAL(8,2)  NULL,
    avg_pickup_wait_min    DECIMAL(8,2)    NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_month (year, month)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 출발구 -> 목적구 이동 경로 집계
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS od_flow_stat (
    id                      BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    origin_district_id      VARCHAR(10)     NOT NULL,
    destination_district_id VARCHAR(10)     NOT NULL,
    request_count           INT             NOT NULL DEFAULT 0,
    ride_count              INT             NOT NULL DEFAULT 0,
    avg_distance            DECIMAL(8,2)    NULL,
    avg_fare                DECIMAL(10,2)   NULL,
    avg_trip_duration_min   DECIMAL(8,2)    NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_od (origin_district_id, destination_district_id),
    KEY idx_od_origin (origin_district_id),
    KEY idx_od_destination (destination_district_id),
    CONSTRAINT fk_od_origin FOREIGN KEY (origin_district_id) REFERENCES area(district_id),
    CONSTRAINT fk_od_destination FOREIGN KEY (destination_district_id) REFERENCES area(district_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 이용 목적별 집계
-- district_id = 'ALL' 은 서울 전체(자치구 무관) 집계 행이다. 자치구 상세정보 화면의
-- "가장 많이 사용한 이용 목적" 표시를 위해 자치구별 행도 함께 저장한다.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS purpose_stat (
    id             BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    district_id    VARCHAR(10)     NOT NULL DEFAULT 'ALL',
    purpose_group  VARCHAR(30)     NOT NULL,
    request_count  INT             NOT NULL DEFAULT 0,
    ride_count     INT             NOT NULL DEFAULT 0,
    percentage     DECIMAL(5,2)    NULL,
    avg_distance   DECIMAL(8,2)    NULL,
    avg_fare       DECIMAL(10,2)   NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_purpose (district_id, purpose_group)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 장애유형 x 차량구분 집계 (표본이 적은 조합은 서비스 계층에서 '기타'로 묶어 노출 제한)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS disability_vehicle_stat (
    id              BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    disability_type VARCHAR(30)     NOT NULL,
    vehicle_type    VARCHAR(30)     NOT NULL,
    ride_count      INT             NOT NULL DEFAULT 0,
    percentage      DECIMAL(5,2)    NULL,
    PRIMARY KEY (id),
    UNIQUE KEY uq_disability_vehicle (disability_type, vehicle_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- FAQ (공식 홈페이지 수집 결과. Streamlit 실행 중에는 크롤링하지 않고 여기서 조회만 한다)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faq (
    faq_id         BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    category       VARCHAR(30)     NOT NULL,
    question       VARCHAR(255)    NOT NULL,
    answer         TEXT            NOT NULL,
    source_url     VARCHAR(500)    NULL,
    source_name    VARCHAR(100)    NULL,
    collected_at   DATETIME        NULL,
    updated_at     DATETIME        NULL,
    display_order  INT             NOT NULL DEFAULT 0,
    is_active      TINYINT(1)      NOT NULL DEFAULT 1,
    PRIMARY KEY (faq_id),
    KEY idx_faq_category (category),
    KEY idx_faq_active_order (is_active, display_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 관련뉴스 (네이버 뉴스 검색 API 수집 결과)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS news (
    news_id        BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    title          VARCHAR(500)    NOT NULL,
    description    TEXT            NULL,
    publisher      VARCHAR(100)    NULL,
    published_at   DATETIME        NULL,
    original_url   VARCHAR(500)    NULL,
    naver_url      VARCHAR(500)    NULL,
    search_keyword VARCHAR(100)    NULL,
    collected_at   DATETIME        NULL,
    title_hash     CHAR(64)        NOT NULL COMMENT '정규화된 제목의 SHA-256 해시 (중복 제거 기준)',
    is_active      TINYINT(1)      NOT NULL DEFAULT 1,
    PRIMARY KEY (news_id),
    UNIQUE KEY uq_news_title_hash (title_hash),
    KEY idx_news_published_at (published_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 데이터 수집/적재 작업 로그 (FAQ 수집, 뉴스 수집, 집계 적재 등)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_collection_log (
    log_id          BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    job_name        VARCHAR(50)     NOT NULL COMMENT 'faq_collect / news_collect / aggregate_load 등',
    status          VARCHAR(20)     NOT NULL COMMENT 'success / failed / partial',
    message         VARCHAR(500)    NULL,
    collected_count INT             NOT NULL DEFAULT 0,
    started_at      DATETIME        NOT NULL,
    finished_at     DATETIME        NULL,
    PRIMARY KEY (log_id),
    KEY idx_log_job (job_name, started_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- 전처리 단계에서 생성된 데이터 품질 보고서의 DB 기록본
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_summary (
    summary_id                   BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    run_at                       DATETIME        NOT NULL,
    total_rows                   INT             NOT NULL DEFAULT 0,
    valid_rows                   INT             NOT NULL DEFAULT 0,
    date_parse_fail_rows         INT             NOT NULL DEFAULT 0,
    district_mapping_fail_rows   INT             NOT NULL DEFAULT 0,
    negative_time_rows           INT             NOT NULL DEFAULT 0,
    abnormal_wait_rows           INT             NOT NULL DEFAULT 0,
    duplicate_rows               INT             NOT NULL DEFAULT 0,
    request_count                INT             NOT NULL DEFAULT 0,
    dispatch_count                INT            NOT NULL DEFAULT 0,
    ride_count                   INT             NOT NULL DEFAULT 0,
    completed_count              INT             NOT NULL DEFAULT 0,
    cancel_count                 INT             NOT NULL DEFAULT 0,
    PRIMARY KEY (summary_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ---------------------------------------------------------------------
-- (선택) 원본 이용 데이터 전체를 DB에 적재해야 하는 요구사항이 추가될 경우에만 사용.
-- 기본 방침: 원본 CSV는 data/raw, 정제 데이터는 Parquet(data/processed), MySQL은 집계만 저장.
-- ---------------------------------------------------------------------
-- CREATE TABLE IF NOT EXISTS taxi_trip (
--     trip_id                BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
--     request_at             DATETIME NULL,
--     scheduled_at           DATETIME NULL,
--     dispatch_at            DATETIME NULL,
--     pickup_at              DATETIME NULL,
--     dropoff_at             DATETIME NULL,
--     cancel_at              DATETIME NULL,
--     origin_district        VARCHAR(10) NULL,
--     origin_dong             VARCHAR(30) NULL,
--     destination_district    VARCHAR(10) NULL,
--     destination_dong        VARCHAR(30) NULL,
--     purpose_group           VARCHAR(30) NULL,
--     fare                    DECIMAL(10,2) NULL,
--     distance                DECIMAL(8,2) NULL,
--     vehicle_type_group      VARCHAR(30) NULL,
--     disability_type_group   VARCHAR(30) NULL,
--     status                  VARCHAR(20) NULL,
--     PRIMARY KEY (trip_id)
-- ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
