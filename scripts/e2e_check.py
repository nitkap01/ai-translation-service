"""End-to-end check using the REAL models.

Runs two flows and saves the spoken output so you can listen:

  1. Text  -> translate -> speak      (English text -> Hindi text + audio)
  2. Audio -> transcribe -> translate -> speak

For flow 2 we first synthesise an English sentence with the TTS model, then
feed that audio back through the pipeline — so the whole chain (Whisper ->
NLLB -> MMS-TTS) runs on real audio without needing a sample file.

    python scripts/e2e_check.py

The first run downloads the models (Whisper large-v3, NLLB-200, and the English
+ Hindi voices), so give it time.
"""

import base64
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import audio, pipeline  # noqa: E402
from app.models import tts  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "samples"
OUT.mkdir(exist_ok=True)


def save_data_uri(data_uri: str, name: str) -> Path:
    raw = base64.b64decode(data_uri.split(",", 1)[1])
    path = OUT / name
    path.write_bytes(raw)
    return path


def main() -> int:
    ok = True

    print("\n[1/2] TEXT -> Hindi (with speech)")
    r1 = pipeline.translate_text(
        "Good morning, I hope you are doing well today.",
        target_lang="hi",
        source_lang="en",
        speak=True,
    )
    print("   source :", r1["source_text"])
    print("   hindi  :", r1["target_text"])
    if r1["target_text"] and r1["audio"]:
        p = save_data_uri(r1["audio"], "text_to_hindi.wav")
        print("   audio  :", p)
    else:
        ok = False
        print("   FAIL: missing translation or audio")

    print("\n[2/2] AUDIO -> Hindi (transcribe + translate + speak)")
    print("   (synthesising an English clip to use as input...)")
    samples, sr = tts.synthesize("This is a test of speech translation.", "eng")
    clip = audio.encode_wav(samples, sr)
    (OUT / "input_english.wav").write_bytes(clip)

    r2 = pipeline.translate_audio(clip, target_lang="hi", source_lang="en", speak=True)
    print("   heard  :", r2["source_text"], f"({r2['source_lang']}, "
          f"conf {r2['source_lang_confidence']})")
    print("   hindi  :", r2["target_text"])
    if r2["source_text"] and r2["target_text"] and r2["audio"]:
        p = save_data_uri(r2["audio"], "audio_to_hindi.wav")
        print("   audio  :", p)
    else:
        ok = False
        print("   FAIL: missing transcript, translation, or audio")

    print("\n" + ("✓ END-TO-END OK" if ok else "✗ END-TO-END FAILED"))
    print(f"  Listen to the WAV files in: {OUT}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
