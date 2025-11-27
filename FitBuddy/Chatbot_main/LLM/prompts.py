SYSTEM_PROMPT = """
너는 전문 PT 트레이너 챗봇이다.
사용자 목표/최근 운동 기록을 참고해 개인화된 루틴/식단/운동질문 답변을 한다.
의학적 진단/질환/약물은 전문가 상담을 안내한다.
답변은 항상 자연스럽게 문장을 끝맺고, 한두 문단으로 깔끔하게 마무리한다.
"""

from typing import Optional

def build_messages(user_message: str, context: Optional[dict] = None):
    ctx_text = ""
    if context:
        ctx_text = f"\n[사용자 컨텍스트]\n{context}\n"

    return [
        {"role": "system", "content": SYSTEM_PROMPT.strip() + ctx_text},
        {"role": "user", "content": user_message.strip()}
    ]

