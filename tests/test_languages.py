from app import languages


def test_every_language_is_self_consistent():
    for lang in languages.LANGUAGES:
        assert languages.get(lang.code) is lang
        assert languages.get_by_whisper(lang.whisper) is lang
        assert lang.nllb and "_" in lang.nllb  # FLORES codes look like "hin_Deva"
        assert lang.mms  # ISO 639-3 present


def test_hindi_and_english_are_supported():
    assert languages.get("hi").name == "Hindi"
    assert languages.get("en").name == "English"


def test_latin_scripts_do_not_need_uroman():
    for code in ("en", "es", "fr", "de", "it", "pt"):
        assert languages.get(code).uroman is False


def test_devanagari_and_other_scripts_need_uroman():
    for code in ("hi", "ru", "ar", "bn", "ta", "mr"):
        assert languages.get(code).uroman is True


def test_unknown_and_empty_lookups_return_none():
    assert languages.get("xx") is None
    assert languages.get(None) is None
    assert languages.get_by_whisper(None) is None


def test_public_list_shape():
    items = languages.public_list()
    assert {"code", "name"} == set(items[0])
    assert any(item["code"] == "hi" for item in items)
