"""FastAPI app: JSON API plus the static web UI.

Endpoints:
  GET  /api/languages        -> supported languages for the dropdowns
  POST /api/translate/text   -> translate typed text (+ optional speech)
  POST /api/translate/audio  -> transcribe + translate audio (+ optional speech)
  GET  /                     -> the web UI (served from ../web)
"""

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config, languages, pipeline

app = FastAPI(title="AI Translation Service", version="0.1.0")


class TextRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str | None = None
    speak: bool = True


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/languages")
def list_languages() -> dict:
    return {"languages": languages.public_list()}


@app.post("/api/translate/text")
def translate_text_endpoint(req: TextRequest) -> dict:
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")
    if languages.get(req.target_lang) is None:
        raise HTTPException(status_code=400, detail="unknown target_lang")
    if req.source_lang and languages.get(req.source_lang) is None:
        raise HTTPException(status_code=400, detail="unknown source_lang")
    return pipeline.translate_text(
        req.text, req.target_lang, req.source_lang, req.speak
    )


@app.post("/api/translate/audio")
async def translate_audio_endpoint(
    file: UploadFile = File(...),
    target_lang: str = Form(...),
    source_lang: str | None = Form(None),
    hints: str | None = Form(None),
    speak: bool = Form(True),
) -> dict:
    if languages.get(target_lang) is None:
        raise HTTPException(status_code=400, detail="unknown target_lang")
    if source_lang and languages.get(source_lang) is None:
        raise HTTPException(status_code=400, detail="unknown source_lang")
    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="empty audio")
    if len(data) > config.MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail="audio too large")
    return pipeline.translate_audio(data, target_lang, source_lang, hints, speak)


# Serve the UI. Mounted last so the /api routes above take priority.
app.mount("/", StaticFiles(directory=str(config.WEB_DIR), html=True), name="web")
