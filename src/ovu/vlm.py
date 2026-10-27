"""Local vision-language model: Qwen3-VL-4B-Instruct, 4-bit (bitsandbytes nf4), ~3.5-4.5 GB VRAM."""

import json
import re

MODEL = "Qwen/Qwen3-VL-4B-Instruct"


def load_vlm():
    import torch
    from transformers import AutoModelForImageTextToText, AutoProcessor, BitsAndBytesConfig

    quant = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_compute_dtype=torch.bfloat16)
    model = AutoModelForImageTextToText.from_pretrained(MODEL, quantization_config=quant, device_map="cuda")
    return model, AutoProcessor.from_pretrained(MODEL)


def generate(model, processor, content: list[dict], max_new_tokens: int = 300, repetition_penalty: float = 1.15,
            **processor_kwargs) -> str:
    """One user turn (text, images and/or video) -> the model's answer, greedy decoding.

    repetition_penalty (applied on top of greedy decoding, so the result stays deterministic) guards against
    degenerate repetition loops (the model repeating one token/phrase until max_new_tokens cuts it off mid-answer,
    e.g. observed with a longer prompt: 700 tokens of "Schneeschuhe" and no closing JSON) - more likely the longer
    and more complex the prompt, so worth keeping on for every call, not just long ones.
    """
    import torch

    inputs = processor.apply_chat_template([{"role": "user", "content": content}], tokenize=True,
                                           add_generation_prompt=True, return_dict=True, return_tensors="pt",
                                           processor_kwargs=processor_kwargs).to(model.device)
    with torch.inference_mode():
        out = model.generate(**inputs, max_new_tokens=max_new_tokens, do_sample=False,
                             repetition_penalty=repetition_penalty)
    return processor.decode(out[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def load_json(raw: str) -> dict:
    """The outermost {...} of a model answer, or {} if there is none / it doesn't parse."""
    m = re.search(r"\{.*\}", raw, re.S)
    try:
        return json.loads(m.group(0)) if m else {}
    except json.JSONDecodeError:
        return {}


def as_text(x) -> str:
    """The model sometimes returns a list (e.g. one entry per frame); keep unique entries in order."""
    if isinstance(x, list):
        return " / ".join(dict.fromkeys(str(i).strip() for i in x if str(i).strip()))
    return str(x or "").strip()
