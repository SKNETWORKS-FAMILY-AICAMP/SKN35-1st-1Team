-- =========================================================
-- 서울 교통약자 이동지원 플랫폼
-- 1단계: 데이터베이스 및 집계 테이블 생성
-- =========================================================

-- 기존 DB가 있더라도 삭제하지 않습니다.
CREATE DATABASE IF NOT EXISTS seoul_mobility_db
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE seoul_mobility_db;

-- ---------------------------------------------------------
-- 1. 서울 자치구 기준정보
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS district (
    district_id INT AUTO_INCREMENT PRIMARY KEY,
    district_name VARCHAR(30) NOT NULL UNIQUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 서울 25개 자치구
INSERT IGNORE INTO district (district_name) VALUES
('강남구'), ('강동구'), ('강북구'), ('강서구'), ('관악구'),
('광진구'), ('구로구'), ('금천구'), ('노원구'), ('도봉구'),
('동대문구'), ('동작구'), ('마포구'), ('서대문구'), ('서초구'),
('성동구'), ('성북구'), ('송파구'), ('양천구'), ('영등포구'),
('용산구'), ('은평구'), ('종로구'), ('중구'), ('중랑구');

-- ---------------------------------------------------------
-- 공통 집계 컬럼 설명
-- trip_count                       완료 운행 건수
-- fare_sum / fare_count            요금 합계 / 유효 건수
-- distance_m_sum / distance_count  승차거리 합계(m) / 유효 건수
-- request_to_dispatch_*            접수 후 배차까지 시간
-- scheduled_to_pickup_*            예정시각 대비 실제 승차시간
-- ride_min_*                       실제 승차시간
-- ---------------------------------------------------------

-- ---------------------------------------------------------
-- 2. 날짜·출발 자치구별 집계
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS district_daily_stat (
    stat_date DATE NOT NULL,
    origin_district_id INT NOT NULL,

    trip_count INT UNSIGNED NOT NULL DEFAULT 0,

    fare_sum DECIMAL(18,2) NOT NULL DEFAULT 0,
    fare_count INT UNSIGNED NOT NULL DEFAULT 0,

    distance_m_sum DECIMAL(20,2) NOT NULL DEFAULT 0,
    distance_count INT UNSIGNED NOT NULL DEFAULT 0,

    request_to_dispatch_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    request_to_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0,

    scheduled_to_pickup_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    scheduled_to_pickup_count INT UNSIGNED NOT NULL DEFAULT 0,

    ride_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    ride_min_count INT UNSIGNED NOT NULL DEFAULT 0,

    avg_fare DECIMAL(12,2) NULL,
    avg_distance_m DECIMAL(14,2) NULL,
    avg_distance_km DECIMAL(12,3) NULL,
    avg_request_to_dispatch_min DECIMAL(12,3) NULL,
    avg_scheduled_to_pickup_min DECIMAL(12,3) NULL,
    avg_ride_min DECIMAL(12,3) NULL,

    total_record_count INT UNSIGNED NOT NULL DEFAULT 0,
    completed_count INT UNSIGNED NOT NULL DEFAULT 0,
    cancelled_count INT UNSIGNED NOT NULL DEFAULT 0,
    completion_rate DECIMAL(10,6) NULL,
    cancellation_rate DECIMAL(10,6) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (stat_date, origin_district_id),
    CONSTRAINT fk_daily_origin_district
        FOREIGN KEY (origin_district_id)
        REFERENCES district (district_id)
) ENGINE=InnoDB;

CREATE INDEX idx_daily_origin_district
    ON district_daily_stat (origin_district_id);

-- ---------------------------------------------------------
-- 3. 요일·시간대별 집계
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS weekday_hour_stat (
    weekday_number TINYINT UNSIGNED NOT NULL,
    weekday_name VARCHAR(10) NOT NULL,
    hour_of_day TINYINT UNSIGNED NOT NULL,

    trip_count INT UNSIGNED NOT NULL DEFAULT 0,

    fare_sum DECIMAL(18,2) NOT NULL DEFAULT 0,
    fare_count INT UNSIGNED NOT NULL DEFAULT 0,

    distance_m_sum DECIMAL(20,2) NOT NULL DEFAULT 0,
    distance_count INT UNSIGNED NOT NULL DEFAULT 0,

    request_to_dispatch_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    request_to_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0,

    scheduled_to_pickup_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    scheduled_to_pickup_count INT UNSIGNED NOT NULL DEFAULT 0,

    ride_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    ride_min_count INT UNSIGNED NOT NULL DEFAULT 0,

    avg_fare DECIMAL(12,2) NULL,
    avg_distance_m DECIMAL(14,2) NULL,
    avg_distance_km DECIMAL(12,3) NULL,
    avg_request_to_dispatch_min DECIMAL(12,3) NULL,
    avg_scheduled_to_pickup_min DECIMAL(12,3) NULL,
    avg_ride_min DECIMAL(12,3) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (weekday_number, hour_of_day),

    CONSTRAINT chk_weekday_number
        CHECK (weekday_number BETWEEN 0 AND 6),
    CONSTRAINT chk_hour_of_day
        CHECK (hour_of_day BETWEEN 0 AND 23)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 4. 출발구-목적구 이동 흐름 집계
-- 목적지가 서울 외 지역일 수도 있으므로 목적지는 문자열로도 보존합니다.
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS od_flow_stat (
    origin_district_id INT NOT NULL,
    destination_name VARCHAR(50) NOT NULL,

    trip_count INT UNSIGNED NOT NULL DEFAULT 0,

    fare_sum DECIMAL(18,2) NOT NULL DEFAULT 0,
    fare_count INT UNSIGNED NOT NULL DEFAULT 0,

    distance_m_sum DECIMAL(20,2) NOT NULL DEFAULT 0,
    distance_count INT UNSIGNED NOT NULL DEFAULT 0,

    request_to_dispatch_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    request_to_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0,

    scheduled_to_pickup_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    scheduled_to_pickup_count INT UNSIGNED NOT NULL DEFAULT 0,

    ride_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    ride_min_count INT UNSIGNED NOT NULL DEFAULT 0,

    avg_fare DECIMAL(12,2) NULL,
    avg_distance_m DECIMAL(14,2) NULL,
    avg_distance_km DECIMAL(12,3) NULL,
    avg_request_to_dispatch_min DECIMAL(12,3) NULL,
    avg_scheduled_to_pickup_min DECIMAL(12,3) NULL,
    avg_ride_min DECIMAL(12,3) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (origin_district_id, destination_name),
    CONSTRAINT fk_od_origin_district
        FOREIGN KEY (origin_district_id)
        REFERENCES district (district_id)
) ENGINE=InnoDB;

CREATE INDEX idx_od_destination
    ON od_flow_stat (destination_name);

-- ---------------------------------------------------------
-- 5. 이용목적별 집계
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS purpose_stat (
    purpose_name VARCHAR(50) PRIMARY KEY,

    trip_count INT UNSIGNED NOT NULL DEFAULT 0,

    fare_sum DECIMAL(18,2) NOT NULL DEFAULT 0,
    fare_count INT UNSIGNED NOT NULL DEFAULT 0,

    distance_m_sum DECIMAL(20,2) NOT NULL DEFAULT 0,
    distance_count INT UNSIGNED NOT NULL DEFAULT 0,

    request_to_dispatch_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    request_to_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0,

    scheduled_to_pickup_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    scheduled_to_pickup_count INT UNSIGNED NOT NULL DEFAULT 0,

    ride_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    ride_min_count INT UNSIGNED NOT NULL DEFAULT 0,

    avg_fare DECIMAL(12,2) NULL,
    avg_distance_m DECIMAL(14,2) NULL,
    avg_distance_km DECIMAL(12,3) NULL,
    avg_request_to_dispatch_min DECIMAL(12,3) NULL,
    avg_scheduled_to_pickup_min DECIMAL(12,3) NULL,
    avg_ride_min DECIMAL(12,3) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 6. 장애유형·차량구분별 집계
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS disability_vehicle_stat (
    disability_type VARCHAR(50) NOT NULL,
    vehicle_type VARCHAR(30) NOT NULL,

    trip_count INT UNSIGNED NOT NULL DEFAULT 0,

    fare_sum DECIMAL(18,2) NOT NULL DEFAULT 0,
    fare_count INT UNSIGNED NOT NULL DEFAULT 0,

    distance_m_sum DECIMAL(20,2) NOT NULL DEFAULT 0,
    distance_count INT UNSIGNED NOT NULL DEFAULT 0,

    request_to_dispatch_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    request_to_dispatch_count INT UNSIGNED NOT NULL DEFAULT 0,

    scheduled_to_pickup_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    scheduled_to_pickup_count INT UNSIGNED NOT NULL DEFAULT 0,

    ride_min_sum DECIMAL(20,4) NOT NULL DEFAULT 0,
    ride_min_count INT UNSIGNED NOT NULL DEFAULT 0,

    avg_fare DECIMAL(12,2) NULL,
    avg_distance_m DECIMAL(14,2) NULL,
    avg_distance_km DECIMAL(12,3) NULL,
    avg_request_to_dispatch_min DECIMAL(12,3) NULL,
    avg_scheduled_to_pickup_min DECIMAL(12,3) NULL,
    avg_ride_min DECIMAL(12,3) NULL,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (disability_type, vehicle_type)
) ENGINE=InnoDB;

-- ---------------------------------------------------------
-- 7. 데이터 품질 점검 결과
-- ---------------------------------------------------------
CREATE TABLE IF NOT EXISTS data_quality_log (
    quality_id BIGINT AUTO_INCREMENT PRIMARY KEY,
    source_name VARCHAR(100) NOT NULL,
    issue_type VARCHAR(100) NOT NULL,
    record_count INT UNSIGNED NOT NULL DEFAULT 0,
    checked_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    description VARCHAR(500) NULL,
    CONSTRAINT uq_quality_source_issue
        UNIQUE (source_name, issue_type)
) ENGINE=InnoDB;

INSERT INTO data_quality_log
    (source_name, issue_type, record_count, description)
VALUES
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'total_records',
        1729476,
        '전처리한 전체 레코드 수'
    ),
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'completed_records',
        1483324,
        '승차일시와 하차일시가 모두 존재하는 완료 운행'
    ),
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'cancelled_records',
        245337,
        '취소일시가 존재하는 레코드'
    ),
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'completed_and_cancelled',
        2,
        '완료와 취소 조건을 동시에 만족하는 레코드'
    ),
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'unclassified_records',
        817,
        '완료 및 취소로 분류되지 않은 레코드'
    ),
    (
        '서울시설공단 장애인콜택시 탑승내역 2025',
        'negative_dispatch_time',
        1,
        '접수일시보다 배차일시가 빠른 레코드'
    )
ON DUPLICATE KEY UPDATE
    record_count = VALUES(record_count),
    checked_at = CURRENT_TIMESTAMP,
    description = VALUES(description);

-- ---------------------------------------------------------
-- 8. 생성 결과 확인
-- ---------------------------------------------------------
SHOW TABLES;

SELECT COUNT(*) AS district_count
FROM district;

SELECT
    issue_type,
    record_count
FROM data_quality_log
ORDER BY quality_id;
