"""Load the models at startup instead of on the first request.

Loading Whisper large-v3 and NLLB into memory takes ~20-30s. Doing it lazily
means whoever sends the first translation waits for that. Instead we warm the
models in a background thread when the server boots, and expose the progress
through /api/health so the UI can show a "warming up" state and only enable the
Translate button once everything is ready.
"""

import os
import threading

from app.models import asr, tts
from app.models import translate as mt

# Voices to preload. The rest load on first use (they're small and quick).
DEFAULT_VOICES = ("eng", "hin")

STATE: dict = {"ready": False, "progress": "starting", "error": None}


def _run() -> None:
    try:
        STATE["progress"] = "loading speech model (Whisper large-v3)"
        asr.preload()
        STATE["progress"] = "loading translator (NLLB-200)"
        mt.preload()
        STATE["progress"] = "loading voices"
        for code in DEFAULT_VOICES:
            tts.preload(code)
        STATE["progress"] = "ready"
        STATE["ready"] = True
    except Exception as exc:  # noqa: BLE001 - surface the reason via /api/health
        STATE["error"] = str(exc)
        STATE["progress"] = "error"


def start_background() -> None:
    """Kick off model loading in a daemon thread (no-op if disabled)."""
    if os.getenv("DISABLE_WARMUP") == "1":
        STATE.update(ready=True, progress="warmup disabled")
        return
    threading.Thread(target=_run, name="warmup", daemon=True).start()
