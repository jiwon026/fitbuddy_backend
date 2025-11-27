import torch
from typing import Optional
from Chatbot_main.LLM.prompts import build_messages

def generate_reply(model, tokenizer, user_message: str, context: Optional[dict] = None) -> str:
    # 1) 메시지 → chat template 텍스트
    messages = build_messages(user_message, context)

    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )

    # 2) 프롬프트 길이 제한 (너무 길면 속도가 기하급수적으로 느려짐)
    inputs = tokenizer(
        [text],
        return_tensors="pt",
        truncation=True,     # 🔹 길면 잘라버리기
        max_length=512       # 🔹 프롬프트 최대 길이 제한
    )

    # 모델이 올라가 있는 디바이스로 이동
    inputs = {k: v.to(model.device) for k, v in inputs.items()}

    # 3) 생성 길이/샘플링 설정
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=200,             # 🔹 256 → 128 로 줄이기 (속도↑)
            do_sample=True,
            temperature=0.7,
            top_p=0.9,
            pad_token_id=tokenizer.eos_token_id,  # 🔹 패딩 토큰 지정(경고 방지)
        )

    # 4) 입력 프롬프트 이후 부분만 추출
    gen_tokens = outputs[0][inputs["input_ids"].shape[-1]:]
    reply = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()

    return reply
