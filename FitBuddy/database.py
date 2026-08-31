# FitBuddy/database.py
# FitBuddy/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# PostgreSQL DB 연결 URL
DATABASE_URL = "postgresql+psycopg2://postgres:0226@localhost:5432/fitbuddy"


# SQLAlchemy 엔진 생성
engine = create_engine(DATABASE_URL)

# DB 세션 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 SQLAlchemy 모델의 기본 클래스
Base = declarative_base()

# FastAPI 의존성 주입을 위한 DB 세션 함수 (FastAPI에서 사용)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()