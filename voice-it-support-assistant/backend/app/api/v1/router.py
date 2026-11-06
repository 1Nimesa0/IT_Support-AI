"""
API v1 Router aggregation.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import audio, dialogue, sops

api_router = APIRouter()

api_router.include_router(audio.router, prefix="/audio", tags=["Audio (ASR & TTS)"])
api_router.include_router(dialogue.router, prefix="/dialogue", tags=["Dialogue Management"])
api_router.include_router(sops.router, prefix="/sops", tags=["SOP Knowledge Base"])
