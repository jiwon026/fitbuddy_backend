# train_baseline.py
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report
import joblib
from pathlib import Path
from config import REPS, MODELS

def train(exercise):
    df = pd.read_csv(REPS / f"{exercise}_reps.csv")
    # 임시 라벨: 깊이 충족을 good으로 (나중에 수동 라벨로 교체)
    y = (df["pct_deep"] >= 0.5).astype(int)
    X = df[["knee_min","knee_rom","hip_min","tilt_max","duration"]].fillna(0)
    # stratify는 클래스가 2개 이상일 때만 사용 가능
    if len(y.unique()) > 1:
        Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42,stratify=y)
    else:
        Xtr,Xte,ytr,yte = train_test_split(X,y,test_size=0.2,random_state=42)
    clf = RandomForestClassifier(n_estimators=200, random_state=42)
    clf.fit(Xtr,ytr)
    print(classification_report(yte, clf.predict(Xte)))
    MODELS.mkdir(exist_ok=True)
    joblib.dump(clf, MODELS / f"{exercise}_rf.pkl")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True)
    a = ap.parse_args()
    train(a.exercise)
