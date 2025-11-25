# FitBuddy/api.py
# FastAPI를 사용한 REST API 서버

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from .database import SessionLocal, get_db
from .models import User, Workout, WorkoutFrame
from .user_manager import hash_password, verify_user as verify_user_func

app = FastAPI(title="FitBuddy API", version="1.0.0")

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

security = HTTPBearer()

# Pydantic 모델 (요청/응답 스키마)
class UserCreate(BaseModel):
    email: EmailStr
    name: str
    password: str
    password_confirm: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInfoUpdate(BaseModel):
    height_cm: Optional[int] = None
    weight_kg: Optional[float] = None
    gender: Optional[str] = None
    workout_goal: Optional[str] = None

class UserResponse(BaseModel):
    user_id: int
    email: str
    name: str
    height_cm: Optional[int]
    weight_kg: Optional[float]
    gender: Optional[str]
    workout_goal: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class WorkoutCreate(BaseModel):
    workout_type: str

class WorkoutResponse(BaseModel):
    workout_id: int
    user_id: int
    workout_type: str
    started_at: datetime
    ended_at: Optional[datetime]
    duration_seconds: Optional[int]

    class Config:
        from_attributes = True

# 인증 헬퍼 함수
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """토큰에서 사용자 정보 가져오기 (간단한 구현)"""
    # 실제로는 JWT 토큰을 검증해야 함
    # 여기서는 간단히 user_id를 토큰으로 사용
    try:
        user_id = int(credentials.credentials)
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail="사용자를 찾을 수 없습니다")
        return user
    except:
        raise HTTPException(status_code=401, detail="인증 실패")

# API 엔드포인트
@app.post("/api/auth/register", response_model=UserResponse)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """회원가입"""
    # 비밀번호 확인
    if user_data.password != user_data.password_confirm:
        raise HTTPException(status_code=400, detail="비밀번호가 일치하지 않습니다")
    
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 존재하는 이메일입니다")
    
    # 사용자 생성
    user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hash_password(user_data.password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user

@app.post("/api/auth/login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """로그인"""
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user or user.password_hash != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    
    # 실제로는 JWT 토큰을 반환해야 함
    return {
        "user_id": user.user_id,
        "email": user.email,
        "name": user.name,
        "token": str(user.user_id)  # 간단한 구현 (실제로는 JWT 사용)
    }

@app.get("/api/user/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """현재 사용자 정보 조회"""
    return current_user

@app.put("/api/user/info", response_model=UserResponse)
def update_user_info(
    user_info: UserInfoUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자 정보 업데이트"""
    if user_info.height_cm is not None:
        current_user.height_cm = user_info.height_cm
    if user_info.weight_kg is not None:
        current_user.weight_kg = user_info.weight_kg
    if user_info.gender is not None:
        current_user.gender = user_info.gender
    if user_info.workout_goal is not None:
        current_user.workout_goal = user_info.workout_goal
    
    db.commit()
    db.refresh(current_user)
    return current_user

@app.get("/api/workouts", response_model=List[WorkoutResponse])
def get_workouts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """사용자의 운동 세션 목록 조회"""
    workouts = db.query(Workout).filter(Workout.user_id == current_user.user_id).all()
    return workouts

@app.post("/api/workouts", response_model=WorkoutResponse)
def create_workout(
    workout_data: WorkoutCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """새 운동 세션 생성"""
    workout = Workout(
        user_id=current_user.user_id,
        workout_type=workout_data.workout_type
    )
    db.add(workout)
    db.commit()
    db.refresh(workout)
    return workout

@app.get("/")
def root():
    """API 상태 확인"""
    return {"message": "FitBuddy API", "status": "running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)



