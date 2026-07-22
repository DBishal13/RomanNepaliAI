"""Minimal HTTP API exposing Translator, for the hosted web demo.

The GitHub Pages demo (docs/) is static and can't run Python or hold API
keys, so real translation (as opposed to client-side transliteration) needs
this small server behind it.

Run locally:
    pip install -e ".[server]"
    uvicorn roman_nepali_ai.server:app --reload

Deploy (e.g. Render): start command
    uvicorn roman_nepali_ai.server:app --host 0.0.0.0 --port $PORT
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .translate import Translator

app = FastAPI(title="RomanNepaliAI Translation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Translator instances are reused across requests per backend (model/client
# setup can be slow, e.g. loading an HF model).
_translators: dict = {}


def _get_translator(backend: str) -> Translator:
    if backend not in _translators:
        _translators[backend] = Translator(backend=backend)
    return _translators[backend]


class TranslateRequest(BaseModel):
    text: str
    backend: str = "google"


class TranslateResponse(BaseModel):
    translation: str
    error: bool = False


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/translate", response_model=TranslateResponse)
def translate(req: TranslateRequest):
    if not req.text.strip():
        return TranslateResponse(translation="")
    try:
        translator = _get_translator(req.backend)
        out = translator.translate(req.text)
    except Exception as e:
        return TranslateResponse(translation=f"Translation failed: {e}", error=True)
    return TranslateResponse(translation=out)
