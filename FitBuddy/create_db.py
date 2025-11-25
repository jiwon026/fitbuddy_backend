# FitBuddy/create_db.py

from .database import engine, Base # database.py에서 engine과 Base 임포트
from .models import SportsFacility, User, Workout, WorkoutFrame # models.py에서 모든 모델 임포트

def create_db_tables():
    print("데이터베이스 테이블을 생성합니다...")
    # Base에 정의된 모든 모델에 해당하는 테이블을 DB에 생성
    Base.metadata.create_all(bind=engine)
    print("테이블 생성 완료.")
    print("생성된 테이블:")
    print("  - users (사용자 정보)")
    print("  - sports_facilities (체육시설 정보)")
    print("  - workouts (운동 세션)")
    print("  - workout_frames (운동 프레임 데이터)")

if __name__ == "__main__":
    create_db_tables()