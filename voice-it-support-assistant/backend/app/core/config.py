"""
Application Configuration using Pydantic Settings.
Loads environment variables from .env or system environment.
"""

import os
from typing import List, Optional
try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    from pydantic import BaseModel as BaseSettings
    SettingsConfigDict = None


class Settings(BaseSettings):
    PROJECT_NAME: str = "Voice-Based IT Support Assistant"
    API_V1_STR: str = "/api/v1"
    
    # External Speech & LLM APIs
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY", "")
    
    # Model Configurations
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    GROQ_WHISPER_MODEL: str = os.getenv("GROQ_WHISPER_MODEL", "whisper-large-v3")
    
    # Vietnamese TTS Voice (Edge TTS Azure Neural)
    # Options: vi-VN-HoaiMyNeural (female natural), vi-VN-NamMinhNeural (male natural)
    TTS_VOICE: str = os.getenv("TTS_VOICE", "vi-VN-HoaiMyNeural")
    TTS_RATE: str = os.getenv("TTS_RATE", "+0%")
    TTS_VOLUME: str = os.getenv("TTS_VOLUME", "+0%")
    
    # Server Settings
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    CORS_ORIGINS: List[str] = ["*"]
    
    # Mock / Sandbox fallback for development without active API keys
    FORCE_MOCK: bool = os.getenv("FORCE_MOCK", "false").lower() in ("true", "1", "yes")

    @property
    def is_mock_mode(self) -> bool:
        if self.FORCE_MOCK:
            return True
        return not bool(self.GROQ_API_KEY or self.OPENAI_API_KEY)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    ) if SettingsConfigDict else None


settings = Settings()
