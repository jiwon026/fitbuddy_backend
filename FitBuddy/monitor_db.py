# FitBuddy/monitor_db.py
# 데이터베이스에 저장되는 데이터를 실시간으로 모니터링하는 스크립트

import sys
import time
from pathlib import Path
from datetime import datetime

# FitBuddy 모듈을 임포트할 수 있도록 경로 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from FitBuddy.database import SessionLocal
from FitBuddy.models import Workout, WorkoutFrame
from sqlalchemy import func

def monitor_database(interval=1.0):
    """
    데이터베이스를 실시간으로 모니터링합니다.
    
    Args:
        interval: 업데이트 간격 (초)
    """
    print("=" * 70)
    print("📊 데이터베이스 실시간 모니터링 시작")
    print("=" * 70)
    print(f"업데이트 간격: {interval}초")
    print("종료하려면 Ctrl+C를 누르세요\n")
    
    last_workout_id = None
    last_frame_count = 0
    
    try:
        while True:
            with SessionLocal() as db:
                # 현재 활성 운동 세션 확인
                active_workout = db.query(Workout).filter(
                    Workout.ended_at.is_(None)
                ).order_by(Workout.started_at.desc()).first()
                
                # 전체 통계
                total_workouts = db.query(Workout).count()
                total_frames = db.query(WorkoutFrame).count()
                
                # 최근 운동 세션
                recent_workout = db.query(Workout).order_by(
                    Workout.started_at.desc()
                ).first()
                
                # 화면 클리어 (터미널에서 깔끔하게 보이도록)
                print("\033[2J\033[H", end="")  # ANSI escape codes for clear screen
                
                print("=" * 70)
                print(f"📊 데이터베이스 모니터링 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 70)
                
                # 전체 통계
                print(f"\n📈 전체 통계:")
                print(f"  총 운동 세션 수: {total_workouts}개")
                print(f"  총 프레임 수: {total_frames}개")
                
                # 활성 운동 세션
                if active_workout:
                    frames = db.query(WorkoutFrame).filter(
                        WorkoutFrame.workout_id == active_workout.workout_id
                    ).count()
                    
                    elapsed = datetime.now() - active_workout.started_at.replace(tzinfo=None)
                    elapsed_seconds = int(elapsed.total_seconds())
                    
                    print(f"\n🔥 활성 운동 세션:")
                    print(f"  Workout ID: {active_workout.workout_id}")
                    print(f"  운동 종류: {active_workout.workout_type}")
                    print(f"  시작 시간: {active_workout.started_at.strftime('%H:%M:%S')}")
                    print(f"  경과 시간: {elapsed_seconds}초")
                    print(f"  저장된 프레임: {frames}개")
                    
                    # 최근 프레임 정보
                    latest_frame = db.query(WorkoutFrame).filter(
                        WorkoutFrame.workout_id == active_workout.workout_id
                    ).order_by(WorkoutFrame.frame_number.desc()).first()
                    
                    if latest_frame:
                        print(f"\n  📸 최근 프레임 (#{latest_frame.frame_number}):")
                        print(f"     무릎 각도: {latest_frame.knee_angle:.1f}°")
                        print(f"     고관절 각도: {latest_frame.hip_angle:.1f}°")
                        print(f"     상체 기울기: {latest_frame.torso_tilt_angle:.1f}°")
                    
                    # 프레임 증가 확인
                    if frames > last_frame_count and last_workout_id == active_workout.workout_id:
                        new_frames = frames - last_frame_count
                        print(f"\n  ✨ 새로 저장된 프레임: +{new_frames}개")
                    
                    last_workout_id = active_workout.workout_id
                    last_frame_count = frames
                else:
                    print(f"\n💤 현재 활성 운동 세션이 없습니다.")
                    if recent_workout:
                        print(f"\n📋 최근 운동 세션:")
                        print(f"  Workout ID: {recent_workout.workout_id}")
                        print(f"  운동 종류: {recent_workout.workout_type}")
                        print(f"  시작: {recent_workout.started_at.strftime('%Y-%m-%d %H:%M:%S')}")
                        if recent_workout.ended_at:
                            print(f"  종료: {recent_workout.ended_at.strftime('%Y-%m-%d %H:%M:%S')}")
                            print(f"  지속 시간: {recent_workout.duration_seconds}초")
                        
                        frames = db.query(WorkoutFrame).filter(
                            WorkoutFrame.workout_id == recent_workout.workout_id
                        ).count()
                        print(f"  저장된 프레임: {frames}개")
                
                print("\n" + "=" * 70)
                print("종료: Ctrl+C")
                
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\n\n모니터링을 종료합니다.")
    except Exception as e:
        print(f"\n❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="데이터베이스 실시간 모니터링")
    parser.add_argument(
        "--interval", 
        type=float, 
        default=1.0,
        help="업데이트 간격 (초, 기본값: 1.0)"
    )
    args = parser.parse_args()
    
    monitor_database(interval=args.interval)



