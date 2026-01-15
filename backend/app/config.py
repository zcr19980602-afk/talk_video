"""API Configuration for AI Voice Conversation System."""

import os
from pathlib import Path
from pydantic import Field, BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class APIConfig(BaseSettings):
    """API configuration settings, loaded from environment variables or .env file."""
    
    # LLM Configuration (mimo-v2-flash)
    llm_api_key: str = Field(alias="LLM_API_KEY")
    llm_base_url: str = Field(default="https://api.xiaomimimo.com/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="mimo-v2-flash", alias="LLM_MODEL")
    
    # Zhipu AI Configuration (ASR & TTS)
    zhipu_api_key: str = Field(alias="ZHIPU_API_KEY")
    zhipu_base_url: str = Field(
        default="https://open.bigmodel.cn/api/paas/v4", 
        alias="ZHIPU_BASE_URL"
    )
    
    # ASR Configuration
    asr_model: str = Field(default="glm-asr-2512", alias="ASR_MODEL")
    asr_stream: bool = Field(default=True)
    
    # TTS Configuration
    tts_model: str = Field(default="glm-tts", alias="TTS_MODEL")
    tts_voice: str = Field(default="female", alias="TTS_VOICE")
    tts_speed: float = Field(default=1.0, ge=0.5, le=2.0, alias="TTS_SPEED")
    tts_volume: float = Field(default=1.0, ge=0.0, le=2.0, alias="TTS_VOLUME")
    
    # Pydantic Settings configuration
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )
    tts_response_format: str = Field(default="pcm")
    tts_encode_format: str = Field(default="base64")
    tts_stream: bool = Field(default=True)

    def mask_api_key(self, key: str) -> str:
        """Mask API key for logging (show only first 8 and last 4 chars)."""
        if len(key) <= 12:
            return "***"
        return f"{key[:8]}...{key[-4:]}"

    def get_masked_config(self) -> dict:
        """Get config with masked API keys for safe logging."""
        return {
            "llm_api_key": self.mask_api_key(self.llm_api_key),
            "llm_base_url": self.llm_base_url,
            "llm_model": self.llm_model,
            "zhipu_api_key": self.mask_api_key(self.zhipu_api_key),
            "zhipu_base_url": self.zhipu_base_url,
            "asr_model": self.asr_model,
            "tts_model": self.tts_model,
            "tts_voice": self.tts_voice,
        }


class RetryConfig(BaseModel):
    """Retry configuration for API calls."""
    max_retries: int = Field(default=3, ge=1, le=10)
    base_delay: float = Field(default=1.0, ge=0.1, le=5.0)
    max_delay: float = Field(default=10.0, ge=1.0, le=60.0)
    exponential_base: float = Field(default=2.0, ge=1.5, le=3.0)

    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = self.base_delay * (self.exponential_base ** attempt)
        return min(delay, self.max_delay)


# Global config instance
config = APIConfig()
retry_config = RetryConfig()
