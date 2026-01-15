"""ASR (Automatic Speech Recognition) Client for Zhipu AI."""

import httpx
import json
import logging
from typing import AsyncGenerator, Optional
from ..config import config
from ..utils.audio_converter import convert_webm_to_mp3

logger = logging.getLogger(__name__)


class ASRClient:
    """Client for Zhipu AI ASR API (glm-asr-2512)."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """Initialize ASR client."""
        self.api_key = api_key or config.zhipu_api_key
        self.base_url = base_url or config.zhipu_base_url
        self.model = config.asr_model
        self.stream = config.asr_stream
        
    async def transcribe_stream(
        self, 
        audio_data: bytes,
        filename: str = "audio.webm"
    ) -> AsyncGenerator[str, None]:
        """
        Transcribe audio to text using streaming API.
        
        Args:
            audio_data: Audio file bytes
            filename: Name of audio file
            
        Yields:
            Text chunks from ASR
        """
        # 智谱 AI ASR 仅支持 WAV/MP3 格式，需要将 WebM 转换为 MP3
        if filename.endswith(".webm") or filename.endswith(".opus"):
            logger.info(f"转换音频格式: {filename} -> MP3")
            audio_data = convert_webm_to_mp3(audio_data)
            filename = filename.rsplit(".", 1)[0] + ".mp3"
        
        url = f"{self.base_url}/audio/transcriptions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        files = {
            "file": (filename, audio_data, "audio/mpeg")
        }
        
        data = {
            "model": self.model,
            "stream": "true" if self.stream else "false"
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                async with client.stream(
                    "POST",
                    url,
                    headers=headers,
                    files=files,
                    data=data
                ) as response:
                    # 流式请求中需要先读取响应内容才能正确处理错误
                    if response.status_code >= 400:
                        error_content = await response.aread()
                        logger.error(f"ASR API error: {response.status_code} - {error_content.decode()}")
                        raise httpx.HTTPStatusError(
                            f"ASR API returned {response.status_code}",
                            request=response.request,
                            response=response
                        )
                    
                    # Parse SSE stream
                    async for line in response.aiter_lines():
                        line = line.strip()
                        
                        if not line:
                            continue
                            
                        # SSE format: "data: {json}"
                        if line.startswith("data:"):
                            data_str = line[5:].strip()
                            
                            # Skip [DONE] marker
                            if data_str == "[DONE]":
                                break
                                
                            try:
                                data_obj = json.loads(data_str)
                                
                                # Extract text from response
                                # Format: {"text": "...", "segments": [...]}
                                if "text" in data_obj:
                                    text = data_obj["text"]
                                    if text:
                                        yield text
                                        
                                # Alternative format with segments
                                elif "segments" in data_obj:
                                    for segment in data_obj["segments"]:
                                        if "text" in segment:
                                            text = segment["text"]
                                            if text:
                                                yield text
                                                
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse ASR response: {e}")
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"ASR API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"ASR request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected ASR error: {e}")
            raise
    
    async def transcribe(
        self,
        audio_data: bytes,
        filename: str = "audio.webm"
    ) -> str:
        """
        Transcribe audio to text (non-streaming).
        
        Args:
            audio_data: Audio file bytes
            filename: Name of audio file
            
        Returns:
            Complete transcribed text
        """
        chunks = []
        async for chunk in self.transcribe_stream(audio_data, filename):
            chunks.append(chunk)
        return "".join(chunks)
