import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_name = "Qwen/Qwen2.5-7B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(
    model_name,
    torch_dtype="auto",
    device_map="auto",
    trust_remote_code=True
)

messages = [
    {"role": "system", "content": "You are a helpful PT trainer."},
    {"role": "user", "content": "체지방 감량을 목표로 주 3회 운동 루틴 짧게 짜줘."}
]

text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
inputs = tokenizer([text], return_tensors="pt").to(model.device)

out = model.generate(**inputs, max_new_tokens=200)
gen = out[0][inputs.input_ids.shape[-1]:]
print(tokenizer.decode(gen, skip_special_tokens=True))
