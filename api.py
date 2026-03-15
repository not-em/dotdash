"""
Q-Less Morse Code API.

Serves the static frontend files and exposes three endpoints:

    POST /api/encode   {"text": "hello"}         → {"morse": "· · · ·"}
    POST /api/decode   {"morse": "... --- ..."}   → {"text": "SOS"}
    POST /api/audio    {"text": "hello", "wpm": 20} → MP3 file

Run locally:
    uvicorn api:app --reload

Deploy (Render):
    start command: uvicorn api:app --host 0.0.0.0 --port $PORT
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from morse import encode, decode, generate_audio

_HERE = Path(__file__).parent

app = FastAPI(title="Morse Code Tool", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------

class EncodeRequest(BaseModel):
    text: str

class DecodeRequest(BaseModel):
    morse: str

class AudioRequest(BaseModel):
    text: str
    wpm: Optional[int] = 20


# ---------------------------------------------------------------------------
# Endpoints — must be registered BEFORE the static file mount
# ---------------------------------------------------------------------------

@app.post("/api/encode")
def api_encode(req: EncodeRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    return {"morse": encode(text)}


@app.post("/api/decode")
def api_decode(req: DecodeRequest):
    morse = req.morse.strip()
    if not morse:
        raise HTTPException(status_code=400, detail="No morse provided")
    return {"text": decode(morse)}


@app.post("/api/audio")
def api_audio(req: AudioRequest):
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="No text provided")
    wpm = max(5, min(40, req.wpm or 20))
    mp3 = generate_audio(text, wpm=wpm)
    return Response(content=mp3, media_type="audio/mpeg")


# ---------------------------------------------------------------------------
# Static files — serves index.html and anything else in /static
# ---------------------------------------------------------------------------

app.mount("/", StaticFiles(directory=_HERE / "static", html=True), name="static")
