"""Conversation Manager for coordinating ASR, LLM, and TTS."""

import logging
from typing import AsyncGenerator, Dict
from .models import (
    ConversationSession,
    ConversationEvent,
    ConversationEventType,
    MessageRole,
    ErrorType,
    ErrorMessage
)
from .clients.asr_client import ASRClient
from .clients.llm_client import LLMClient
from .clients.tts_client import TTSClient
from .state_machine import StateMachine, StateEvent, ConversationState

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation flow and coordinates API clients."""
    
    def __init__(
        self,
        asr_client: ASRClient,
        llm_client: LLMClient,
        tts_client: TTSClient
    ):
        """Initialize conversation manager."""
        self.asr_client = asr_client
        self.llm_client = llm_client
        self.tts_client = tts_client
        self.sessions: Dict[str, ConversationSession] = {}
        self.state_machines: Dict[str, StateMachine] = {}
    
    def create_session(self) -> str:
        """
        Create a new conversation session.
        
        Returns:
            Session ID
        """
        session = ConversationSession()
        self.sessions[session.session_id] = session
        self.state_machines[session.session_id] = StateMachine()
        logger.info(f"Created session: {session.session_id}")
        return session.session_id
    
    def get_session(self, session_id: str) -> ConversationSession:
        """Get session by ID."""
        if session_id not in self.sessions:
            raise ValueError(f"Session not found: {session_id}")
        return self.sessions[session_id]
    
    def get_state_machine(self, session_id: str) -> StateMachine:
        """Get state machine for session."""
        if session_id not in self.state_machines:
            raise ValueError(f"Session not found: {session_id}")
        return self.state_machines[session_id]
    
    async def process_audio(
        self,
        session_id: str,
        audio_data: bytes
    ) -> AsyncGenerator[ConversationEvent, None]:
        """
        Process audio input through ASR, LLM, and TTS pipeline.
        
        Args:
            session_id: Session ID
            audio_data: Audio file bytes
            
        Yields:
            ConversationEvent objects
        """
        session = self.get_session(session_id)
        state_machine = self.get_state_machine(session_id)
        
        try:
            # Transition to processing state
            state_machine.transition(StateEvent.AUDIO_RECEIVED)
            yield ConversationEvent(
                type=ConversationEventType.STATE_CHANGE,
                data={"state": ConversationState.PROCESSING.value},
                session_id=session_id
            )
            
            # Step 1: ASR - Transcribe audio to text
            transcript_chunks = []
            async for text_chunk in self.asr_client.transcribe_stream(audio_data):
                transcript_chunks.append(text_chunk)
                yield ConversationEvent(
                    type=ConversationEventType.TRANSCRIPT,
                    data={"text": text_chunk},
                    session_id=session_id
                )
            
            transcript = "".join(transcript_chunks)
            if not transcript:
                raise ValueError("Empty transcript")
            
            # Add user message to session
            session.add_message(MessageRole.USER, transcript)
            
            # Step 2: LLM - Generate response
            response_chunks = []
            async for response_chunk in self.llm_client.chat_stream(
                session.get_api_messages()
            ):
                response_chunks.append(response_chunk)
                yield ConversationEvent(
                    type=ConversationEventType.RESPONSE,
                    data={"text": response_chunk},
                    session_id=session_id
                )
            
            response = "".join(response_chunks)
            if not response:
                raise ValueError("Empty response")
            
            # Add assistant message to session
            session.add_message(MessageRole.ASSISTANT, response)
            
            # Transition to speaking state
            state_machine.transition(StateEvent.PROCESSING_COMPLETE)
            yield ConversationEvent(
                type=ConversationEventType.STATE_CHANGE,
                data={"state": ConversationState.SPEAKING.value},
                session_id=session_id
            )
            
            # Step 3: TTS - Synthesize speech
            async for audio_chunk in self.tts_client.synthesize_stream(response):
                yield ConversationEvent(
                    type=ConversationEventType.AUDIO,
                    data={
                        "audio": audio_chunk.audio_data,
                        "sample_rate": audio_chunk.sample_rate,
                        "index": audio_chunk.index
                    },
                    session_id=session_id
                )
            
            # Transition back to listening
            state_machine.transition(StateEvent.SPEAKING_COMPLETE)
            yield ConversationEvent(
                type=ConversationEventType.STATE_CHANGE,
                data={"state": ConversationState.LISTENING.value},
                session_id=session_id
            )
            
            # Done
            yield ConversationEvent(
                type=ConversationEventType.DONE,
                data={},
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Error processing audio: {e}")
            state_machine.transition(StateEvent.ERROR)
            
            error_msg = ErrorMessage.from_error_type(
                ErrorType.UNKNOWN_ERROR,
                details=str(e)
            )
            
            yield ConversationEvent(
                type=ConversationEventType.ERROR,
                data=error_msg.dict(),
                session_id=session_id
            )
    
    async def start_conversation(
        self,
        session_id: str,
        initial_prompt: str = "你好！我是AI助手，很高兴与你对话。请问有什么我可以帮助你的吗？"
    ) -> AsyncGenerator[ConversationEvent, None]:
        """
        Start a conversation with AI greeting.
        
        Args:
            session_id: Session ID
            initial_prompt: Initial AI greeting
            
        Yields:
            ConversationEvent objects
        """
        session = self.get_session(session_id)
        state_machine = self.get_state_machine(session_id)
        
        try:
            # Add system message
            session.add_message(MessageRole.ASSISTANT, initial_prompt)
            
            # Transition to speaking
            state_machine.force_state(ConversationState.SPEAKING)
            yield ConversationEvent(
                type=ConversationEventType.STATE_CHANGE,
                data={"state": ConversationState.SPEAKING.value},
                session_id=session_id
            )
            
            # Send response text
            yield ConversationEvent(
                type=ConversationEventType.RESPONSE,
                data={"text": initial_prompt},
                session_id=session_id
            )
            
            # Synthesize speech
            async for audio_chunk in self.tts_client.synthesize_stream(initial_prompt):
                yield ConversationEvent(
                    type=ConversationEventType.AUDIO,
                    data={
                        "audio": audio_chunk.audio_data,
                        "sample_rate": audio_chunk.sample_rate,
                        "index": audio_chunk.index
                    },
                    session_id=session_id
                )
            
            # Transition to listening
            state_machine.transition(StateEvent.SPEAKING_COMPLETE)
            yield ConversationEvent(
                type=ConversationEventType.STATE_CHANGE,
                data={"state": ConversationState.LISTENING.value},
                session_id=session_id
            )
            
            yield ConversationEvent(
                type=ConversationEventType.DONE,
                data={},
                session_id=session_id
            )
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            state_machine.transition(StateEvent.ERROR)
            
            error_msg = ErrorMessage.from_error_type(
                ErrorType.UNKNOWN_ERROR,
                details=str(e)
            )
            
            yield ConversationEvent(
                type=ConversationEventType.ERROR,
                data=error_msg.dict(),
                session_id=session_id
            )
    
    def get_conversation_history(self, session_id: str) -> list:
        """Get conversation history for session."""
        session = self.get_session(session_id)
        return [msg.dict() for msg in session.messages]
