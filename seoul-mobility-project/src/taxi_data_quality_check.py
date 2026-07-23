from pathlib import Path

import pandas as pd


FILE_PATH = Path(
    r"C:\Users\tommy\sk-encore"
    r"\서울시설공단_장애인콜택시 탑승내역_20251231.csv"
)

OUTPUT_DIR = Path(
    r"C:\Users\tommy\sk-encore\taxi_processed\data_quality"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

DATETIME_COLUMNS = [
    "접수일시",
    "예정일시",
    "배차일시",
    "승차일시",
    "하차일시",
    "취소일시",
]

USE_COLUMNS = DATETIME_COLUMNS + [
    "출발구",
    "출발동",
    "목적구",
    "목적동",
    "이용목적",
    "요금",
    "승차거리",
    "차량구분",
    "장애유형",
]

both_completed_cancelled = []
neither_completed_nor_cancelled = []
negative_dispatch_time = []

reader = pd.read_csv(
    FILE_PATH,
    encoding="utf-8-sig",
    dtype="string",
    usecols=USE_COLUMNS,
    chunksize=100_000,
)

for chunk_number, chunk in enumerate(reader, start=1):

    for column in DATETIME_COLUMNS:
        chunk[column] = pd.to_datetime(
            chunk[column],
            errors="coerce",
        )

    completed = (
        chunk["승차일시"].notna()
        & chunk["하차일시"].notna()
    )

    cancelled = chunk["취소일시"].notna()

    dispatch_minutes = (
        chunk["배차일시"] - chunk["접수일시"]
    ).dt.total_seconds() / 60

    both_mask = completed & cancelled
    neither_mask = ~completed & ~cancelled
    negative_dispatch_mask = dispatch_minutes < 0

    if both_mask.any():
        data = chunk.loc[both_mask].copy()
        data["이상유형"] = "완료 및 취소 동시 기록"
        both_completed_cancelled.append(data)

    if neither_mask.any():
        data = chunk.loc[neither_mask].copy()
        data["이상유형"] = "완료 및 취소 모두 아님"
        neither_completed_nor_cancelled.append(data)

    if negative_dispatch_mask.any():
        data = chunk.loc[negative_dispatch_mask].copy()
        data["접수후배차_분"] = dispatch_minutes.loc[
            negative_dispatch_mask
        ]
        data["이상유형"] = "음수 배차시간"
        negative_dispatch_time.append(data)

    print(f"{chunk_number}번째 청크 확인 완료")


def save_results(
    frames: list[pd.DataFrame],
    filename: str,
) -> None:
    if frames:
        result = pd.concat(frames, ignore_index=True)
        result.to_csv(
            OUTPUT_DIR / filename,
            index=False,
            encoding="utf-8-sig",
        )
        print(f"{filename}: {len(result):,}건 저장")
    else:
        print(f"{filename}: 해당 데이터 없음")


save_results(
    both_completed_cancelled,
    "completed_and_cancelled.csv",
)

save_results(
    neither_completed_nor_cancelled,
    "unclassified_records.csv",
)

save_results(
    negative_dispatch_time,
    "negative_dispatch_time.csv",
)