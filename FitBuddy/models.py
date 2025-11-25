# FitBuddy/models.py

from sqlalchemy import Column, Integer, String, DECIMAL, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

# 같은 폴더에 있는 database.py에서 Base를 불러옴
from database import Base

class SportsFacility(Base):
    __tablename__ = "sports_facilities" # DB에 생성될 테이블 이름

    id = Column(Integer, primary_key=True, index=True) # 기본 키, 자동 증가
    
    # 체육 시설 기본 정보
    alsfc_nm = Column(String(200), nullable=False) # 체육시설명
    alsfc_sdiv_nm = Column(String(200)) # 체육시설구분명
    alsfc_ty_nm = Column(String(200)) # 체육시설유형명
    alsfc_ctprvn_cd = Column(String(30)) # 체육시설시도코드
    alsfc_ctprvn_nm = Column(String(200)) # 체육시설시도명
    alsfc_signgu_cd = Column(String(30)) # 체육시설시군구코드
    alsfc_signgu_nm = Column(String(200)) # 체육시설시군구명
    alsfc_addr = Column(String(200)) # 체육시설주소
    
    # 체육시설 위치 정보 (위도/경도 및 PostGIS Point)
    alsfc_la = Column(DECIMAL(10, 8)) # 체육시설 위도 (DECIMAL(10, 8)은 총 10자리, 소수점 8자리)
    alsfc_lo = Column(DECIMAL(11, 8)) # 체육시설 경도 (DECIMAL(11, 8)은 총 11자리, 소수점 8자리)
    geom = Column(Geometry('POINT', srid=4326)) # 체육시설 PostGIS 포인트 (SRID 4326은 WGS84 위경도)
    
    # 대중교통 정보
    pbt_sdiv_nm = Column(String(200)) # 대중교통시설구분명
    strt_dstnc_value = Column(DECIMAL(28, 5)) # 직선거리값
    wlkg_dstnc_value = Column(DECIMAL(28, 5)) # 도보거리값
    wlkg_mvmn_time = Column(DECIMAL(30)) # 도보이동시간
    bstp_subwayst_nm = Column(String(200)) # 정류장지하철역명
    pbt_fclty_la = Column(DECIMAL(10, 8)) # 대중교통시설 위도
    pbt_fclty_lo = Column(DECIMAL(11, 8)) # 대중교통시설 경도
    pbt_fclty_geom = Column(Geometry('POINT', srid=4326)) # 대중교통시설 PostGIS 포인트


class User(Base):
    """사용자 정보를 저장하는 테이블"""
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True) # 기본 키, 자동 증가
    
    # 회원가입 정보
    email = Column(String(100), unique=True, nullable=False, index=True) # 이메일 (고유, 로그인용)
    name = Column(String(50), nullable=False) # 이름
    password_hash = Column(String(255), nullable=False) # 비밀번호 해시
    
    # 사용자 정보
    height_cm = Column(Integer) # 키 (cm)
    weight_kg = Column(DECIMAL(5, 2)) # 몸무게 (kg)
    gender = Column(String(10)) # 성별 ("male", "female", "other")
    workout_goal = Column(String(100)) # 운동 목적 (예: "체중 감량", "근력 향상", "건강 유지")
    
    # 타임스탬프
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # 가입일시
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) # 수정일시
    
    # 관계 설정: 한 사용자가 여러 운동 세션을 가질 수 있음
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")


class Workout(Base):
    """운동 세션 정보를 저장하는 테이블"""
    __tablename__ = "workouts"
    
    workout_id = Column(Integer, primary_key=True, index=True) # 기본 키, 자동 증가
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True) # 사용자 ID
    workout_type = Column(String(50), nullable=False) # 운동 종류 (예: "squat", "pushup")
    started_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False) # 시작 시간
    ended_at = Column(DateTime(timezone=True)) # 종료 시간
    duration_seconds = Column(Integer) # 운동 지속 시간 (초)
    distance_km = Column(DECIMAL(10, 3)) # 이동 거리 (km, 달리기 등에 사용)
    
    # 관계 설정
    user = relationship("User", back_populates="workouts")
    frames = relationship("WorkoutFrame", back_populates="workout", cascade="all, delete-orphan")


class WorkoutFrame(Base):
    """운동 중 각 프레임의 상세 데이터를 저장하는 테이블"""
    __tablename__ = "workout_frames"
    
    frame_id = Column(Integer, primary_key=True, index=True) # 기본 키, 자동 증가
    workout_id = Column(Integer, ForeignKey("workouts.workout_id", ondelete="CASCADE"), nullable=False, index=True) # 운동 세션 ID
    frame_number = Column(Integer, nullable=False) # 프레임 번호 (세션 내 순서)
    knee_angle = Column(Float) # 무릎 각도
    hip_angle = Column(Float) # 고관절 각도
    torso_tilt_angle = Column(Float) # 상체 기울기 각도
    keypoints_json = Column(Text) # 키포인트 데이터 (JSON 문자열)
    main_joint_location = Column(Geometry('POINT', srid=4326)) # 주요 관절 위치 (PostGIS Point, 픽셀 좌표)
    
    # 관계 설정
    workout = relationship("Workout", back_populates="frames")