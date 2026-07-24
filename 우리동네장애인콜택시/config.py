"""애플리케이션 전역 설정.

.env 파일(또는 환경변수)에서 값을 읽어온다. 민감한 값(비밀번호, API 키, 연락처)은
절대 코드에 하드코딩하지 않고 이 모듈을 통해서만 접근한다.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv
from sqlalchemy.engine import URL

load_dotenv()


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default) or default


@dataclass(frozen=True)
class DBConfig:
    driver: str = _get("DB_DRIVER", "mysql")  # "mysql"(운영) 또는 "sqlite"(로컬 데모 전용)
    host: str = _get("DB_HOST", "localhost")
    port: int = int(_get("DB_PORT", "3306") or 3306)
    user: str = _get("DB_USER", "root")
    password: str = _get("DB_PASSWORD", "")
    name: str = _get("DB_NAME", "call_taxi")
    sqlite_path: str = _get("DEMO_SQLITE_PATH", "data/demo.db")

    def sqlalchemy_url(self) -> URL:
        # URL.create가 비밀번호의 한글/특수문자를 안전하게 인코딩해준다.
        # 문자열 결합(f-string)으로 접속 URL을 만들지 않는다.
        if self.driver == "sqlite":
            # 실제 MySQL 없이 화면을 빠르게 확인하기 위한 로컬 데모 전용 경로.
            # 운영 배포 시에는 DB_DRIVER를 mysql로 두거나 비워둔다.
            return URL.create(drivername="sqlite", database=self.sqlite_path)
        return URL.create(
            drivername="mysql+pymysql",
            username=self.user,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.name,
            query={"charset": "utf8mb4"},
        )


@dataclass(frozen=True)
class NaverAPIConfig:
    client_id: str = _get("NAVER_CLIENT_ID", "")
    client_secret: str = _get("NAVER_CLIENT_SECRET", "")

    @property
    def is_configured(self) -> bool:
        return bool(self.client_id and self.client_secret)


@dataclass(frozen=True)
class FAQSourceConfig:
    source_url: str = _get("FAQ_SOURCE_URL", "https://www.sisul.or.kr/open_content/calltaxi/")
    source_name: str = _get("FAQ_SOURCE_NAME", "서울시설공단 장애인콜택시")


@dataclass(frozen=True)
class OfficialChannelConfig:
    reservation_url: str = _get("OFFICIAL_RESERVATION_URL", "https://www.sisul.or.kr/open_content/calltaxi/")
    phone_number: str = _get("OFFICIAL_PHONE_NUMBER", "1588-4388")
    sms_number: str = _get("OFFICIAL_SMS_NUMBER", "1588-4388")


DB = DBConfig()
NAVER = NaverAPIConfig()
FAQ_SOURCE = FAQSourceConfig()
OFFICIAL = OfficialChannelConfig()

# 서비스 전체에서 반복 사용하는 안내 문구
SERVICE_DISCLAIMER = (
    "본 서비스는 서울시설공단의 공식 예약·배차 시스템이 아닙니다. "
    "입력한 예약 내용을 정리하고 과거 이용 통계를 기반으로 참고 정보를 제공합니다."
)

# 소규모 표본 노출 제한 (예: 장애유형×차량구분 조합 건수가 이 값 미만이면 화면에 세부 노출하지 않고 '기타'로 묶음)
SMALL_SAMPLE_THRESHOLD = 5
