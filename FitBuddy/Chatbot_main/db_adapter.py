# Chatbot_main/db_adapter.py

from sqlalchemy.orm import Session

from models import User, Workout              # FitBuddy 메인 모델
from Chatbot_main.models import ChatLog       # 챗봇용 대화 로그 모델


def fetch_user_context(db: Session, user_id: int) -> dict:
    """사용자 프로필/운동 기록 등 컨텍스트 가져오기"""
    user = db.query(User).filter(User.user_id == user_id).first()
    workouts = (
        db.query(Workout)
        .filter(Workout.user_id == user_id)
        .order_by(Workout.started_at.desc())
        .limit(10)
        .all()
    )

    return {
        "user": user,
        "workouts": workouts,
    }


def save_chat_log(db: Session, user_id: int, user_message: str, bot_reply: str) -> None:
    """대화 로그 저장"""
    log = ChatLog(
        user_id=user_id,
        user_message=user_message,
        bot_reply=bot_reply,
    )
    db.add(log)
    db.commit()
