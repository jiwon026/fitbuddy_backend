# train_from_images.py
# 정자세/오자세 라벨링된 이미지에서 추출한 피처로 모델 학습
# 사용법:
#   python train_from_images.py --exercise squat

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
import joblib
from pathlib import Path
from config import LABELED, MODELS

def train_from_labeled_images(exercise):
    """라벨링된 이미지에서 추출한 피처로 모델 학습"""
    csv_path = LABELED / f"{exercise}_labeled.csv"
    
    if not csv_path.exists():
        print(f"Error: {csv_path} not found.")
        print(f"Please run: python extract_from_images.py --exercise {exercise} --good_dir <good_dir> --bad_dir <bad_dir>")
        return
    
    df = pd.read_csv(csv_path)
    
    if 'label' not in df.columns:
        print("Error: 'label' column not found in CSV")
        return
    
    # 피처 선택 (각도 기반)
    feature_cols = ['knee', 'hip', 'torso_tilt']
    missing_cols = [col for col in feature_cols if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns: {missing_cols}")
        return
    
    X = df[feature_cols].fillna(0)
    y = df['label']
    
    print(f"\nTraining model for {exercise}...")
    print(f"  Total samples: {len(df)}")
    print(f"  Good posture (1): {len(df[df['label'] == 1])}")
    print(f"  Bad posture (0): {len(df[df['label'] == 0])}")
    print(f"  Features: {feature_cols}")
    
    # 데이터가 충분한지 확인
    if len(y.unique()) < 2:
        print("Error: Need both good and bad posture samples")
        return
    
    # 학습/테스트 분할
    if len(y.unique()) > 1:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    else:
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 모델 학습
    clf = RandomForestClassifier(n_estimators=200, random_state=42, max_depth=10)
    clf.fit(Xtr, ytr)
    
    # 평가
    y_pred = clf.predict(Xte)
    print("\nClassification Report:")
    print(classification_report(yte, y_pred, target_names=['bad', 'good']))
    print("\nConfusion Matrix:")
    print(confusion_matrix(yte, y_pred))
    
    # 모델 저장
    MODELS.mkdir(exist_ok=True)
    model_path = MODELS / f"{exercise}_from_images.pkl"
    joblib.dump(clf, model_path)
    print(f"\nModel saved to: {model_path}")
    
    # 피처 중요도 출력
    print("\nFeature Importance:")
    for col, imp in zip(feature_cols, clf.feature_importances_):
        print(f"  {col}: {imp:.4f}")

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--exercise", required=True, help="Exercise name (e.g., squat)")
    args = ap.parse_args()
    train_from_labeled_images(args.exercise)

