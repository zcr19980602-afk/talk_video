"""Conversation State Machine for AI Voice Conversation System."""

from enum import Enum
from typing import Optional, Set, Callable
from dataclasses import dataclass, field


class ConversationState(str, Enum):
    """States of the conversation."""
    IDLE = "idle"
    LISTENING = "listening"
    PROCESSING = "processing"
    SPEAKING = "speaking"


class StateEvent(str, Enum):
    """Events that trigger state transitions."""
    START_LISTENING = "start_listening"
    AUDIO_RECEIVED = "audio_received"
    PROCESSING_COMPLETE = "processing_complete"
    SPEAKING_COMPLETE = "speaking_complete"
    USER_INTERRUPT = "user_interrupt"
    ERROR = "error"
    RESET = "reset"


# Valid state transitions
VALID_TRANSITIONS: dict[ConversationState, dict[StateEvent, ConversationState]] = {
    ConversationState.IDLE: {
        StateEvent.START_LISTENING: ConversationState.LISTENING,
        StateEvent.RESET: ConversationState.IDLE,
    },
    ConversationState.LISTENING: {
        StateEvent.AUDIO_RECEIVED: ConversationState.PROCESSING,
        StateEvent.ERROR: ConversationState.IDLE,
        StateEvent.RESET: ConversationState.IDLE,
    },
    ConversationState.PROCESSING: {
        StateEvent.PROCESSING_COMPLETE: ConversationState.SPEAKING,
        StateEvent.ERROR: ConversationState.IDLE,
        StateEvent.RESET: ConversationState.IDLE,
    },
    ConversationState.SPEAKING: {
        StateEvent.SPEAKING_COMPLETE: ConversationState.LISTENING,
        StateEvent.USER_INTERRUPT: ConversationState.LISTENING,
        StateEvent.ERROR: ConversationState.IDLE,
        StateEvent.RESET: ConversationState.IDLE,
    },
}


@dataclass
class StateMachine:
    """State machine for managing conversation flow."""
    
    current_state: ConversationState = ConversationState.IDLE
    _listeners: list[Callable[[ConversationState, ConversationState], None]] = field(
        default_factory=list
    )

    def get_state(self) -> ConversationState:
        """Get current state."""
        return self.current_state

    def can_transition(self, event: StateEvent) -> bool:
        """Check if transition is valid for given event."""
        transitions = VALID_TRANSITIONS.get(self.current_state, {})
        return event in transitions

    def get_valid_events(self) -> Set[StateEvent]:
        """Get all valid events for current state."""
        transitions = VALID_TRANSITIONS.get(self.current_state, {})
        return set(transitions.keys())

    def transition(self, event: StateEvent) -> bool:
        """
        Attempt to transition to new state based on event.
        
        Returns True if transition was successful, False otherwise.
        """
        transitions = VALID_TRANSITIONS.get(self.current_state, {})
        new_state = transitions.get(event)
        
        if new_state is None:
            return False
        
        old_state = self.current_state
        self.current_state = new_state
        
        # Notify listeners
        for listener in self._listeners:
            listener(old_state, new_state)
        
        return True

    def force_state(self, state: ConversationState) -> None:
        """Force state change (use with caution)."""
        old_state = self.current_state
        self.current_state = state
        for listener in self._listeners:
            listener(old_state, state)

    def reset(self) -> None:
        """Reset to idle state."""
        self.transition(StateEvent.RESET)

    def add_listener(
        self, 
        listener: Callable[[ConversationState, ConversationState], None]
    ) -> None:
        """Add state change listener."""
        self._listeners.append(listener)

    def remove_listener(
        self, 
        listener: Callable[[ConversationState, ConversationState], None]
    ) -> None:
        """Remove state change listener."""
        if listener in self._listeners:
            self._listeners.remove(listener)

    def is_idle(self) -> bool:
        """Check if in idle state."""
        return self.current_state == ConversationState.IDLE

    def is_listening(self) -> bool:
        """Check if in listening state."""
        return self.current_state == ConversationState.LISTENING

    def is_processing(self) -> bool:
        """Check if in processing state."""
        return self.current_state == ConversationState.PROCESSING

    def is_speaking(self) -> bool:
        """Check if in speaking state."""
        return self.current_state == ConversationState.SPEAKING
