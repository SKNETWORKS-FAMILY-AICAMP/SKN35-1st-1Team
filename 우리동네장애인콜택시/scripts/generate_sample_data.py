"""개발/검증용 더미 원본 데이터 생성 스크립트.

실제 서울시 장애인콜택시 원본 데이터는 아직 없으므로, 전처리·집계·DB적재·
Streamlit 화면까지 전체 파이프라인이 정상 동작하는지 검증할 수 있도록
원본 컬럼 스키마(접수일시, 배차일시 ... )를 그대로 따르는 더미 CSV를
data/sample/ 에 생성한다.

실제 데이터가 준비되면 이 파일 대신 data/raw/ 에 원본 CSV를 넣고
preprocessing/clean_taxi_data.py --input data/raw/<파일명> 으로 실행하면 된다.

주의: 이 스크립트가 생성하는 데이터는 샘플이며 data/raw 가 아닌
data/sample 에만 저장한다. 실제 DB에는 절대 자동 삽입하지 않는다.
"""
from __future__ import annotations

import argparse
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

SEOUL_DISTRICTS = [
    "강남구", "강동구", "강북구", "강서구", "관악구", "광진구", "구로구", "금천구",
    "노원구", "도봉구", "동대문구", "동작구", "마포구", "서대문구", "서초구", "성동구",
    "성북구", "송파구", "양천구", "영등포구", "용산구", "은평구", "종로구", "중구", "중랑구",
]

# 정규화 테스트를 위한 원본 표기 변형(일부 행에만 적용)
DISTRICT_ALIAS_VARIANTS = {
    "강남구": ["강남", "강남구", "서울 강남구", "서울특별시 강남구", " 강남구 "],
    "서초구": ["서초", "서초구", "서울 서초구"],
}
UNMAPPED_SAMPLES = ["세종시", "부산 해운대구", "경기 성남시", ""]

PURPOSE_RAW_TO_GROUP = {
    "병원 진료": "의료", "재활 치료": "의료",
    "복지관 이용": "복지시설", "주간보호센터": "복지시설",
    "학교 등하교": "교육", "직업훈련": "교육",
    "출퇴근": "직장", "관공서 방문": "공공업무",
    "여가 활동": "여가", "경조사": "기타", "기타": "기타",
}
VEHICLE_RAW_TO_GROUP = {
    "휠체어 탑승형 대형": "휠체어차량", "휠체어 탑승형 중형": "휠체어차량",
    "일반 세단형": "일반차량", "기타 차량": "기타",
}
DISABILITY_RAW_TO_GROUP = {
    "지체장애 1급": "지체장애", "지체장애 2급": "지체장애",
    "뇌병변장애 1급": "뇌병변장애", "뇌병변장애 2급": "뇌병변장애",
    "시각장애 1급": "시각장애", "신장장애": "신장장애",
    "국가유공자(상이)": "기타",
}


def _pick_district(rng: random.Random) -> str:
    district = rng.choice(SEOUL_DISTRICTS)
    if district in DISTRICT_ALIAS_VARIANTS and rng.random() < 0.15:
        return rng.choice(DISTRICT_ALIAS_VARIANTS[district])
    if rng.random() < 0.01:
        return rng.choice(UNMAPPED_SAMPLES)
    return district


def _fare_for_distance(distance_km: float) -> int:
    # 서울시설공단 공개 요금기준(2026-07 기준): 5km 기본 1,500원,
    # 5~10km 구간 km당 280원, 10km 초과 구간 km당 70원 추가.
    if distance_km <= 5:
        return 1500
    if distance_km <= 10:
        return int(1500 + (distance_km - 5) * 280)
    return int(1500 + 5 * 280 + (distance_km - 10) * 70)


def generate(n_rows: int, seed: int, start: datetime, end: datetime) -> pd.DataFrame:
    rng = random.Random(seed)
    np_rng = np.random.default_rng(seed)
    total_seconds = int((end - start).total_seconds())

    rows = []
    for i in range(n_rows):
        request_at = start + timedelta(seconds=rng.randint(0, total_seconds))
        # 낮 시간대에 접수가 몰리도록 가중치 부여
        hour_weights = [1, 1, 1, 1, 1, 2, 4, 6, 8, 7, 6, 6, 6, 6, 6, 6, 7, 8, 6, 4, 3, 2, 1, 1]
        hour = rng.choices(range(24), weights=hour_weights, k=1)[0]
        request_at = request_at.replace(hour=hour, minute=rng.randint(0, 59), second=rng.randint(0, 59))

        origin = _pick_district(rng)
        destination = _pick_district(rng)
        purpose_raw = rng.choice(list(PURPOSE_RAW_TO_GROUP.keys()))
        vehicle_raw = rng.choice(list(VEHICLE_RAW_TO_GROUP.keys()))
        disability_raw = rng.choice(list(DISABILITY_RAW_TO_GROUP.keys()))
        distance = round(max(0.5, np_rng.gamma(3.0, 3.0)), 1)
        fare = _fare_for_distance(distance)

        scheduled_at = request_at + timedelta(minutes=rng.randint(10, 180))

        outcome = rng.random()
        dispatch_at = pickup_at = dropoff_at = cancel_at = None

        if outcome < 0.08:
            # 배차 전 취소
            cancel_at = request_at + timedelta(minutes=rng.randint(1, 30))
        else:
            dispatch_wait = max(1, np_rng.exponential(18))
            dispatch_at = request_at + timedelta(minutes=dispatch_wait)
            if outcome < 0.12:
                # 배차 후 취소(노쇼 등)
                cancel_at = dispatch_at + timedelta(minutes=rng.randint(1, 20))
            else:
                boarding_delay = max(1, np_rng.exponential(8))
                pickup_at = dispatch_at + timedelta(minutes=boarding_delay)
                trip_minutes = max(3, distance / rng.uniform(15, 25) * 60)
                dropoff_at = pickup_at + timedelta(minutes=trip_minutes)

        row = {
            "접수일시": request_at,
            "예정일시": scheduled_at,
            "배차일시": dispatch_at,
            "승차일시": pickup_at,
            "하차일시": dropoff_at,
            "취소일시": cancel_at,
            "출발구": origin,
            "출발동": f"{rng.choice(['1','2','3'])}동",
            "목적구": destination,
            "목적동": f"{rng.choice(['1','2','3'])}동",
            "이용목적": purpose_raw,
            "요금": fare,
            "승차거리": distance,
            "차량구분": vehicle_raw,
            "장애유형": disability_raw,
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    date_cols = ["접수일시", "예정일시", "배차일시", "승차일시", "하차일시", "취소일시"]
    for col in date_cols:
        df[col] = df[col].astype(object).where(df[col].notna(), None)

    # 의도적 이상치/결측 주입: 전처리 파이프라인의 이상치 플래그 로직 검증용
    n = len(df)
    neg_idx = np_rng.choice(n, size=max(1, n // 200), replace=False)
    for idx in neg_idx:
        if pd.notna(df.at[idx, "배차일시"]):
            df.at[idx, "배차일시"] = df.at[idx, "접수일시"] - timedelta(minutes=int(np_rng.integers(1, 30)))

    huge_wait_idx = np_rng.choice(n, size=max(1, n // 300), replace=False)
    for idx in huge_wait_idx:
        if pd.notna(df.at[idx, "배차일시"]):
            df.at[idx, "배차일시"] = df.at[idx, "접수일시"] + timedelta(hours=int(np_rng.integers(25, 48)))

    bad_date_idx = np_rng.choice(n, size=max(1, n // 250), replace=False)
    for idx in bad_date_idx:
        df.at[idx, "접수일시"] = "0000-00-00"

    neg_fare_idx = np_rng.choice(n, size=max(1, n // 400), replace=False)
    for idx in neg_fare_idx:
        df.at[idx, "요금"] = -df.at[idx, "요금"]

    dup_rows = df.sample(n=max(1, n // 150), random_state=seed)
    df = pd.concat([df, dup_rows], ignore_index=True)

    return df.sample(frac=1.0, random_state=seed).reset_index(drop=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="더미 장애인콜택시 원본 데이터 생성")
    parser.add_argument("--rows", type=int, default=4000)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=str, default="data/sample/dummy_taxi_raw.csv")
    parser.add_argument("--start", type=str, default="2025-01-01")
    parser.add_argument("--end", type=str, default="2025-12-31")
    args = parser.parse_args()

    start = datetime.fromisoformat(args.start)
    end = datetime.fromisoformat(args.end)
    df = generate(args.rows, args.seed, start, end)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"생성 완료: {out_path} ({len(df)}행)")


if __name__ == "__main__":
    main()
