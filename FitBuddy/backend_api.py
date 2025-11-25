from typing import Dict

import base64
import cv2
from models import Base
from database import engine
import numpy as np
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from pose_detector import PoseDetector
from angles import extract_angles
from database import SessionLocal, get_db
from models import User
from user_manager import hash_password
from typing import Dict
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()
Base.metadata.create_all(bind=engine)

# CORS 설정 (프론트엔드에서 접근 가능하도록)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인만 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# 요청/응답 모델 정의 (회원가입/로그인)
# ==============================
class SignupRequest(BaseModel):
    email: str
    password: str
    name: str  # 닉네임/이름


class SignupResponse(BaseModel):
    success: bool
    message: str


class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str

class UserInfoRequest(BaseModel):
    email: str              # 어떤 사용자인지 구분 (로그인에 쓰는 이메일)
    height_cm: int | None = None
    weight_kg: float | None = None
    gender: str | None = None
    workout_goal: str | None = None


class UserInfoResponse(BaseModel):
    success: bool
    message: str



# ==============================
# 포즈 분석용 요청/응답 모델
# ==============================
class PoseRequest(BaseModel):
    image_base64: str  # 클라이언트가 보내는 이미지(Base64)


class PoseResponse(BaseModel):
    knee_angle: float
    hip_angle: float
    torso_tilt: float
    feedback: str


# ==============================
# 기본 ping 엔드포인트
# ==============================
@app.get("/")
def read_root():
    return {"message": "hello from backend"}


# ==============================
# 회원가입 API
# ==============================
@app.post("/signup", response_model=SignupResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    """
    회원가입 API - PostgreSQL DB에 사용자 정보 저장
    
    SessionLocal이란?
    - SQLAlchemy의 sessionmaker로 만든 클래스
    - 데이터베이스 세션(연결)을 생성하는 팩토리
    - Depends(get_db)를 사용하면 각 요청마다 자동으로:
      1. 새로운 DB 세션 생성
      2. 요청 처리
      3. 요청 완료 후 자동으로 세션 닫기
    """
    try:
        # 이미 존재하는 이메일인지 확인
        existing_user = db.query(User).filter(User.email == req.email).first()
        if existing_user:
            return SignupResponse(success=False, message="이미 가입된 이메일입니다.")

        # 비밀번호 해시화
        password_hash = hash_password(req.password)

        # 새 사용자 생성
        new_user = User(
            email=req.email,
            name=req.name,
            password_hash=password_hash
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        print(f"[SIGNUP] {req.email} registered. user_id={new_user.user_id}")
        return SignupResponse(success=True, message="회원가입이 완료되었습니다.")

    except IntegrityError:
        db.rollback()
        return SignupResponse(success=False, message="이미 가입된 이메일입니다.")
    except Exception as e:
        db.rollback()
        print(f"[SIGNUP ERROR] {e}")
        return SignupResponse(success=False, message=f"회원가입 중 오류가 발생했습니다: {str(e)}")


# ==============================
# 로그인 API
# ==============================
@app.post("/login", response_model=LoginResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    """
    로그인 API - PostgreSQL DB에서 사용자 정보 확인
    
    Depends(get_db)를 사용하면:
    - FastAPI가 자동으로 DB 세션을 생성하고 주입
    - 함수 실행 후 자동으로 세션 닫기
    """
    try:
        # DB에서 사용자 찾기
        user = db.query(User).filter(User.email == req.email).first()

        if not user:
            return LoginResponse(success=False, message="가입되지 않은 이메일입니다.")

        # 비밀번호 확인 (해시 비교)
        password_hash = hash_password(req.password)
        if user.password_hash != password_hash:
            return LoginResponse(success=False, message="비밀번호가 올바르지 않습니다.")

        print(f"[LOGIN] {req.email} logged in. user_id={user.user_id}")
        return LoginResponse(success=True, message="로그인 성공")

    except Exception as e:
        print(f"[LOGIN ERROR] {e}")
        return LoginResponse(success=False, message=f"로그인 중 오류가 발생했습니다: {str(e)}")

# ==============================
# 사용자 정보 입력 / 수정 API
# ==============================
@app.post("/user/info", response_model=UserInfoResponse)
def update_user_info(req: UserInfoRequest, db: Session = Depends(get_db)):
    """
    회원가입 후 사용자 추가 정보 저장/수정 API
    """
    try:
        # 1. 이메일로 사용자 조회
        user = db.query(User).filter(User.email == req.email).first()
        if not user:
            return UserInfoResponse(success=False, message="해당 이메일의 사용자가 존재하지 않습니다.")

        # 2. 전달된 값들만 업데이트
        if req.height_cm is not None:
            user.height_cm = req.height_cm
        if req.weight_kg is not None:
            user.weight_kg = req.weight_kg
        if req.gender is not None:
            user.gender = req.gender
        if req.workout_goal is not None:
            user.workout_goal = req.workout_goal

        db.commit()
        db.refresh(user)

        # 🔥 요청된 전체 값 출력
        print(f"[USER_INFO] {req.email} -> {req.dict()}")

        return UserInfoResponse(success=True, message="사용자 정보가 저장되었습니다.")

    except Exception as e:
        db.rollback()
        print(f"[USER INFO ERROR] {e}")
        return UserInfoResponse(success=False, message=f"사용자 정보 저장 중 오류가 발생했습니다: {str(e)}")



# ==============================
# 포즈 분석 API
# ==============================
@app.post("/pose/analyze", response_model=PoseResponse)
def analyze_pose(req: PoseRequest):

    # 1. Base64 → OpenCV 이미지
    img_bytes = base64.b64decode(req.image_base64)
    # Base64 디코딩된 바이트를 numpy 배열로 변환
    # NumPy의 frombuffer 함수 사용 (일부 버전에서는 없을 수 있음)
    try:
        np_arr = np.frombuffer(img_bytes, dtype=np.uint8)
    except (AttributeError, TypeError):
        # 대안: bytearray를 numpy 배열로 변환
        np_arr = np.array(bytearray(img_bytes), dtype=np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return PoseResponse(
            knee_angle=-1, hip_angle=-1, torso_tilt=-1,
            feedback="이미지를 처리할 수 없습니다."
        )

    # 2. Pose detection
    pose = PoseDetector(model_complexity=1)
    lms = pose.process(frame)

    if lms is None:
        return PoseResponse(
            knee_angle=-1, hip_angle=-1, torso_tilt=-1,
            feedback="사람이 화면에 정확히 나타나지 않습니다."
        )

    kpts = pose.to_numpy()

    # 3. 각도 계산
    h, w = frame.shape[:2]
    ang = extract_angles(kpts, side='right', w=w, h=h)

    knee = float(ang.get("knee", -1))
    hip = float(ang.get("hip", -1))
    tilt = float(ang.get("torso_tilt", -1))

    # 4. 피드백 생성 로직 (예시)
    if knee < 40:
        fb = "너무 깊어요! 무릎을 조금 펴주세요."
    elif knee < 70:
        fb = "좋아요! 안정적인 자세입니다."
    elif knee < 110:
        fb = "조금 더 내려가보세요!"
    else:
        fb = "무릎을 더 굽혀야 해요!"

    # 5. 최종 응답
    return PoseResponse(
        knee_angle=knee,
        hip_angle=hip,
        torso_tilt=tilt,
        feedback=fb
    )
