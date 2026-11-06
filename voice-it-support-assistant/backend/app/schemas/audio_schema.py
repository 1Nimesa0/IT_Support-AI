"""
Pydantic Schemas for Audio Operations (ASR, TTS).
"""

from typing import Optional
from pydantic import BaseModel, Field


class TranscriptionResponse(BaseModel):
    raw_text: str = Field(..., description="Raw text output directly from Whisper ASR")
    normalized_text: str = Field(..., description="Normalized IT domain text after phonetic repair")
    confidence: float = Field(default=0.95, description="Confidence score estimated from ASR")
    duration_seconds: Optional[float] = Field(default=None, description="Audio duration in seconds")
    language: str = Field(default="vi", description="Detected language code")


class SynthesisRequest(BaseModel):
    text: str = Field(..., description="Spoken text to synthesize into speech")
    voice: Optional[str] = Field(default=None, description="Optional Edge TTS voice name")
    rate: Optional[str] = Field(default="+0%", description="Speech speed adjustment")


class AudioChunkMessage(BaseModel):
    type: str = "tts_chunk"
    audio_base64: str
    chunk_index: int
    is_final: bool = False
