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
# --------- 이용현황 --------- //