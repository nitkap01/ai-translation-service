"""Pre-download every model the service needs.

Run this once after installing the ML dependencies. It fetches:
  - Whisper large-v3 (speech-to-text)
  - NLLB-200 (text translation)
  - One MMS-TTS voice per supported language (text-to-speech)

Downloads land in the Hugging Face cache (~/.cache/huggingface by default;
set HF_HOME to point somewhere with more room, e.g. an external drive).

    python scripts/download_models.py
"""

import sys
from pathlib import Path

# Make `app` importable when run as a plain script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import config, languages  # noqa: E402


def main() -> None:
    print(f"→ Whisper: {config.WHISPER_MODEL}")
    from faster_whisper import WhisperModel

    WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")

    from huggingface_hub import snapshot_download

    print(f"→ Translation: {config.NLLB_MODEL}")
    snapshot_download(config.NLLB_MODEL)

    for lang in languages.LANGUAGES:
        model_id = config.MMS_TTS_PREFIX + lang.mms
        print(f"→ Voice ({lang.name}): {model_id}")
        try:
            snapshot_download(model_id)
        except Exception as exc:  # noqa: BLE001
            print(f"  ! skipped {model_id}: {exc}")

    print("\n✓ All models downloaded.")


if __name__ == "__main__":
    main()
