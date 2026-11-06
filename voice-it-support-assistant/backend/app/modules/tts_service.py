"""
Text-to-Speech (TTS) Service with Inverse Text Normalization (ITN).
Utilizes Edge-TTS (Azure Speech backend) for streaming natural Vietnamese voice (vi-VN-HoaiMyNeural).
"""

from __future__ import annotations
import re
import io
import asyncio
from typing import AsyncGenerator, Optional
from app.core.config import settings
from app.core.logging import logger

try:
    import edge_tts
except ImportError:
    edge_tts = None


class TTSService:
    # Inverse Text Normalization (ITN) replacements for clear Vietnamese speech synthesis
    ITN_REPLACEMENTS = [
        # Command syntax and punctuation with pauses
        (r"\bipconfig\b", "ai-pi con-phích"),
        (r"\bping\s+8\.8\.8\.8\b", "ping, 8 chấm 8, chấm 8, chấm 8"),
        (r"\b1\.1\.1\.1\b", "1 chấm 1, chấm 1, chấm 1"),
        (r"\bcmd\b", "c m d"),
        (r"\bDHCP\b", "đê hắt xê bê"),
        (r"\bSSID\b", "ét ét ai đi"),
        (r"\bVPN\b", "vê phê en"),
        (r"\bMFA\b", "mờ ép a"),
        (r"\bOTP\b", "ô tê pê"),
        (r"\bActive Directory\b", "Ác-típ Đai-réc-tơ-ri"),
        (r"\bDNS\b", "đê nờ ét"),
        (r"\bURL\b", "u r l"),
        (r"\bWin\s*\+\s*R\b", "Windows cộng R"),
        (r"\bCtrl\s*\+\s*Shift\s*\+\s*Delete\b", "Ctrl cộng Shift cộng Delete"),
        (r"\bneverssl\.com\b", "ne-vơ ét ét eo chấm com"),
        (r"/flushdns\b", "xẹc flush d n s"),
        (r"/renew\b", "xẹc renew"),
        (r"/release\b", "xẹc release"),
    ]

    def __init__(self):
        self.default_voice = settings.TTS_VOICE
        self.rate = settings.TTS_RATE
        self.volume = settings.TTS_VOLUME

    @classmethod
    def apply_itn(cls, text: str) -> str:
        """
        Inverse Text Normalization:
        Pre-processes text to ensure technical terms and abbreviations sound natural
        when read by the Vietnamese TTS engine.
        """
        if not text:
            return ""

        formatted = text
        for pattern, replacement in cls.ITN_REPLACEMENTS:
            formatted = re.sub(pattern, replacement, formatted, flags=re.IGNORECASE)

        # Ensure commas give a natural pause after greetings or command mentions
        formatted = re.sub(r"\b(Bây giờ|Trước tiên|Tiếp tục|Cuối cùng)\b", r"\1,", formatted)
        return formatted

    async def stream_audio_chunks(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> AsyncGenerator[bytes, None]:
        """
        Asynchronously streams audio chunks from Edge-TTS for low-latency playback.
        Yields raw MP3 byte chunks as they arrive from Azure Neural endpoint.
        """
        spoken_text = self.apply_itn(text)
        selected_voice = voice or self.default_voice

        if edge_tts is not None:
            try:
                communicate = edge_tts.Communicate(
                    text=spoken_text,
                    voice=selected_voice,
                    rate=self.rate,
                    volume=self.volume,
                )
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        yield chunk["data"]
                return
            except Exception as e:
                logger.error(f"Edge-TTS streaming failed: {e}. Falling back to synthetic tone.")

        # Fallback generator for offline/test environments (silent or pulse WAV)
        fallback_audio = self._generate_silent_wav(duration_ms=500)
        yield fallback_audio

    async def synthesize_full_audio(
        self,
        text: str,
        voice: Optional[str] = None
    ) -> bytes:
        """Synthesizes the complete text into a single MP3/WAV byte buffer."""
        buffer = bytearray()
        async for chunk in self.stream_audio_chunks(text, voice):
            buffer.extend(chunk)
        return bytes(buffer)

    @staticmethod
    def _generate_silent_wav(duration_ms: int = 500) -> bytes:
        """Generates a minimal valid PCM WAV header and data for mock/fallback."""
        sample_rate = 16000
        num_samples = int(sample_rate * (duration_ms / 1000.0))
        num_channels = 1
        bits_per_sample = 16
        byte_rate = sample_rate * num_channels * bits_per_sample // 8
        block_align = num_channels * bits_per_sample // 8
        data_size = num_samples * block_align
        chunk_size = 36 + data_size

        wav_bytes = io.BytesIO()
        # RIFF header
        wav_bytes.write(b"RIFF")
        wav_bytes.write(chunk_size.to_bytes(4, "little"))
        wav_bytes.write(b"WAVE")
        # fmt chunk
        wav_bytes.write(b"fmt ")
        wav_bytes.write((16).to_bytes(4, "little"))
        wav_bytes.write((1).to_bytes(2, "little"))  # PCM
        wav_bytes.write(num_channels.to_bytes(2, "little"))
        wav_bytes.write(sample_rate.to_bytes(4, "little"))
        wav_bytes.write(byte_rate.to_bytes(4, "little"))
        wav_bytes.write(block_align.to_bytes(2, "little"))
        wav_bytes.write(bits_per_sample.to_bytes(2, "little"))
        # data chunk
        wav_bytes.write(b"data")
        wav_bytes.write(data_size.to_bytes(4, "little"))
        wav_bytes.write(b"\x00" * data_size)

        return wav_bytes.getvalue()


# Global singleton instance
tts_service = TTSService()
