# Chatbot_main/database.py

"""
챗봇 모듈에서 FitBuddy의 DB 설정을 재사용
"""

from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base  # ← FitBuddy/database.py 재사용

# FastAPI 의존성 주입용
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
