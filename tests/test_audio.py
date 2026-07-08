import numpy as np
import pytest

from app import audio


def test_encode_wav_produces_valid_riff():
    samples = np.zeros(1600, dtype=np.float32)
    wav = audio.encode_wav(samples, 16000)
    assert wav[:4] == b"RIFF"
    assert wav[8:12] == b"WAVE"


def test_encode_then_decode_roundtrip_length():
    sr = 16000
    t = np.linspace(0, 1.0, sr, endpoint=False)
    tone = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    wav = audio.encode_wav(tone, sr)

    decoded = audio.decode_to_16k_mono(wav)
    # One second at 16 kHz, allow small codec padding.
    assert abs(len(decoded) - sr) < 500
    assert np.isfinite(decoded).all()


def test_decode_rejects_garbage():
    with pytest.raises(ValueError):
        audio.decode_to_16k_mono(b"this is not audio")
