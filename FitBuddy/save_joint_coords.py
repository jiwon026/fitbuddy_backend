# save_joint_coords.py
# 카메라에서 관절 좌표를 추출하여 저장 (나중에 모델 학습용)
# 사용법:
#   python save_joint_coords.py --exercise squat --output data/raw_joints/squat_session1.csv

import argparse
import cv2
import csv
import time
import numpy as np
from pathlib import Path
from pose_detector import PoseDetector
from angles import extract_angles
from utils import EMA, RingBuffer
from config import DATA

def save_joint_coordinates(exercise, output_path, duration_sec=None):
    """
    카메라에서 관절 좌표를 추출하여 CSV로 저장
    
    Args:
        exercise: 운동 이름
        output_path: 저장할 CSV 파일 경로
        duration_sec: 녹화 시간 (초), None이면 수동 종료
    """
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    
    pose = PoseDetector(model_complexity=1)
    ema = EMA(alpha=0.25)
    rb = RingBuffer(size=5)
    
    # 출력 디렉토리 생성
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # CSV 작성 준비
    f = open(output_path, 'w', newline='', encoding='utf-8')
    
    # 관절 좌표 컬럼 (MediaPipe Pose는 33개 관절)
    joint_names = [
        'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
        'right_eye_inner', 'right_eye', 'right_eye_outer',
        'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
        'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
        'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
        'left_index', 'right_index', 'left_thumb', 'right_thumb',
        'left_hip', 'right_hip', 'left_knee', 'right_knee',
        'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
        'left_foot_index', 'right_foot_index'
    ]
    
    # CSV 헤더 작성
    fieldnames = ['timestamp', 'frame_idx']
    # 각 관절의 x, y, visibility
    for joint in joint_names:
        fieldnames.extend([f'{joint}_x', f'{joint}_y', f'{joint}_visibility'])
    # 계산된 각도
    fieldnames.extend(['knee_angle', 'hip_angle', 'torso_tilt'])
    
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    
    print(f"Recording joint coordinates...")
    print(f"Press 'q' to stop or wait {duration_sec} seconds")
    print(f"Output: {output_path}")
    
    start_time = time.time()
    frame_idx = 0
    
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            
            h, w = frame.shape[:2]
            
            # 관절 좌표 추출
            lms = pose.process(frame)
            if lms is not None:
                kpts = pose.to_numpy()
                if kpts is not None:
                    # 각도 계산
                    ang = extract_angles(kpts, side='right', w=w, h=h)
                    
                    # 각도 스무딩
                    knee_s = ema(ang['knee'])
                    rb.push(knee_s)
                    knee = rb.mean()
                    if np.isnan(knee):
                        knee = knee_s
                    
                    # CSV 행 작성
                    row = {
                        'timestamp': time.time(),
                        'frame_idx': frame_idx,
                    }
                    
                    # 관절 좌표 저장 (정규화 좌표)
                    for i, joint_name in enumerate(joint_names):
                        if i < len(kpts):
                            row[f'{joint_name}_x'] = float(kpts[i, 0])
                            row[f'{joint_name}_y'] = float(kpts[i, 1])
                            row[f'{joint_name}_visibility'] = float(kpts[i, 2])
                        else:
                            row[f'{joint_name}_x'] = 0.0
                            row[f'{joint_name}_y'] = 0.0
                            row[f'{joint_name}_visibility'] = 0.0
                    
                    # 계산된 각도 저장
                    row['knee_angle'] = float(knee)
                    row['hip_angle'] = float(ang['hip'])
                    row['torso_tilt'] = float(ang['torso_tilt'])
                    
                    writer.writerow(row)
                    
                    # 화면 표시
                    cv2.putText(frame, f"Recording... Frame: {frame_idx}", (20, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    cv2.putText(frame, f"knee:{knee:.1f} hip:{ang['hip']:.1f} tilt:{ang['torso_tilt']:.1f}",
                               (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                    
                    # 스켈레톤 표시
                    pose.draw_landmarks(frame)
            
            cv2.putText(frame, "Press 'q' to stop", (20, h - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)
            
            cv2.imshow('Recording Joint Coordinates', frame)
            
            # 종료 조건 확인
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q') or key == 27:
                break
            
            if duration_sec and (time.time() - start_time) >= duration_sec:
                break
            
            frame_idx += 1
            
            # 창 닫기 확인
            try:
                if cv2.getWindowProperty('Recording Joint Coordinates', cv2.WND_PROP_VISIBLE) < 1:
                    break
            except:
                break
    
    finally:
        f.close()
        cap.release()
        cv2.destroyAllWindows()
        print(f"\nSaved {frame_idx} frames to {output_path}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Save joint coordinates from camera")
    ap.add_argument("--exercise", required=True, help="Exercise name")
    ap.add_argument("--output", default=None, help="Output CSV path")
    ap.add_argument("--duration", type=int, default=None, help="Recording duration in seconds")
    args = ap.parse_args()
    
    if args.output:
        output_path = Path(args.output)
    else:
        timestamp = int(time.time())
        output_path = DATA / "raw_joints" / f"{args.exercise}_{timestamp}.csv"
    
    save_joint_coordinates(args.exercise, output_path, args.duration)

