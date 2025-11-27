# Chatbot_main/service.py

import traceback
from sqlalchemy.orm import Session
from Chatbot_main.LLM.load_model import get_llm
from Chatbot_main.LLM.generate import generate_reply
from Chatbot_main.db_adapter import fetch_user_context, save_chat_log


def chat_with_pt(db: Session, user_id: int, user_message: str) -> str:
    try:
        # 1) 모델 + 토크나이저 (서버 시작 후 최초 1회만 로딩)
        model, tokenizer = get_llm()

        # 2) 사용자 컨텍스트
        context = fetch_user_context(db, user_id)

        # 3) 답변 생성
        reply = generate_reply(
            model, tokenizer,
            user_message=user_message,
            context=context
        )

        # 4) 대화 로그 저장
        save_chat_log(db, user_id, user_message, reply)

        return reply

    except Exception as e:
        error_message = f"응답 생성 중 오류가 발생했습니다: {str(e)}"
        traceback.print_exc()
        save_chat_log(db, user_id, user_message, error_message)
        # 에러는 상위(라우터)로 던져서 500 처리
        raise
