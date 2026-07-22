-- =====================================================================
-- 장애인 자동차 지원 시스템 — MySQL 스키마 설계 (초안)
-- 실행: mysql -u root -p < schema.sql
-- 문자셋: utf8mb4 (한글/이모지 대응)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS vehicle_support
  DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE vehicle_support;

-- ---------------------------------------------------------------------
-- 1) 지원사업 공고 (지역별/대상별 지원금 비교의 원천)
--    target_type: 보훈 | 산재 | 일반
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS support_programs (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  region        VARCHAR(20)  NOT NULL,          -- 시/도 (예: 서울, 경기)
  target_type   VARCHAR(10)  NOT NULL,          -- 보훈 | 산재 | 일반
  agency        VARCHAR(50)  NOT NULL,          -- 주관 기관 (국가보훈부, 근로복지공단 등)
  program_name  VARCHAR(200) NOT NULL,          -- 지원사업명
  support_item  VARCHAR(200),                   -- 지원 항목 (개조비, 구입보조 등)
  limit_amount  INT,                            -- 지원금 한도(원)
  eligibility   TEXT,                           -- 수혜 자격 조건
  source_url    VARCHAR(500),                   -- 공고 원문 링크
  scraped_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_region_target (region, target_type)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 2) 판매 업체/판매자 (엔카 스타일 리스트업)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sellers (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  shop_name     VARCHAR(100) NOT NULL,          -- 판매자/업체 상호
  region        VARCHAR(20),
  phone         VARCHAR(30),
  email         VARCHAR(100),
  photo_url     VARCHAR(500),                   -- 대표 사진
  portfolio_url VARCHAR(500),                   -- 블로그/작업물 링크
  career        TEXT,                           -- 작업자 이력
  rating        DECIMAL(2,1) DEFAULT 0.0,       -- 평균 평점
  review_count  INT DEFAULT 0,
  created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS seller_reviews (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  seller_id  INT NOT NULL,
  author     VARCHAR(50),
  rating     INT,                               -- 1~5
  content    TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (seller_id) REFERENCES sellers(id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 3) 합법 개조/검사 — 보조기구별 절차 + 지역별 공업사/검사소
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS modification_steps (
  id          INT AUTO_INCREMENT PRIMARY KEY,
  device_type VARCHAR(50) NOT NULL,             -- 핸드컨트롤러, 리프트 등
  step_no     INT NOT NULL,
  title       VARCHAR(200) NOT NULL,
  detail      TEXT,
  INDEX idx_device (device_type, step_no)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS inspection_shops (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  name       VARCHAR(100) NOT NULL,
  kind       VARCHAR(20),                        -- 공업사 | 검사소
  region     VARCHAR(20),
  address    VARCHAR(300),
  lat        DECIMAL(9,6),
  lon        DECIMAL(9,6),
  phone      VARCHAR(30)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 4) 차량 등록 통계 (도별)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS registration_stats (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  region        VARCHAR(20) NOT NULL,
  year          INT NOT NULL,
  registered    INT NOT NULL,                    -- 등록 대수
  UNIQUE KEY uq_region_year (region, year)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 5) 편의시설 (장애인 주차/충전/편의) — 위치기반
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS facilities (
  id       INT AUTO_INCREMENT PRIMARY KEY,
  name     VARCHAR(150) NOT NULL,
  kind     VARCHAR(20),                          -- 주차 | 충전 | 편의
  region   VARCHAR(20),
  address  VARCHAR(300),
  lat      DECIMAL(9,6),
  lon      DECIMAL(9,6)
) ENGINE=InnoDB;

-- ---------------------------------------------------------------------
-- 6) FAQ 게시판
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS faqs (
  id         INT AUTO_INCREMENT PRIMARY KEY,
  category   VARCHAR(30),
  question   VARCHAR(300) NOT NULL,
  answer     TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;
