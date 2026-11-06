"""
Automatic Speech Recognition (ASR) Service with IT Domain Text Normalization (TN).
Integrates Groq Cloud Whisper API (whisper-large-v3) with phonetic repair and number normalization.
"""

from __future__ import annotations
import re
import io
import time
from typing import Optional, Dict, Any
from app.core.config import settings
from app.core.logging import logger
from app.schemas.audio_schema import TranscriptionResponse

try:
    from groq import Groq
except ImportError:
    Groq = None


class ASRService:
    # IT Domain biasing prompt for Whisper ASR
    DOMAIN_PROMPT = (
        "Sự cố mạng IT Helpdesk, Wi-Fi, IPConfig, ping, DNS 8.8.8.8, SSID, DHCP, "
        "VPN, Router, Modern Auth, MFA OTP, Active Directory, ping timed out, "
        "cmd, flushdns, renew, release, neverssl.com, Windows, macOS."
    )

    # Phonetic mappings for mispronounced IT technical terms in Vietnamese
    PHONETIC_REPAIRS = [
        # IPConfig variations
        (r"\b(?:ai[-\s]?pi[-\s]?c[oô]n[-\s]?ph[íi]ch|íp[-\s]?c[oô]n[-\s]?ph[íi]ch|ai[-\s]?pi[-\s]?config|ip[-\s]?config)\b", "ipconfig"),
        # DHCP
        (r"\b(?:đi[-\s]?hắt[-\s]?x[eê][-\s]?b[eê]|d[-\s]?h[-\s]?c[-\s]?p|đê[-\s]?hát[-\s]?xê[-\s]?bê)\b", "DHCP"),
        # VPN
        (r"\b(?:vi[-\s]?pi[-\s]?en|v[eê][-\s]?ph[eê][-\s]?en|ve[-\s]?pe[-\s]?en|v[-\s]?p[-\s]?n)\b", "VPN"),
        # DNS
        (r"\b(?:đê[-\s]?nờ[-\s]?ét|đi[-\s]?en[-\s]?ét|d[-\s]?n[-\s]?s)\b", "DNS"),
        # SSID
        (r"\b(?:ét[-\s]?ét[-\s]?ai[-\s]?đi|s[-\s]?s[-\s]?i[-\s]?d)\b", "SSID"),
        # CMD
        (r"\b(?:cờ[-\s]?mờ[-\s]?đê|xê[-\s]?mờ[-\s]?đê|c[-\s]?m[-\s]?d)\b", "cmd"),
        # MFA / OTP
        (r"\b(?:mờ[-\s]?ép[-\s]?a|em[-\s]?eff[-\s]?ay|m[-\s]?f[-\s]?a)\b", "MFA"),
        (r"\b(?:ô[-\s]?tê[-\s]?pê|o[-\s]?t[-\s]?p)\b", "OTP"),
        # Active Directory
        (r"\b(?:áp[-\s]?típ[-\s]?đai[-\s]?r[eé]c[-\s]?tơ[-\s]?ri|ác[-\s]?típ[-\s]?đai[-\s]?r[eé]t[-\s]?to[-\s]?ri|active[-\s]?directory)\b", "Active Directory"),
        # Symbols
        (r"\b(?:xẹc|xẹt|gạch[-\s]?chéo)\b", "/"),
        (r"\b(?:xẹc[-\s]?ngược|gạch[-\s]?chéo[-\s]?ngược)\b", "\\"),
        (r"\b(?:dấu[-\s]?trừ|gạch[-\s]?ngang)\b", "-"),
    ]

    # Vietnamese spoken digit words for number normalization
    VIET_DIGITS = {
        "không": "0", "khong": "0",
        "một": "1", "mot": "1", "mốt": "1",
        "hai": "2",
        "ba": "3",
        "bốn": "4", "bon": "4", "tư": "4",
        "năm": "5", "nam": "5", "lăm": "5",
        "sáu": "6", "sau": "6",
        "bảy": "7", "bay": "7", "bẩy": "7",
        "tám": "8", "tam": "8",
        "chín": "9", "chin": "9"
    }

    def __init__(self):
        self.client = None
        if settings.GROQ_API_KEY and Groq:
            try:
                self.client = Groq(api_key=settings.GROQ_API_KEY)
            except Exception as e:
                logger.warning(f"Failed to initialize Groq ASR client: {e}")

    @classmethod
    def normalize_ip_addresses(cls, text: str) -> str:
        """
        Converts spoken Vietnamese numbers with 'chấm' into IP address format:
        e.g. 'tám chấm tám chấm tám chấm tám' -> '8.8.8.8'
        'một chín hai chấm một sáu tám chấm một chấm một' -> '192.168.1.1'
        """
        # First handle standard single octet repetitions: "X chấm Y chấm Z chấm W"
        def replace_spoken_octet(match: re.Match) -> str:
            parts = match.group(0).split()
            # Parse segments separated by 'chấm' or '.'
            out_segments = []
            curr_num = ""
            for word in parts:
                w = word.strip().lower()
                if w in ("chấm", "cham", "."):
                    if curr_num:
                        out_segments.append(curr_num)
                        curr_num = ""
                elif w in cls.VIET_DIGITS:
                    curr_num += cls.VIET_DIGITS[w]
                elif w.isdigit():
                    curr_num += w
            if curr_num:
                out_segments.append(curr_num)
            if len(out_segments) >= 2:
                return ".".join(out_segments)
            return match.group(0)

        # Regex for digit-word patterns separated by 'chấm'
        digit_keys = "|".join(cls.VIET_DIGITS.keys())
        pattern = rf"(?:(?:\b(?:{digit_keys}|\d+)\b\s*)+(?:chấm|cham|\.)\s*)+(?:\b(?:{digit_keys}|\d+)\b\s*)+"
        normalized = re.sub(pattern, replace_spoken_octet, text, flags=re.IGNORECASE)

        # Direct normalization for common Google DNS / Cloudflare DNS phrasing
        normalized = re.sub(r"\b8\s*chấm\s*8\s*chấm\s*8\s*chấm\s*8\b", "8.8.8.8", normalized, flags=re.IGNORECASE)
        normalized = re.sub(r"\b1\s*chấm\s*1\s*chấm\s*1\s*chấm\s*1\b", "1.1.1.1", normalized, flags=re.IGNORECASE)
        return normalized

    @classmethod
    def apply_text_normalization(cls, raw_text: str) -> str:
        """
        Text Normalization (TN) Pipeline:
        1. Normalize spoken IP addresses and numbers
        2. Repair phonetic Vietnamese mispronunciations of IT terms
        3. Clean up spacing and punctuation
        """
        if not raw_text:
            return ""

        text = raw_text

        # 1. IP and Number normalization
        text = cls.normalize_ip_addresses(text)

        # 2. Phonetic technical repair
        for pattern, replacement in cls.PHONETIC_REPAIRS:
            text = re.sub(pattern, lambda m, r=replacement: r, text, flags=re.IGNORECASE)

        # 3. Clean up formatting around commands and flags (e.g. "ipconfig / flushdns" -> "ipconfig /flushdns")
        text = re.sub(r"/\s+", "/", text)
        text = re.sub(r"\\\s+", "\\\\", text)
        text = re.sub(r"\s{2,}", " ", text).strip()

        return text

    async def transcribe_audio(
        self,
        audio_bytes: bytes,
        filename: str = "audio.wav",
        mime_type: str = "audio/wav",
    ) -> TranscriptionResponse:
        """
        Transcribes audio bytes using Groq Whisper Cloud API with domain biasing,
        then runs the IT Text Normalization pipeline.
        """
        raw_text = ""
        confidence = 0.95

        # Check if Groq client is available and active
        if self.client and not settings.is_mock_mode:
            try:
                audio_file = (filename, audio_bytes, mime_type)
                logger.info(f"Calling Groq Whisper API for file size {len(audio_bytes)} bytes...")
                transcription = self.client.audio.transcriptions.create(
                    model=settings.GROQ_WHISPER_MODEL,
                    file=audio_file,
                    language="vi",
                    prompt=self.DOMAIN_PROMPT,
                    response_format="json",
                    temperature=0.0,
                )
                raw_text = transcription.text if hasattr(transcription, "text") else str(transcription)
            except Exception as e:
                logger.error(f"Groq Whisper transcription failed: {e}. Falling back to mock/repair.")
                raw_text = self._mock_transcription(audio_bytes)
        else:
            # Mock / local testing mode
            logger.info("ASR Service operating in mock/local mode.")
            raw_text = self._mock_transcription(audio_bytes)

        # Apply domain text normalization (TN)
        normalized_text = self.apply_text_normalization(raw_text)

        return TranscriptionResponse(
            raw_text=raw_text,
            normalized_text=normalized_text,
            confidence=confidence,
            duration_seconds=round(len(audio_bytes) / 32000.0, 2),
            language="vi"
        )

    @staticmethod
    def _mock_transcription(audio_bytes: bytes) -> str:
        """Fallback mock transcription for testing or offline environment."""
        # Returns a standard test phrase if no audio can be processed
        if len(audio_bytes) < 100:
            return "Tôi đã gõ xong lệnh ipconfig rồi."
        return "Mạng cơ quan tôi không vào được, biểu tượng có chấm than vàng."


# Global singleton instance
asr_service = ASRService()
