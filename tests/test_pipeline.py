from app import pipeline


def test_translate_text_translates_and_speaks():
    out = pipeline.translate_text("hello", target_lang="hi", source_lang="en", speak=True)
    assert out["source_lang"] == "en"
    assert out["target_lang"] == "hi"
    assert out["target_text"] == "[hin_Deva] hello"
    assert out["audio"].startswith("data:audio/wav;base64,")


def test_translate_text_same_language_skips_translation():
    out = pipeline.translate_text("hello", target_lang="en", source_lang="en", speak=False)
    assert out["target_text"] == "hello"
    assert out["audio"] is None


def test_translate_text_can_skip_speech():
    out = pipeline.translate_text("hello", target_lang="hi", source_lang="en", speak=False)
    assert out["audio"] is None


def test_detect_text_language_defaults_to_english_on_junk():
    assert pipeline.detect_text_language("zzz") == "en"


def test_translate_audio_transcribes_translates_and_speaks(wav_bytes):
    out = pipeline.translate_audio(
        wav_bytes, target_lang="en", source_lang="hi", speak=True
    )
    assert out["source_text"] == "namaste duniya"  # from the fake transcriber
    assert out["source_lang"] == "hi"
    assert out["target_text"] == "[eng_Latn] namaste duniya"
    assert out["source_lang_confidence"] == 0.98
    assert out["audio"].startswith("data:audio/wav;base64,")
