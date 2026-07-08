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


def test_translate_text_to_hinglish_romanizes_but_still_speaks():
    out = pipeline.translate_text("hello", target_lang="hi-Latn", source_lang="en", speak=True)
    assert out["target_lang"] == "hi-Latn"
    assert out["target_text"].startswith("ROMAN:")  # shown in Latin letters
    assert out["audio"].startswith("data:audio/wav;base64,")  # still spoken


def test_segment_by_script_separates_latin_from_devanagari():
    from app.models.tts import _segment_by_script

    segs = _segment_by_script("Inclusio में आपका")
    assert segs[0][0] is True and "Inclusio" in segs[0][1]
    assert segs[1][0] is False


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
