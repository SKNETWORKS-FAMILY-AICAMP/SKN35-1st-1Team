-- =====================================================================
-- 참고용 샘플 쿼리 모음. 실제 애플리케이션은 이 쿼리들을
-- repositories/*.py 에서 SQLAlchemy text() + 파라미터 바인딩으로 실행한다.
-- (Streamlit 페이지에서 직접 SQL을 작성하지 않는다.)
-- =====================================================================

-- 1) 기간 + 자치구(출발) 필터로 KPI 집계
SELECT
    SUM(request_count)   AS total_request,
    SUM(ride_count)       AS total_ride,
    SUM(completed_count)  AS total_completed,
    SUM(cancel_count)     AS total_cancel,
    ROUND(SUM(cancel_count) / NULLIF(SUM(request_count), 0) * 100, 1) AS cancel_rate_pct,
    SUM(avg_dispatch_wait_min * valid_wait_count) / NULLIF(SUM(valid_wait_count), 0) AS avg_dispatch_wait_min,
    AVG(avg_distance) AS avg_distance,
    AVG(avg_fare)      AS avg_fare
FROM district_daily_stat
WHERE stat_date BETWEEN :start_date AND :end_date
  AND (:district_id IS NULL OR district_id = :district_id);

-- 2) 예약 준비 도우미: 혼잡도 대체조회 1단계 (출발구 + 요일 + 시간)
SELECT request_count, avg_dispatch_wait_min, median_dispatch_wait_min,
       congestion_percentile, congestion_level, valid_wait_count
FROM district_hourly_stat
WHERE district_id = :district_id AND weekday_num = :weekday_num AND request_hour = :request_hour;

-- 3) 혼잡도 대체조회 3단계 (요일 + 시간, 자치구 무관)
SELECT request_count, avg_dispatch_wait_min, median_dispatch_wait_min,
       congestion_percentile, congestion_level
FROM weekday_hour_stat
WHERE weekday_num = :weekday_num AND request_hour = :request_hour;

-- 4) 자치구별 출발 이용 건수 (지도/막대차트용)
SELECT district_id, SUM(request_count) AS request_count, SUM(ride_count) AS ride_count
FROM district_daily_stat
WHERE stat_date BETWEEN :start_date AND :end_date
GROUP BY district_id
ORDER BY request_count DESC;

-- 5) 주요 출발구 -> 목적구 이동 경로 Top N
SELECT origin_district_id, destination_district_id, request_count, ride_count, avg_distance, avg_fare
FROM od_flow_stat
ORDER BY ride_count DESC
LIMIT :top_n;

-- 6) 월별 이용 건수 / 평균 배차 대기시간 추이
SELECT year, month, request_count, ride_count, avg_dispatch_wait_min
FROM monthly_stat
ORDER BY year, month;

-- 7) FAQ 카테고리 + 키워드 검색
SELECT faq_id, category, question, answer, source_url, source_name, updated_at
FROM faq
WHERE is_active = 1
  AND (:category IS NULL OR category = :category)
  AND (:keyword IS NULL OR question LIKE CONCAT('%', :keyword, '%') OR answer LIKE CONCAT('%', :keyword, '%'))
ORDER BY display_order, faq_id;

-- 8) 최신 뉴스 목록 (검색어 필터, 최신순, 최대 N건)
SELECT news_id, title, description, publisher, published_at, original_url, search_keyword, collected_at
FROM news
WHERE is_active = 1
  AND (:search_keyword IS NULL OR search_keyword = :search_keyword)
ORDER BY published_at DESC
LIMIT :limit_n;
