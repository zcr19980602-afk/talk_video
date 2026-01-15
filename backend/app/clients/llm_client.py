"""LLM Client for mimo-v2-flash."""

import httpx
import json
import logging
from typing import AsyncGenerator, List, Dict, Optional
from ..config import config

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for mimo-v2-flash LLM API (OpenAI-compatible)."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        """Initialize LLM client."""
        self.api_key = api_key or config.llm_api_key
        self.base_url = base_url or config.llm_base_url
        self.model = model or config.llm_model
        
    async def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """
        Generate chat completion using streaming API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            Text chunks from LLM
        """
        url = f"{self.base_url}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": temperature
        }
        
        if max_tokens:
            payload["max_tokens"] = max_tokens
        
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
                            
                            # Skip [DONE] marker
                            if data_str == "[DONE]":
                                break
                                
                            try:
                                data_obj = json.loads(data_str)
                                
                                # Extract delta content
                                # Format: {"choices": [{"delta": {"content": "..."}}]}
                                if "choices" in data_obj and len(data_obj["choices"]) > 0:
                                    choice = data_obj["choices"][0]
                                    
                                    if "delta" in choice:
                                        delta = choice["delta"]
                                        
                                        if "content" in delta:
                                            content = delta["content"]
                                            if content:
                                                yield content
                                                
                            except json.JSONDecodeError as e:
                                logger.warning(f"Failed to parse LLM response: {e}")
                                continue
                                
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"LLM request error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise
    
    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate chat completion (non-streaming).
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Complete response text
        """
        chunks = []
        async for chunk in self.chat_stream(messages, temperature, max_tokens):
            chunks.append(chunk)
        return "".join(chunks)
