import cv2
import csv
import time
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import json
from pathlib import Path

# FitBuddy 디렉토리를 sys.path에 추가 (직접 실행 시)
if __name__ == "__main__":
    fitbuddy_dir = Path(__file__).parent
    if str(fitbuddy_dir) not in sys.path:
        sys.path.insert(0, str(fitbuddy_dir))

# 상대 import와 절대 import 모두 지원
try:
    from .pose_detector import PoseDetector
    from .angles import extract_angles
    from .utils import EMA, RingBuffer
    from .database import SessionLocal
    from .models import Workout, WorkoutFrame
except ImportError:
    # 직접 실행할 때를 위한 절대 import
from pose_detector import PoseDetector
from angles import extract_angles
from utils import EMA, RingBuffer
    from database import SessionLocal
    from models import Workout, WorkoutFrame

# --- PostgreSQL DB 관련 라이브러리 및 설정 (SQLAlchemy ORM 사용) ---
from geoalchemy2 import WKTElement
from sqlalchemy.orm import Session

def start_new_workout_session(user_id, workout_type):
    """새로운 운동 세션을 시작하고 workout_id를 반환합니다."""
    db: Session = SessionLocal()
    try:
        workout = Workout(
            user_id=user_id,
            workout_type=workout_type
        )
        db.add(workout)
        db.commit()
        db.refresh(workout)
        print(f"새로운 운동 세션 시작! Workout ID: {workout.workout_id}")
        return workout.workout_id
    except Exception as error:
        print(f"새로운 운동 세션 시작 실패: {error}")
        db.rollback()
        return None
    finally:
        db.close()

def update_workout_session_end_time(workout_id, duration_seconds, distance_km):
    """운동 세션 종료 시 duration_seconds와 distance_km을 업데이트합니다."""
    db: Session = SessionLocal()
    try:
        workout = db.query(Workout).filter(Workout.workout_id == workout_id).first()
        if workout:
            from datetime import datetime
            workout.ended_at = datetime.now()
            workout.duration_seconds = duration_seconds
            workout.distance_km = distance_km
            db.commit()
        print(f"운동 세션 {workout_id} 종료 시간 및 요약 정보 업데이트 완료.")
        else:
            print(f"운동 세션 {workout_id}를 찾을 수 없습니다.")
    except Exception as error:
        print(f"운동 세션 {workout_id} 업데이트 실패: {error}")
        db.rollback()
    finally:
        db.close()

def save_frame_data(workout_id, frame_number, knee_angle, hip_angle, torso_tilt_angle, kpts_data, main_joint_loc):
    """
    단일 프레임의 상세 데이터를 workout_frames 테이블에 저장하는 함수
    """
    db: Session = SessionLocal()
    try:
        # 키포인트 데이터를 JSON 문자열로 변환 (NumPy 배열은 직접 JSON 직렬화 불가)
        kpts_json_str = json.dumps(kpts_data.tolist()) if kpts_data is not None else None

        # main_joint_loc (핵심 관절 위치)를 PostGIS POINT로 변환
        point_geom = None
        if main_joint_loc:
            # 픽셀 좌표를 PostGIS Point로 변환 (SRID 4326은 위경도용이지만, 여기서는 픽셀 좌표이므로 0 사용)
            point_geom = WKTElement(f"POINT({main_joint_loc[0]:.6f} {main_joint_loc[1]:.6f})", srid=0)

        frame = WorkoutFrame(
            workout_id=workout_id,
            frame_number=frame_number,
            knee_angle=knee_angle,
            hip_angle=hip_angle,
            torso_tilt_angle=torso_tilt_angle,
            keypoints_json=kpts_json_str,
            main_joint_location=point_geom
        )
        db.add(frame)
        db.commit()
    except Exception as error:
        print(f"프레임 데이터 저장 실패: {error}")
        db.rollback()
    finally:
        db.close()

# 특정 관절 인덱스 (MediaPipe Pose)
R_HIP, R_KNEE, R_ANKLE = 24, 26, 28
R_SHOULDER = 12

def px(pt, w, h):
    """정규화 좌표를 픽셀 좌표로 변환"""
    return int(pt[0] * w), int(pt[1] * h)

def put_korean_text(frame, text, position, font_size=20, color=(255, 255, 255)):
    """한글 텍스트를 이미지에 그리기"""
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    pil_image = Image.fromarray(frame_rgb)
    draw = ImageDraw.Draw(pil_image)
    
    font = None
    font_paths = [
        "C:/Windows/Fonts/malgun.ttf",
        "/System/Library/Fonts/Supplemental/AppleSDGothicNeo.ttc",
        "/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/KoPubDotumMedium.ttf",
        "/System/Library/Fonts/Apple Color Emoji.ttc"
    ]
    
    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                font = ImageFont.truetype(font_path, font_size)
                break
        except Exception:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    b, g, r = color
    draw.text(position, text, fill=(r, g, b), font=font)
    
    frame_bgr = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
    return frame_bgr

def draw_angle_line(frame, kpts, idx_a, idx_b, idx_c, color=(0, 200, 255), label=""):
    """A-B-C 세 점을 이은 선과 B에 각도 라벨 표시"""
    h, w = frame.shape[:2]
    A = px(kpts[idx_a], w, h)
    B = px(kpts[idx_b], w, h)
    C = px(kpts[idx_c], w, h)
    cv2.line(frame, A, B, color, 2)
    cv2.line(frame, C, B, color, 2)
    if label:
        cv2.putText(frame, label, (B[0] + 8, B[1] - 8), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

def main():
    current_user_id = 1
    workout_type = "squat"
    
    active_workout_id = None
    workout_start_real_time = None
    frame_counter = 0

    # --- 데이터 저장 간격 (1.0초) 및 마지막 저장 시간 ---
    SAVE_INTERVAL_SECONDS = 1.0 
    last_save_time = time.time() 

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open camera")
        return
    pose = PoseDetector(model_complexity=1)
    ema = EMA(alpha=0.25)
    rb = RingBuffer(size=5)
    
    show_skeleton = True
    show_angle_lines = True
    
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            h, w = frame.shape[:2]
            
            lms = pose.process(frame)
            kpts_norm = None
            knee, hip, tilt = 0.0, 0.0, 0.0

            if lms is not None:
                kpts_norm = pose.to_numpy()
                if kpts_norm is not None:
                    ang = extract_angles(kpts_norm, side='right', w=w, h=h)
                    
                    knee_s = ema(ang['knee'])
                    rb.push(knee_s)
                    knee = rb.mean()
                    
                    if np.isnan(knee): knee = knee_s
                    
                    hip = ang['hip']
                    tilt = ang['torso_tilt']
                    
                    # 시각화
                    if show_skeleton:
                        pose.draw_landmarks(frame)
                    
                    if show_angle_lines:
                        draw_angle_line(frame, kpts_norm, R_HIP, R_KNEE, R_ANKLE, 
                                      (0, 200, 255), f"knee {knee:.0f}°")
                        draw_angle_line(frame, kpts_norm, R_SHOULDER, R_HIP, R_KNEE, 
                                      (255, 200, 0), f"hip {hip:.0f}°")
                    
                    cv2.putText(frame, f"knee:{knee:.1f} hip:{hip:.1f} tilt:{tilt:.1f}", 
                               (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                else:
                    if show_skeleton:
                        pose.draw_landmarks(frame)
            
            # --- 운동 세션 활성화 시 '일정 간격'으로 데이터 DB 저장 ---
            if active_workout_id is not None:
                current_real_time = time.time()
                
                # 1.0초 간격이 지났을 때만 데이터 저장
                if (current_real_time - last_save_time) >= SAVE_INTERVAL_SECONDS:
                    frame_counter += 1
                    
                    main_joint_pixel_loc = None
                    if kpts_norm is not None:
                        main_joint_pixel_loc = px(kpts_norm[R_HIP], w, h)
                    
                    save_frame_data(
                        workout_id=active_workout_id,
                        frame_number=frame_counter,
                        knee_angle=round(knee, 1),
                        hip_angle=round(hip, 1),
                        torso_tilt_angle=round(tilt, 1),
                        kpts_data=kpts_norm,
                        main_joint_loc=main_joint_pixel_loc
                    )
                    last_save_time = current_real_time # 마지막 저장 시간 업데이트
            
            # 하단 안내 메시지
            status_text = "준비 완료 (S 키로 시작)"
            if active_workout_id is not None:
                elapsed_time = int(time.time() - workout_start_real_time)
                status_text = f"기록 중 (ID: {active_workout_id}, 샘플: {frame_counter}, 시간: {elapsed_time}s)"
            
            frame = put_korean_text(frame, f"[V] 스켈레톤 [A] 각도선 [S] 시작/종료 [Q] 종료 | {status_text}", 
                                    (20, h - 30), font_size=20, color=(180, 180, 180))
            
            cv2.imshow('FitBuddy - Squat', frame)
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27 or key == ord('q') or key == ord('Q'):
                if active_workout_id is not None:
                    print(f"운동 세션 {active_workout_id} 종료 중 (Q 키).")
                    workout_end_real_time = time.time()
                    total_duration_seconds = int(workout_end_real_time - workout_start_real_time)
                    update_workout_session_end_time(active_workout_id, total_duration_seconds, 0.0)
                break
            elif key == ord('v') or key == ord('V'):
                show_skeleton = not show_skeleton
            elif key == ord('a') or key == ord('A'):
                show_angle_lines = not show_angle_lines
            elif key == ord('s') or key == ord('S'):
                if active_workout_id is None:
                    print("새로운 운동 세션 시작 준비...")
                    new_id = start_new_workout_session(current_user_id, workout_type)
                    if new_id:
                        active_workout_id = new_id
                        workout_start_real_time = time.time()
                        frame_counter = 0 
                        last_save_time = time.time() # 시작 시점에 저장 시간 초기화
                        print(f"운동 세션 {active_workout_id} 기록 시작!")
                    else:
                        print("운동 세션 시작 실패.")
                else:
                    print(f"운동 세션 {active_workout_id} 종료 중 (S 키).")
                    workout_end_real_time = time.time()
                    total_duration_seconds = int(workout_end_real_time - workout_start_real_time)
                    # 종료 시점에 workouts 테이블의 요약 정보 업데이트
                    update_workout_session_end_time(active_workout_id, total_duration_seconds, 0.0) 
                    
                    active_workout_id = None
                    workout_start_real_time = None
                    frame_counter = 0
                    print("운동 세션 기록 중지.")

            try:
                if cv2.getWindowProperty('FitBuddy - Squat', cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                break
    
    finally:
        cap.release()
        cv2.destroyAllWindows()
        print("애플리케이션 종료.")

if __name__ == "__main__":
    main()