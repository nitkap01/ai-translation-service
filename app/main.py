"""FastAPI app: JSON API plus the static web UI.

Endpoints:
  GET  /api/languages        -> supported languages for the dropdowns
  POST /api/translate/text   -> translate typed text (+ optional speech)
  POST /api/translate/audio  -> transcribe + translate audio (+ optional speech)
  GET  /                     -> the web UI (served from ../web)
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app import config, languages, pipeline, warmup


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start loading the models as soon as the server boots.
    warmup.start_background()
    yield


app = FastAPI(title="AI Translation Service", version="0.1.0", lifespan=lifespan)


class TextRequest(BaseModel):
    text: str
    target_lang: str
    source_lang: str | None = None
    speak: bool = True


@app.get("/api/health")
def health() -> dict:
    # Includes model warmup state: {ready, progress, error}.
    return {"status": "ok", **warmup.STATE}


@app.get("/api/languages")
def list_languages() -> dict:
    # "languages" = sources (the 12); "targets" = the 12 plus Hinglish.
    return {"languages": languages.public_list(), "targets": languages.target_list()}


@app.post("/api/translate/text")
def translate_text_endpoint(req: TextRequest) -> dict:
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="text is empty")
    if not languages.is_valid_target(req.target_lang):
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
    if not languages.is_valid_target(target_lang):
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
