"""Data models for AI Voice Conversation System."""

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import time
import uuid


class MessageRole(str, Enum):
    """Role of a message in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationEventType(str, Enum):
    """Type of conversation event."""
    TRANSCRIPT = "transcript"
    RESPONSE = "response"
    AUDIO = "audio"
    ERROR = "error"
    DONE = "done"
    STATE_CHANGE = "state_change"


class ErrorType(str, Enum):
    """Type of error."""
    PERMISSION_DENIED = "permission_denied"
    DEVICE_NOT_FOUND = "device_not_found"
    NETWORK_ERROR = "network_error"
    ASR_ERROR = "asr_error"
    LLM_ERROR = "llm_error"
    TTS_ERROR = "tts_error"
    AUDIO_PLAYBACK_ERROR = "audio_playback_error"
    SESSION_ERROR = "session_error"
    UNKNOWN_ERROR = "unknown_error"


class Message(BaseModel):
    """A single message in conversation."""
    role: MessageRole
    content: str
    timestamp: float = Field(default_factory=time.time)

    def to_api_format(self) -> Dict[str, str]:
        """Convert to API format for LLM calls."""
        return {"role": self.role.value, "content": self.content}


class ConversationSession(BaseModel):
    """A conversation session."""
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)
    last_activity: float = Field(default_factory=time.time)

    def add_message(self, role: MessageRole, content: str) -> Message:
        """Add a message to the conversation."""
        message = Message(role=role, content=content)
        self.messages.append(message)
        self.last_activity = time.time()
        return message

    def get_api_messages(self) -> List[Dict[str, str]]:
        """Get messages in API format for LLM calls."""
        return [msg.to_api_format() for msg in self.messages]


class AudioChunk(BaseModel):
    """A chunk of audio data."""
    audio_data: str  # base64 encoded
    sample_rate: int
    index: int


class ConversationEvent(BaseModel):
    """An event in the conversation stream."""
    type: ConversationEventType
    data: Dict[str, Any]
    session_id: str

    def to_sse_format(self) -> str:
        """Format as Server-Sent Event."""
        import json
        return f"event: {self.type.value}\ndata: {json.dumps(self.data)}\n\n"


class ErrorMessage(BaseModel):
    """Error message with details."""
    error_type: ErrorType
    message: str
    details: Optional[str] = None
    retry_allowed: bool = True

    @classmethod
    def from_error_type(cls, error_type: ErrorType, details: Optional[str] = None) -> "ErrorMessage":
        """Create error message from error type."""
        messages = {
            ErrorType.PERMISSION_DENIED: "请在浏览器设置中允许访问摄像头和麦克风",
            ErrorType.DEVICE_NOT_FOUND: "未检测到摄像头或麦克风，请检查设备连接",
            ErrorType.NETWORK_ERROR: "网络连接不稳定，正在重试...",
            ErrorType.ASR_ERROR: "抱歉，没有听清楚，请再说一次",
            ErrorType.LLM_ERROR: "AI服务暂时不可用，请稍后重试",
            ErrorType.TTS_ERROR: "语音合成失败，请查看文字回复",
            ErrorType.AUDIO_PLAYBACK_ERROR: "音频播放失败",
            ErrorType.SESSION_ERROR: "会话错误，请刷新页面重试",
            ErrorType.UNKNOWN_ERROR: "发生未知错误，请稍后重试",
        }
        return cls(
            error_type=error_type,
            message=messages.get(error_type, "发生错误"),
            details=details,
            retry_allowed=error_type not in [ErrorType.PERMISSION_DENIED, ErrorType.DEVICE_NOT_FOUND]
        )
