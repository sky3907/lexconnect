import os
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

MODEL_DIR = r"C:\Users\sahit\Downloads\legal_rag\tinyllama"
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"

_model = None
_tokenizer = None

def _load_model():
    global _model, _tokenizer
    if _model is not None:
        return _model, _tokenizer

    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"🔄 Loading TinyLlama on {device}...")

    _tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
    if _tokenizer.pad_token is None:
        _tokenizer.pad_token = _tokenizer.eos_token

    _model = AutoModelForCausalLM.from_pretrained(
        MODEL_DIR,
        torch_dtype=torch.float16,
        low_cpu_mem_usage=True,
        device_map="auto",
    )
    print("✅ Model loaded!")
    return _model, _tokenizer

def calllocalslm(prompt: str, max_new_tokens: int = 300, temperature: float = 0.1) -> str:
    model, tokenizer = _load_model()
    
    # TinyLlama Chat Template - CRITICAL
    messages = [
        {"role": "system", "content": 
         "You are an Indian civil law expert. Answer legal questions directly in 4-6 sentences. "
         "NEVER give writing instructions, APA format advice, or academic guidance. "
         "Use plain English about Indian law procedures, timelines, jurisdiction."},
        {"role": "user", "content": prompt}
    ]
    
    # Apply chat template
    chat_prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    
    inputs = tokenizer(chat_prompt, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=True,
            temperature=temperature,  # Lower temp = less creative
            top_p=0.9,
            repetition_penalty=1.15,
            pad_token_id=tokenizer.eos_token_id,
        )
    
    # Decode ONLY new tokens
    new_tokens = outputs[0][inputs['input_ids'].shape[1]:]
    response = tokenizer.decode(new_tokens, skip_special_tokens=True).strip()
    
    return response if len(response) > 20 else "Under Indian law, consult a lawyer for case-specific advice."
