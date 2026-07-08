"""Audio helpers.

Two jobs:
  - decode whatever the browser or a file gives us (webm, mp3, wav, m4a...)
    into the 16 kHz mono float array Whisper expects.
  - encode a float waveform from the TTS model back into a WAV file we can
    send to the browser.

Decoding leans on ffmpeg, which handles every format the browser produces.
Encoding uses the standard-library `wave` module, so no extra dependency.
"""

import io
import subprocess
import wave

import numpy as np

TARGET_SR = 16000


def decode_to_16k_mono(data: bytes) -> np.ndarray:
    """Decode arbitrary audio bytes into a 16 kHz mono float32 array."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-nostdin",
            "-i", "pipe:0",
            "-f", "f32le",
            "-ac", "1",
            "-ar", str(TARGET_SR),
            "pipe:1",
        ],
        input=data,
        capture_output=True,
    )
    if proc.returncode != 0:
        tail = proc.stderr[-500:].decode(errors="ignore")
        raise ValueError(f"Could not decode audio: {tail}")
    samples = np.frombuffer(proc.stdout, dtype=np.float32).copy()
    if samples.size == 0:
        raise ValueError("Decoded audio is empty")
    return samples


def encode_wav(samples: np.ndarray, sample_rate: int) -> bytes:
    """Encode a float waveform ([-1, 1]) into 16-bit PCM WAV bytes."""
    samples = np.asarray(samples, dtype=np.float32).flatten()
    samples = np.clip(samples, -1.0, 1.0)
    pcm = (samples * 32767.0).astype("<i2")
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm.tobytes())
    return buf.getvalue()
