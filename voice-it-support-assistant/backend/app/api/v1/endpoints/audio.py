"""
API Endpoints for Audio Operations: ASR Speech-to-Text & TTS Text-to-Speech.
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from app.modules.asr_service import asr_service
from app.modules.tts_service import tts_service
from app.schemas.audio_schema import TranscriptionResponse, SynthesisRequest

router = APIRouter()


@router.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_audio_endpoint(file: UploadFile = File(...)):
    """Transcribes an uploaded audio file (WAV/WebM/MP3) with IT domain text normalization."""
    try:
        audio_bytes = await file.read()
        if not audio_bytes:
            raise HTTPException(status_code=400, detail="Audio file cannot be empty")
        
        result = await asr_service.transcribe_audio(
            audio_bytes=audio_bytes,
            filename=file.filename or "audio.wav",
            mime_type=file.content_type or "audio/wav",
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio transcription failed: {str(e)}")


@router.post("/synthesize")
async def synthesize_speech_endpoint(request: SynthesisRequest):
    """Synthesizes text into natural Vietnamese speech (MP3 stream)."""
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    async def audio_stream():
        async for chunk in tts_service.stream_audio_chunks(request.text, request.voice):
            yield chunk

    return StreamingResponse(
        audio_stream(),
        media_type="audio/mpeg",
        headers={"Content-Disposition": "inline; filename=speech.mp3"}
    )
