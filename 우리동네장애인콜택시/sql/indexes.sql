-- =====================================================================
-- schema.sql 의 기본 PK/UNIQUE/인덱스 외에 조회 성능을 위해 추가로
-- 고려할 수 있는 인덱스. 기존 인덱스와 중복되지 않도록 실행 전 확인한다.
-- (MySQL은 CREATE INDEX IF NOT EXISTS를 지원하지 않으므로 실행 전
--  information_schema.statistics 로 존재 여부를 확인하고 실행한다.)
-- =====================================================================

-- 기간 필터 + 자치구 필터를 함께 거는 조회 (이용현황 페이지 KPI/추이)
-- 이미 UNIQUE KEY uq_daily(stat_date, district_id) 가 있어 커버되므로 별도 인덱스 불필요.

-- 뉴스: 검색 키워드별 최신순 조회
CREATE INDEX idx_news_keyword_published ON news (search_keyword, published_at);

-- FAQ: 키워드 검색(LIKE) 보조용 -- MySQL LIKE '%...%' 는 인덱스를 못 타므로
-- 실제 키워드 검색 성능이 중요해지면 FULLTEXT 인덱스 도입을 검토한다.
ALTER TABLE faq ADD FULLTEXT INDEX ft_faq_question_answer (question, answer);
