import os, json
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

BASE_ID = "google/functiongemma-270m-it"
ADAPTER_DIR = "./clr-finetuned"

ALLOWED = {
    "hide_chat_and_focus_work",
    "rage_break",
    "soft_nudge",
    "enforce_break",
    "no_action",
}

token = os.environ.get("HF_TOKEN")
if not token:
    raise RuntimeError('HF_TOKEN not set. In PowerShell: $env:HF_TOKEN="hf_..."')

print("[GemmaDeciderLocal] Loading base model (first time only)...")
_base = AutoModelForCausalLM.from_pretrained(BASE_ID, token=token, device_map="auto")
print("[GemmaDeciderLocal] Loading LoRA adapter...")
_model = PeftModel.from_pretrained(_base, ADAPTER_DIR)
_tok = AutoTokenizer.from_pretrained(ADAPTER_DIR)
if _tok.pad_token is None:
    _tok.pad_token = _tok.eos_token
_model.eval()

def _sanitize(a: str) -> str:
    if not a:
        return "no_action"
    a = a.strip().splitlines()[0].strip().strip(' "\'`.,')
    if a in ALLOWED:
        return a
    if "hide" in a:
        return "hide_chat_and_focus_work"
    if "rage" in a:
        return "rage_break"
    if "nudge" in a:
        return "soft_nudge"
    if "break" in a:
        return "enforce_break"
    if "no_action" in a:
        return "no_action"
    return "no_action"

def get_label(state: dict) -> str:
    prompt = (
        f"Signal state: {json.dumps(state)}\n"
        f"Choose exactly one action from: {sorted(list(ALLOWED))}\n"
        f"Action:"
    )
    inputs = _tok(prompt, return_tensors="pt")
    inputs = {k: v.to(_model.device) for k, v in inputs.items()}

    with torch.no_grad():
        out = _model.generate(
            **inputs,
            max_new_tokens=10,
            do_sample=False,
            pad_token_id=_tok.eos_token_id,
        )

    decoded = _tok.decode(out[0], skip_special_tokens=True)
    raw = decoded.split("Action:")[-1].strip()
    return _sanitize(raw)