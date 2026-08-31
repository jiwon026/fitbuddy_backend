# Chatbot_main/LLM/load_model.py

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-1.5B-Instruct"

_model = None
_tokenizer = None

def get_llm():
    global _model, _tokenizer

    if _model is not None and _tokenizer is not None:
        return _model, _tokenizer

    print("[LLM] 모델 로딩 시작")
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype=torch.float16
    ) 

    print("[LLM] 모델 로딩 완료")

    return _model, _tokenizer
