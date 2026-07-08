"""Text translation with NLLB-200.

NLLB translates between any pair of its 200 languages, so unlike Whisper's
built-in "translate to English" it can go, say, Hindi -> French directly.
"""

from functools import lru_cache

from app import config


@lru_cache(maxsize=1)
def _model_and_tokenizer():
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

    tokenizer = AutoTokenizer.from_pretrained(config.NLLB_MODEL)
    model = AutoModelForSeq2SeqLM.from_pretrained(config.NLLB_MODEL)
    device = config.resolve_device()
    model.to(device)
    model.eval()
    return model, tokenizer, device


def translate(text: str, src_nllb: str, tgt_nllb: str) -> str:
    """Translate `text` from one FLORES-200 code to another."""
    text = text.strip()
    if not text:
        return ""

    import torch

    model, tokenizer, device = _model_and_tokenizer()
    tokenizer.src_lang = src_nllb
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    inputs = {key: value.to(device) for key, value in inputs.items()}
    forced_bos = tokenizer.convert_tokens_to_ids(tgt_nllb)
    with torch.no_grad():
        generated = model.generate(
            **inputs,
            forced_bos_token_id=forced_bos,
            max_length=512,
            num_beams=4,
        )
    return tokenizer.batch_decode(generated, skip_special_tokens=True)[0].strip()


def preload() -> None:
    """Load the model into memory now, so the first request isn't slow."""
    _model_and_tokenizer()
