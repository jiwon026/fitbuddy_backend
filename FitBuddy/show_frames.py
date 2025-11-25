#!/usr/bin/env python3
# FitBuddy/show_frames.py
# 터미널에서 프레임 데이터를 확인하는 간단한 스크립트

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from FitBuddy.database import SessionLocal
from FitBuddy.models import Workout, WorkoutFrame

def show_frames(workout_id=None, limit=20):
    """프레임 데이터를 표로 출력"""
    with SessionLocal() as db:
        if workout_id:
            frames = db.query(WorkoutFrame).filter(
                WorkoutFrame.workout_id == workout_id
            ).order_by(WorkoutFrame.frame_number.desc()).limit(limit).all()
            
            workout = db.query(Workout).filter(Workout.workout_id == workout_id).first()
            if workout:
                print(f"\n운동 세션 ID: {workout_id} ({workout.workout_type})")
        else:
            # 최신 운동 세션의 프레임
            latest_workout = db.query(Workout).order_by(Workout.started_at.desc()).first()
            if not latest_workout:
                print("❌ 저장된 데이터가 없습니다.")
                return
            
            workout_id = latest_workout.workout_id
            frames = db.query(WorkoutFrame).filter(
                WorkoutFrame.workout_id == workout_id
            ).order_by(WorkoutFrame.frame_number.desc()).limit(limit).all()
            
            print(f"\n최신 운동 세션 ID: {workout_id} ({latest_workout.workout_type})")
        
        if not frames:
            print("❌ 프레임 데이터가 없습니다.")
            return
        
        print("\n" + "=" * 80)
        print(f"{'프레임#':<8} {'무릎각도':<12} {'고관절각도':<12} {'상체기울기':<12} {'키포인트':<10}")
        print("=" * 80)
        
        for frame in reversed(frames):  # 오래된 것부터 표시
            kpts_count = "있음" if frame.keypoints_json else "없음"
            knee = f"{frame.knee_angle:.1f}°" if frame.knee_angle else "N/A"
            hip = f"{frame.hip_angle:.1f}°" if frame.hip_angle else "N/A"
            tilt = f"{frame.torso_tilt_angle:.1f}°" if frame.torso_tilt_angle else "N/A"
            
            print(f"{frame.frame_number:<8} {knee:<12} {hip:<12} {tilt:<12} {kpts_count:<10}")
        
        print("=" * 80)
        print(f"총 {len(frames)}개 프레임 표시")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="프레임 데이터 확인")
    parser.add_argument("--workout-id", type=int, help="운동 세션 ID (지정하지 않으면 최신 세션)")
    parser.add_argument("--limit", type=int, default=20, help="표시할 프레임 수 (기본값: 20)")
    args = parser.parse_args()
    
    show_frames(workout_id=args.workout_id, limit=args.limit)



