"""
TiDB Cloud 연결 및 장애인콜택시 통계 조회

reserve.py와 함께 사용하는 버전입니다.
vw_weekday_hour_stat의 평균 대기시간을 합칠 때
전체 요청 수가 아닌 유효 대기시간 건수(valid_wait_count)를 가중치로 사용합니다.
"""

import os

import certifi
import pymysql
from dotenv import load_dotenv
from pymysql.cursors import DictCursor


load_dotenv()


def get_db_connection():
    """환경 변수의 접속정보를 이용해 TiDB Cloud에 연결합니다."""

    return pymysql.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USERNAME"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_DATABASE"),
        charset="utf8mb4",
        cursorclass=DictCursor,
        ssl={
            "ca": certifi.where(),
            "check_hostname": True,
        },
        autocommit=True,
        connect_timeout=15,
        read_timeout=60,
        write_timeout=60,
    )


def get_year_count():
    """연도별 전체 이용 건수를 조회합니다."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    source_year,
                    COUNT(*) AS trip_count
                FROM trip
                GROUP BY source_year
                ORDER BY source_year;
                """
            )

            return cursor.fetchall()

    finally:
        connection.close()


def get_weekday_hour_stats(weekday_no):
    """
    특정 요일의 시간대별 이용 건수와 평균 대기시간을 조회합니다.

    weekday_no:
        월요일 = 0
        화요일 = 1
        ...
        일요일 = 6

    여러 연도의 평균 대기시간을 합칠 때는 각 평균을 계산하는 데
    실제로 사용된 valid_wait_count를 가중치로 사용합니다.
    """

    if weekday_no not in range(7):
        raise ValueError("weekday_no는 0부터 6 사이여야 합니다.")

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    weekday_no,
                    MAX(weekday_name) AS weekday_name,
                    request_hour,
                    SUM(request_count) AS request_count,

                    ROUND(
                        SUM(
                            CASE
                                WHEN avg_wait_minutes IS NOT NULL
                                 AND valid_wait_count > 0
                                THEN avg_wait_minutes * valid_wait_count
                                ELSE 0
                            END
                        )
                        /
                        NULLIF(
                            SUM(
                                CASE
                                    WHEN avg_wait_minutes IS NOT NULL
                                     AND valid_wait_count > 0
                                    THEN valid_wait_count
                                    ELSE 0
                                END
                            ),
                            0
                        ),
                        1
                    ) AS avg_wait_minutes

                FROM vw_weekday_hour_stat

                WHERE weekday_no = %s

                GROUP BY
                    weekday_no,
                    request_hour

                ORDER BY
                    request_hour;
                """,
                (weekday_no,),
            )

            return cursor.fetchall()

    finally:
        connection.close()


def test_db_connection():
    """TiDB 연결 상태를 확인합니다."""

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    DATABASE() AS database_name,
                    VERSION() AS server_version,
                    (SELECT COUNT(*) FROM trip) AS trip_count;
                """
            )

            return cursor.fetchone()

    finally:
        connection.close()


if __name__ == "__main__":
    result = test_db_connection()

    print("TiDB 연결 성공")
    print(f"DB 이름: {result['database_name']}")
    print(f"서버 버전: {result['server_version']}")
    print(f"전체 이용 건수: {result['trip_count']:,}")