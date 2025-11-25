# rep_segmenter.py
import pandas as pd, numpy as np
from scipy.signal import find_peaks
from pathlib import Path

def segment_by_knee(df, knee_col="knee", min_prom=10, min_dist=10):
    # 낮을수록 하강 → valley 기반 분할 (운동별로 규칙 바꿔도 됨)
    inv = -df[knee_col].values
    peaks, _ = find_peaks(inv, prominence=min_prom, distance=min_dist)
    # valley 사이의 구간을 rep로
    reps = []
    for i in range(len(peaks)-1):
        s, e = int(peaks[i]), int(peaks[i+1])
        reps.append((s, e))
    return reps

def write_with_rep_ids(csv_path):
    df = pd.read_csv(csv_path)
    reps = segment_by_knee(df)
    rep_ids = np.full(len(df), -1, dtype=int)
    for rid,(s,e) in enumerate(reps, 1):
        rep_ids[s:e+1] = rid
    df["rep_id"] = rep_ids
    out = Path(csv_path).with_name(Path(csv_path).stem + "_seg.csv")
    df.to_csv(out, index=False)
    print("segmented ->", out)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    a = ap.parse_args()
    write_with_rep_ids(a.csv)
