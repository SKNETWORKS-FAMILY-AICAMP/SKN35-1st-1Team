-- =========================================================================
-- 서울시 장애인콜택시 FAQ 조회 시스템 — MySQL 스키마
-- 담당 파트 : FAQ (서울시설공단 공식 홈페이지 → Q&A 재구성)
-- 대상 DBMS : MySQL 8.x
-- 실행 방법 : DBeaver에서 이 파일을 열고 전체 실행(Alt+X)
--             또는  python db/loader.py  (스키마 생성 + 데이터 적재 자동 수행)
-- =========================================================================

CREATE DATABASE IF NOT EXISTS seoul_calltaxi
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE seoul_calltaxi;

-- 재실행 가능하도록 자식 테이블부터 제거 (FK 역순)
DROP TABLE IF EXISTS crawl_log;
DROP TABLE IF EXISTS faq_keyword;
DROP TABLE IF EXISTS faq;
DROP TABLE IF EXISTS faq_source;
DROP TABLE IF EXISTS faq_category;


-- -------------------------------------------------------------------------
-- 1. faq_category : FAQ 분류 코드 (마스터)
--    전처리 단계의 규칙 기반 분류 결과가 이 표의 값으로만 들어온다.
-- -------------------------------------------------------------------------
CREATE TABLE faq_category (
    category_id   INT          NOT NULL AUTO_INCREMENT COMMENT '카테고리 고유번호',
    category_name VARCHAR(30)  NOT NULL                COMMENT '카테고리명',
    sort_order    INT          NOT NULL DEFAULT 0      COMMENT '화면 노출 순서',
    description   VARCHAR(200) NULL                    COMMENT '분류 설명',
    PRIMARY KEY (category_id),
    UNIQUE KEY uk_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FAQ 분류 마스터';


-- -------------------------------------------------------------------------
-- 2. faq_source : 수집 출처 (마스터)
--    어떤 페이지를 어떤 도구로 수집했는지 기록 → 데이터 추적성 확보
-- -------------------------------------------------------------------------
CREATE TABLE faq_source (
    source_id      INT          NOT NULL AUTO_INCREMENT COMMENT '출처 고유번호',
    source_code    VARCHAR(30)  NOT NULL                COMMENT '출처 코드(board_faq, receipt 등)',
    source_name    VARCHAR(150) NOT NULL                COMMENT '출처 페이지명',
    source_url     VARCHAR(500) NOT NULL                COMMENT '원본 URL',
    collect_method VARCHAR(20)  NOT NULL                COMMENT '수집 도구(BeautifulSoup/Selenium)',
    created_at     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '등록일시',
    PRIMARY KEY (source_id),
    UNIQUE KEY uk_source_code (source_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FAQ 수집 출처 마스터';


-- -------------------------------------------------------------------------
-- 3. faq : FAQ 본문 (핵심 테이블)
--    content_hash = MD5(질문+답변) → 재수집 시 중복 적재 방지 키
-- -------------------------------------------------------------------------
CREATE TABLE faq (
    faq_id        INT          NOT NULL AUTO_INCREMENT COMMENT 'FAQ 고유번호',
    category_id   INT          NOT NULL                COMMENT '카테고리 FK',
    source_id     INT          NOT NULL                COMMENT '출처 FK',
    question      VARCHAR(300) NOT NULL                COMMENT '질문',
    answer        TEXT         NOT NULL                COMMENT '답변 본문',
    answer_length INT          NOT NULL DEFAULT 0      COMMENT '답변 길이(자)',
    orig_msg_seq  INT          NULL                    COMMENT '원본 게시글 번호(게시판 출처만)',
    view_count    INT          NULL                    COMMENT '원본 조회수(게시판 출처만)',
    department    VARCHAR(50)  NULL                    COMMENT '담당 부서',
    content_hash  CHAR(32)     NOT NULL                COMMENT '내용 해시(중복 방지)',
    collected_at  DATETIME     NOT NULL                COMMENT '수집 일시',
    created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '적재 일시',
    updated_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
                               ON UPDATE CURRENT_TIMESTAMP        COMMENT '수정 일시',
    PRIMARY KEY (faq_id),
    UNIQUE KEY uk_faq_content_hash (content_hash),
    KEY idx_faq_category (category_id),
    KEY idx_faq_source (source_id),
    KEY idx_faq_question (question),
    CONSTRAINT fk_faq_category FOREIGN KEY (category_id)
        REFERENCES faq_category (category_id) ON UPDATE CASCADE,
    CONSTRAINT fk_faq_source FOREIGN KEY (source_id)
        REFERENCES faq_source (source_id) ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FAQ 본문';


-- -------------------------------------------------------------------------
-- 4. faq_keyword : 검색 키워드 (faq 와 1:N)
--    전처리에서 추출한 상위 5개 키워드를 정규화해 별도 테이블로 분리
-- -------------------------------------------------------------------------
CREATE TABLE faq_keyword (
    keyword_id    INT         NOT NULL AUTO_INCREMENT COMMENT '키워드 고유번호',
    faq_id        INT         NOT NULL                COMMENT 'FAQ FK',
    keyword       VARCHAR(50) NOT NULL                COMMENT '검색 키워드',
    keyword_order INT         NOT NULL DEFAULT 1      COMMENT '빈도 순위(1이 최상위)',
    PRIMARY KEY (keyword_id),
    UNIQUE KEY uk_faq_keyword (faq_id, keyword),
    KEY idx_keyword (keyword),
    CONSTRAINT fk_keyword_faq FOREIGN KEY (faq_id)
        REFERENCES faq (faq_id) ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='FAQ 검색 키워드';


-- -------------------------------------------------------------------------
-- 5. crawl_log : 수집 실행 이력
--    언제 몇 건을 수집·적재했고 성공했는지 기록 → 재수집 운영 근거
-- -------------------------------------------------------------------------
CREATE TABLE crawl_log (
    log_id          INT          NOT NULL AUTO_INCREMENT COMMENT '이력 고유번호',
    source_id       INT          NULL                    COMMENT '출처 FK(전체 실행이면 NULL)',
    run_at          DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '실행 일시',
    status          VARCHAR(10)  NOT NULL                COMMENT 'SUCCESS / FAIL / PARTIAL',
    collected_count INT          NOT NULL DEFAULT 0      COMMENT '수집 건수',
    loaded_count    INT          NOT NULL DEFAULT 0      COMMENT '적재 건수',
    message         VARCHAR(500) NULL                    COMMENT '비고 / 오류 메시지',
    PRIMARY KEY (log_id),
    KEY idx_log_source (source_id),
    CONSTRAINT fk_log_source FOREIGN KEY (source_id)
        REFERENCES faq_source (source_id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='크롤링 실행 이력';


-- -------------------------------------------------------------------------
-- 카테고리 기준값 (전처리 표준 분류 7종과 일치해야 함)
-- -------------------------------------------------------------------------
INSERT INTO faq_category (category_name, sort_order, description) VALUES
    ('가입·등록',     1, '이용 등록 절차, 제출 서류, 복지카드 확인'),
    ('이용대상·자격', 2, '이용 가능 대상, 장애정도 기준, 동승·단독탑승'),
    ('이용방법·접수', 3, '전화·문자·인터넷·앱 접수 방법 및 예약/취소'),
    ('요금·결제',     4, '이용요금 산정 기준과 결제 방식'),
    ('배차·대기',     5, '차량 연결 기준, 대기시간, 배차 지연'),
    ('운행지역·시간', 6, '운행 범위(서울·수도권)와 운행 시간'),
    ('준수사항·기타', 7, '이용자 준수사항 및 기타 문의');
