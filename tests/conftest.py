"""Shared test fixtures.

The three models are replaced with fast fakes for every test, so the suite
runs in milliseconds and needs none of the multi-gigabyte ML stack. The fakes
keep the same input/output shape as the real functions, so they exercise the
real pipeline, endpoints, and audio handling.
"""

import numpy as np
import pytest

from app.models import asr, tts
from app.models import translate as mt


def fake_transcribe(samples, initial_prompt=None, language=None):
    return {
        "text": "namaste duniya",
        "language": language or "hi",
        "language_probability": 0.98,
    }


def fake_translate(text, src_nllb, tgt_nllb):
    # Prefix with the target code so tests can assert translation happened.
    return f"[{tgt_nllb}] {text}"


def fake_synthesize(text, mms_code):
    # Half a second of silence at 16 kHz — enough to encode a real WAV.
    return np.zeros(8000, dtype=np.float32), 16000


@pytest.fixture(autouse=True)
def fake_models(monkeypatch):
    monkeypatch.setattr(asr, "transcribe", fake_transcribe)
    monkeypatch.setattr(mt, "translate", fake_translate)
    monkeypatch.setattr(tts, "synthesize", fake_synthesize)


@pytest.fixture
def wav_bytes():
    """A short real WAV clip for exercising the audio path."""
    from app import audio

    sr = 16000
    t = np.linspace(0, 0.5, int(sr * 0.5), endpoint=False)
    tone = (0.2 * np.sin(2 * np.pi * 220 * t)).astype(np.float32)
    return audio.encode_wav(tone, sr)
