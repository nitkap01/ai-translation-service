import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json() == {"status": "ok"}


def test_languages_endpoint_lists_hindi():
    data = client.get("/api/languages").json()
    codes = [lang["code"] for lang in data["languages"]]
    assert "hi" in codes and "en" in codes


def test_translate_text_endpoint():
    res = client.post(
        "/api/translate/text",
        json={"text": "hello", "target_lang": "hi", "source_lang": "en"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["target_text"] == "[hin_Deva] hello"
    assert body["audio"].startswith("data:audio/wav;base64,")


def test_translate_text_rejects_empty():
    res = client.post("/api/translate/text", json={"text": "  ", "target_lang": "hi"})
    assert res.status_code == 400


def test_translate_text_rejects_unknown_language():
    res = client.post(
        "/api/translate/text", json={"text": "hi", "target_lang": "zz"}
    )
    assert res.status_code == 400


def test_translate_audio_endpoint(wav_bytes):
    res = client.post(
        "/api/translate/audio",
        files={"file": ("clip.wav", wav_bytes, "audio/wav")},
        data={"target_lang": "en", "source_lang": "hi", "speak": "true"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["source_text"] == "namaste duniya"
    assert body["target_text"] == "[eng_Latn] namaste duniya"


def test_translate_audio_rejects_empty_file():
    res = client.post(
        "/api/translate/audio",
        files={"file": ("clip.wav", b"", "audio/wav")},
        data={"target_lang": "en"},
    )
    assert res.status_code == 400


def test_ui_is_served():
    res = client.get("/")
    assert res.status_code == 200
    assert "AI Translation Service" in res.text
