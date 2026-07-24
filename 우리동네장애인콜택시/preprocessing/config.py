"""전처리 파이프라인 상수 설정.

컬럼명 매핑, 범주값 그룹핑, 이상치 판정 기준값을 한 곳에서 관리한다.
"""
from __future__ import annotations

CHUNK_SIZE = 50_000

# 원본 컬럼명 -> 정제 컬럼명.
# 출발구/목적구/이용목적/차량구분/장애유형은 "원본 그대로 보존 + 정제값 분리"
# 요구사항에 따라 *_raw 로 우선 이름을 바꾸고, 정제값(origin_district, purpose_group 등)은
# transforms.py에서 별도 컬럼으로 새로 만든다.
COLUMN_RENAME_MAP: dict[str, str] = {
    "접수일시": "request_at",
    "예정일시": "scheduled_at",
    "배차일시": "dispatch_at",
    "승차일시": "pickup_at",
    "하차일시": "dropoff_at",
    "취소일시": "cancel_at",
    "출발구": "origin_district_raw",
    "출발동": "origin_dong",
    "목적구": "destination_district_raw",
    "목적동": "destination_dong",
    "이용목적": "purpose_raw",
    "요금": "fare",
    "승차거리": "distance",
    "차량구분": "vehicle_type_raw",
    "장애유형": "disability_type_raw",
}

REQUIRED_RAW_COLUMNS = list(COLUMN_RENAME_MAP.keys())

DATETIME_COLUMNS = [
    "request_at", "scheduled_at", "dispatch_at", "pickup_at", "dropoff_at", "cancel_at",
]

# 이용목적 원본 표기 -> 그룹 (홈페이지에 없는 표기는 '기타'로 묶는다)
PURPOSE_GROUP_MAP: dict[str, str] = {
    "병원 진료": "의료", "재활 치료": "의료", "통원 치료": "의료",
    "복지관 이용": "복지시설", "주간보호센터": "복지시설",
    "학교 등하교": "교육", "직업훈련": "교육",
    "출퇴근": "직장",
    "관공서 방문": "공공업무",
    "여가 활동": "여가", "경조사": "기타",
}
DEFAULT_PURPOSE_GROUP = "기타"

VEHICLE_GROUP_MAP: dict[str, str] = {
    "휠체어 탑승형 대형": "휠체어차량",
    "휠체어 탑승형 중형": "휠체어차량",
    "일반 세단형": "일반차량",
}
DEFAULT_VEHICLE_GROUP = "기타"

DISABILITY_GROUP_MAP: dict[str, str] = {
    "지체장애 1급": "지체장애", "지체장애 2급": "지체장애",
    "뇌병변장애 1급": "뇌병변장애", "뇌병변장애 2급": "뇌병변장애",
    "시각장애 1급": "시각장애",
    "신장장애": "신장장애",
}
DEFAULT_DISABILITY_GROUP = "기타"

# 이상치 판정 기준
MAX_REASONABLE_WAIT_HOURS = 24
MAX_REASONABLE_TRIP_HOURS = 24

# 집계 결과 노출 시 표본이 이 값 미만인 조합은 화면에 세부 노출하지 않고 '기타/표시제한' 처리
SMALL_SAMPLE_THRESHOLD = 5

RAW_DIR = "data/raw"
SAMPLE_DIR = "data/sample"
PROCESSED_DIR = "data/processed"
REJECTED_DIR = "data/rejected"
