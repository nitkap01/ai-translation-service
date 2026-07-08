"""Runtime configuration.

Everything here can be overridden with environment variables so the same code
runs on a laptop (CPU/MPS) or a bigger box without edits.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

# --- Model ids ---------------------------------------------------------------
# Whisper large-v3, served through faster-whisper (a smaller, faster build of
# the same model). Set WHISPER_MODEL=large-v3 for the full weights.
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "large-v3")
# Any-language to any-language text translation.
NLLB_MODEL = os.getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
# Text-to-speech. One small model per language: facebook/mms-tts-<iso3>.
MMS_TTS_PREFIX = os.getenv("MMS_TTS_PREFIX", "facebook/mms-tts-")

# --- Runtime -----------------------------------------------------------------
# "auto" picks Apple MPS when available, else CPU. Used by the torch models
# (translation + TTS). Whisper runs on CPU via faster-whisper.
DEVICE = os.getenv("DEVICE", "auto")
# Reject uploads bigger than this so a huge file can't stall the server.
MAX_AUDIO_MB = int(os.getenv("MAX_AUDIO_MB", "25"))


def resolve_device() -> str:
    """Return the torch device to use ("mps" or "cpu")."""
    if DEVICE != "auto":
        return DEVICE
    try:
        import torch

        if torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"
