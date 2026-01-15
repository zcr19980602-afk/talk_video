"""TTS (Text-to-Speech) Client for Zhipu AI."""

import httpx
import json
import logging
from typing import AsyncGenerator, Optional
from ..models import AudioChunk
from ..config import config

logger = logging.getLogger(__name__)


class TTSClient:
    """Client for Zhipu AI TTS API (glm-tts)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """Initialize TTS client."""
        self.api_key = api_key or config.zhipu_api_key
        self.base_url = base_url or config.zhipu_base_url
        self.model = config.tts_model
        self.voice = config.tts_voice
        self.speed = config.tts_speed
        self.volume = config.tts_volume
        self.response_format = config.tts_response_format
        self.encode_format = config.tts_encode_format
        self.stream = config.tts_stream
        
    async def synthesize_stream(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None
    ) -> AsyncGenerator[AudioChunk, None]:
        """
        Synthesize text to speech using streaming API.
        
        Args:
            text: Text to synthesize
            voice: Voice to use (default: female)
            speed: Speech speed (0.5-2.0)
            volume: Speech volume (0.0-2.0)
            
        Yields:
            AudioChunk objects with base64 encoded audio
        """
        url = f"{self.base_url}/audio/speech"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "input": text,
            "voice": voice or self.voice,
            "response_format": self.response_format,
            "encode_format": self.encode_format,
            "stream": self.stream,
            "speed": speed or self.speed,
            "volume": volume or self.volume
        }
        
        chunk_index = 0
        
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    json=payload
                ) as response:
                    response.raise_for_status()
                    
                    # Parse SSE stream
                    async for line in response.aiter_lines():
                        line = line.strip()
                        
                        if not line:
                            continue
                            
                        # SSE format: "data: {json}"
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            
                            try:
                                data_obj = json.loads(data_str)
                                
                                # Extract audio data
                                # Format: {"choices": [{"delta": {"content": "base64...", "return_sample_rate": 24000}}]}
                                if "choices" in data_obj and len(data_obj["choices"]) > 0:
                                    choice = data_obj["choices"][0]
                                    
                                    # Check for finish reason
                                    if "finish_reason" in choice and choice["finish_reason"] == "stop":
                                        break
                                    
                                    if "delta" in choice:
                                        delta = choice["delta"]
                                        
                                        # Extract audio content and sample rate
                                        if "content" in delta:
                                            audio_data = delta["content"]
                                            sample_rate = delta.get("return_sample_rate", 24000)
                                            
                                            if audio_data:
                                                yield AudioChunk(
                                                    audio_data=audio_data,
                                                    sample_rate=sample_rate,
                                                    index=chunk_index
                                                )
                                                chunk_index += 1
                                                
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse TTS response: {e}")
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"TTS API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"TTS request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected TTS error: {e}")
            raise
    
    async def synthesize(
        self,
        text: str,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        volume: Optional[float] = None
    ) -> list[AudioChunk]:
        """
        Synthesize text to speech (non-streaming).
        
        Args:
            text: Text to synthesize
            voice: Voice to use
            speed: Speech speed
            volume: Speech volume
            
        Returns:
            List of AudioChunk objects
        """
        chunks = []
        async for chunk in self.synthesize_stream(text, voice, speed, volume):
            chunks.append(chunk)
        return chunks
