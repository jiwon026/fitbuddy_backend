# Chatbot_main/models.py

from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

# 🔹 메인 앱의 Base, User 재사용 (절대 FitBuddy. 접두사 쓰지 말기)
from database import Base
from models import User   # FitBuddy/models.py 안의 User

class ChatLog(Base):
    """
    챗봇 대화 로그 테이블
    """
    __tablename__ = "chat_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    user_message = Column(Text, nullable=False)
    bot_reply = Column(Text, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 (옵션)
    user = relationship("User", backref="chat_logs")
