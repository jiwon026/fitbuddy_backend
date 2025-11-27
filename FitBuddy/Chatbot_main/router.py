from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import TYPE_CHECKING
import traceback

from Chatbot_main.database import get_db
from Chatbot_main.service import chat_with_pt
from Chatbot_main.auth import get_current_user

if TYPE_CHECKING:
    from Chatbot_main.auth import CurrentUser

router = APIRouter(prefix="/api", tags=["chat"])

class ChatReq(BaseModel):
    message: str

class ChatRes(BaseModel):
    reply: str

@router.post("/chat", response_model=ChatRes)   # ★ 수정됨 (/api/chat)
def chat(
    req: ChatReq,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        reply = chat_with_pt(db, user.user_id, req.message)
        return ChatRes(reply=reply)
    except Exception as e:
        traceback.print_exc()  # 서버 로그에 출력
        raise HTTPException(
            status_code=500,
            detail=f"Chatbot error: {e!r}"
        )
