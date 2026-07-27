"""
DB 정보
"""

# DB 데이터
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv() # .env 파일 로드


# --------- 공통 ---------
# DB 호출
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
        port=int(os.getenv("DB_PORT"))
    )
# --------- 공통 --------- //


# --------- 이용현황 ---------
# 연도별 이용 건수
def get_year_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_year, COUNT(*) AS trip_count
        FROM trip
        GROUP BY source_year
        ORDER BY source_year DESC;
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return result

# 시간별 이용 건수
def get_hour_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT YEAR(pickup_at) AS yr, HOUR(pickup_at) AS hr, COUNT(*) AS trip_count
        FROM trip
        WHERE pickup_at IS NOT NULL
        GROUP BY YEAR(pickup_at), HOUR(pickup_at)
        ORDER BY yr, hr;
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return result

# 월별 이용 건수
def get_month_count():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT YEAR(pickup_at) AS yr, MONTH(pickup_at) AS mo, COUNT(*) AS trip_count
        FROM trip
        GROUP BY YEAR(pickup_at), MONTH(pickup_at)
        ORDER BY yr, mo;
    """)
    result = cursor.fetchall()
    cursor.close()
    conn.close()

    return result

# 이용건수/대기시간/평균요금 데이터
def get_district_summary(gu_name):
    """
    선택한 출발 자치구의 요약 통계를 조회합니다.

    - 일평균 이용 건수:
      해당 자치구의 전체 이용 건수 / 전체 데이터 기간의 일수
    - 평균 배차 대기시간:
      접수일시부터 배차일시까지 0~180분인 유효 데이터의 평균
    - 평균 이용요금:
      0원보다 큰 유효 요금의 평균
    """

    if not gu_name:
        return {
            "daily_avg_count": None,
            "avg_wait_minutes": None,
            "avg_fare": None,
        }

    connection = get_db_connection()

    try:
        with connection.cursor(dictionary=True) as cursor:
            cursor.execute(
                """
                SELECT
                    ROUND(
                        COUNT(*) /
                        NULLIF(
                            (
                                SELECT
                                    DATEDIFF(
                                        MAX(DATE(request_at)),
                                        MIN(DATE(request_at))
                                    ) + 1
                                FROM trip
                                WHERE request_at IS NOT NULL
                            ),
                            0
                        ),
                        1
                    ) AS daily_avg_count,

                    ROUND(
                        AVG(
                            CASE
                                WHEN t.request_at IS NOT NULL
                                 AND t.dispatch_at IS NOT NULL
                                 AND t.dispatch_at >= t.request_at
                                 AND TIMESTAMPDIFF(
                                        MINUTE,
                                        t.request_at,
                                        t.dispatch_at
                                     ) BETWEEN 0 AND 180
                                THEN TIMESTAMPDIFF(
                                        MINUTE,
                                        t.request_at,
                                        t.dispatch_at
                                     )
                            END
                        ),
                        1
                    ) AS avg_wait_minutes,

                    ROUND(
                        AVG(
                            CASE
                                WHEN t.fare IS NOT NULL
                                 AND t.fare > 0
                                THEN t.fare
                            END
                        ),
                        0
                    ) AS avg_fare

                FROM trip AS t
                JOIN location AS l
                  ON t.origin_location_id = l.location_id
                WHERE l.district_name = %s;
                """,
                (gu_name,),
            )

            return cursor.fetchone()

    finally:
        connection.close()
# --------- 이용현황 --------- //