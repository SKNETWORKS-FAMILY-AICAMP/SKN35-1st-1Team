-- =========================================================
-- 2단계 사전 수정: 서울 외 출발지역도 저장할 수 있도록 기준 테이블 확장
-- 최초 1회만 실행하세요.
-- =========================================================

USE seoul_mobility_db;

ALTER TABLE district
    ADD COLUMN is_seoul TINYINT(1) NOT NULL DEFAULT 0
        COMMENT '서울 25개 자치구 여부' AFTER district_name,
    ADD COLUMN area_type VARCHAR(20) NULL
        COMMENT '구/시/군/기타' AFTER is_seoul;

-- 기존에 입력한 서울 25개 자치구 표시
UPDATE district
SET
    is_seoul = 1,
    area_type = '구';

SELECT *
FROM district
ORDER BY district_id;
