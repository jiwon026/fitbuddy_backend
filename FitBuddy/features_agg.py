# features_agg.py
import pandas as pd
from glob import glob
from pathlib import Path
from config import RAW, REPS

def summarize_rep(df):
    g = {}
    g["frames"] = len(df)
    g["knee_min"] = df["knee"].min()
    g["knee_max"] = df["knee"].max()
    g["knee_rom"] = g["knee_max"] - g["knee_min"]
    g["hip_min"]  = df["hip"].min()
    g["tilt_max"] = df["torso_tilt"].max()
    g["pct_deep"] = (df["knee"] < 95).mean()
    g["duration"] = (df["t"].iloc[-1] - df["t"].iloc[0]) if len(df)>1 else 0
    return g

def build_agg(exercise):
    files = glob(str(RAW / exercise / "*" / "*_seg.csv"))
    rows = []
    for fp in files:
        df = pd.read_csv(fp)
        for rid, grp in df.groupby("rep_id"):
            if rid==-1: continue
            feat = summarize_rep(grp)
            feat["exercise"] = exercise
            feat["source"] = Path(fp).name
            feat["rep_id"] = int(rid)
            rows.append(feat)
    outdir = REPS; outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / f"{exercise}_reps.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print("saved:", out)

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True)
    a = ap.parse_args()
    build_agg(a.exercise)
