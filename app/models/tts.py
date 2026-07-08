"""Text-to-speech with Meta MMS-TTS.

MMS ships one small VITS model per language (facebook/mms-tts-<iso3>). Models
are loaded and cached on first use.

Each voice only speaks its own script — the Hindi voice, for example, ignores
Latin letters. So for a non-Latin target we split the text by script and speak
each run with the right voice (English words with the English voice, the rest
with the target voice) and join the clips. That way a name like "Inclusio"
inside a Hindi sentence, or mixed Hinglish text, is spoken instead of dropped.
"""

import re
from functools import lru_cache

import numpy as np

from app import config

# Voice used for embedded Latin runs (names, English words) in a non-Latin target.
ENGLISH_MMS = "eng"
_LATIN_LETTER = re.compile(r"[A-Za-z]")


@lru_cache(maxsize=1)
def _uroman():
    from uroman import Uroman

    return Uroman()


def _romanize(text: str) -> str:
    return _uroman().romanize_string(text)


def romanize(text: str) -> str:
    """Transliterate native-script text to Latin (used for Hinglish output)."""
    return _romanize(text)


@lru_cache(maxsize=None)
def _model_and_tokenizer(mms_code: str):
    from transformers import AutoTokenizer, VitsModel

    model_id = config.MMS_TTS_PREFIX + mms_code
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = VitsModel.from_pretrained(model_id)
    device = config.resolve_device()
    model.to(device)
    model.eval()
    return model, tokenizer, device


def synthesize(text: str, mms_code: str):
    """Turn text into speech with a single voice. Returns (waveform, sample_rate)."""
    import torch

    model, tokenizer, device = _model_and_tokenizer(mms_code)
    # Only romanise if this particular voice was trained on romanised text.
    if getattr(tokenizer, "is_uroman", False):
        text = _romanize(text)
    inputs = tokenizer(text, return_tensors="pt")
    inputs = {key: value.to(device) for key, value in inputs.items()}
    with torch.no_grad():
        waveform = model(**inputs).waveform
    samples = waveform.squeeze().detach().cpu().numpy()
    return samples, model.config.sampling_rate


def _segment_by_script(text: str):
    """Split text into (is_latin, chunk) runs. Spaces/punctuation stick to the
    current run; the class only switches on a letter of the other script."""
    segments, current, buf = [], None, []
    for ch in text:
        if ch.isalpha():
            is_latin = bool(_LATIN_LETTER.match(ch))
        else:
            is_latin = current if current is not None else False
        if current is None:
            current = is_latin
        if ch.isalpha() and is_latin != current:
            segments.append((current, "".join(buf)))
            buf = [ch]
            current = is_latin
        else:
            buf.append(ch)
    if buf:
        segments.append((current, "".join(buf)))
    return segments


def synthesize_segmented(text: str, target_mms: str):
    """Speak text that may mix Latin words into a non-Latin script.

    Latin runs are spoken with the English voice, the rest with the target
    voice, and the clips are joined so nothing is dropped.
    """
    segments = _segment_by_script(text)
    has_latin = any(is_latin and any(c.isalpha() for c in chunk) for is_latin, chunk in segments)
    if not has_latin:
        return synthesize(text, target_mms)

    waves, sr_out = [], None
    for is_latin, chunk in segments:
        if not any(c.isalpha() for c in chunk):
            continue  # pure punctuation/space: skip (empty input would crash VITS)
        samples, sr = synthesize(chunk, ENGLISH_MMS if is_latin else target_mms)
        if sr_out is None:
            sr_out = sr
        elif sr != sr_out:
            count = max(1, round(len(samples) * sr_out / sr))
            samples = np.interp(
                np.linspace(0, len(samples), count, endpoint=False),
                np.arange(len(samples)),
                samples,
            ).astype(np.float32)
        waves.append(samples.astype(np.float32))
        waves.append(np.zeros(int(sr_out * 0.08), dtype=np.float32))  # small gap

    if not waves:
        return synthesize(text, target_mms)
    return np.concatenate(waves), sr_out


def preload(mms_code: str) -> None:
    """Load one voice into memory now, so the first request isn't slow."""
    _model_and_tokenizer(mms_code)
