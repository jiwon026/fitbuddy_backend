# extract_from_images.py
# 정자세/오자세 라벨링된 이미지에서 관절 좌표를 추출하여 학습 데이터 생성
# 사용법:
#   python extract_from_images.py --exercise squat --good_dir data/images/squat/good --bad_dir data/images/squat/bad

import argparse
import cv2
import pandas as pd
import numpy as np
from pathlib import Path
from pose_detector import PoseDetector
from angles import extract_angles
from config import DATA

def extract_features_from_image(image_path, pose_detector):
    """이미지에서 관절 좌표를 추출하고 피처 계산"""
    img = cv2.imread(str(image_path))
    if img is None:
        return None
    
    h, w = img.shape[:2]
    lms = pose_detector.process(img)
    
    if lms is None:
        return None
    
    kpts = pose_detector.to_numpy()
    if kpts is None:
        return None
    
    # 각도 추출
    ang = extract_angles(kpts, side='right', w=w, h=h)
    
    # 추가 피처 계산
    # 무릎, 고관절, 상체 기울기
    features = {
        'knee': float(ang['knee']),
        'hip': float(ang['hip']),
        'torso_tilt': float(ang['torso_tilt']),
        'image_path': str(image_path),
    }
    
    return features

def process_images(exercise, good_dir, bad_dir, output_path):
    """정자세/오자세 이미지 디렉토리에서 피처 추출"""
    pose = PoseDetector(model_complexity=1)
    
    good_dir = Path(good_dir)
    bad_dir = Path(bad_dir)
    
    rows = []
    
    # 정자세 이미지 처리
    if good_dir.exists():
        print(f"Processing good posture images from {good_dir}...")
        for img_path in good_dir.glob("*.jpg"):
            feat = extract_features_from_image(img_path, pose)
            if feat:
                feat['label'] = 1  # 정자세
                feat['label_name'] = 'good'
                rows.append(feat)
        for img_path in good_dir.glob("*.png"):
            feat = extract_features_from_image(img_path, pose)
            if feat:
                feat['label'] = 1
                feat['label_name'] = 'good'
                rows.append(feat)
        print(f"  Found {len([r for r in rows if r['label'] == 1])} good posture images")
    
    # 오자세 이미지 처리
    if bad_dir.exists():
        print(f"Processing bad posture images from {bad_dir}...")
        bad_count = 0
        for img_path in bad_dir.glob("*.jpg"):
            feat = extract_features_from_image(img_path, pose)
            if feat:
                feat['label'] = 0  # 오자세
                feat['label_name'] = 'bad'
                rows.append(feat)
                bad_count += 1
        for img_path in bad_dir.glob("*.png"):
            feat = extract_features_from_image(img_path, pose)
            if feat:
                feat['label'] = 0
                feat['label_name'] = 'bad'
                rows.append(feat)
                bad_count += 1
        print(f"  Found {bad_count} bad posture images")
    
    if not rows:
        print("Error: No images processed. Check directory paths.")
        return
    
    # DataFrame으로 변환 및 저장
    df = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"\nSaved {len(df)} samples to {output_path}")
    print(f"  Good: {len(df[df['label'] == 1])} samples")
    print(f"  Bad: {len(df[df['label'] == 0])} samples")
    
    return df

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Extract pose features from labeled images")
    ap.add_argument("--exercise", required=True, help="Exercise name (e.g., squat)")
    ap.add_argument("--good_dir", required=True, help="Directory containing good posture images")
    ap.add_argument("--bad_dir", required=True, help="Directory containing bad posture images")
    ap.add_argument("--output", default=None, help="Output CSV path (default: data/labeled/{exercise}_labeled.csv)")
    args = ap.parse_args()
    
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = DATA / "labeled" / f"{args.exercise}_labeled.csv"
    
    process_images(args.exercise, args.good_dir, args.bad_dir, output_path)

