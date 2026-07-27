"""
DB 정보
"""

# DB 데이터
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv() # .env 파일 로드



def get_db_connection():
    """환경 변수에서 정보를 가져와 MySQL에 연결합니다."""
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
        port=int(os.getenv("DB_PORT"))
    )

def get_year_count():
    """테이블이 없을 경우 초기 생성합니다."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT source_year, COUNT(*) AS trip_count
        FROM trip
        GROUP BY source_year
        ORDER BY source_year DESC;
    """)
    result = cursor.fetchall()
    # conn.commit()
    cursor.close()
    conn.close()

    return result