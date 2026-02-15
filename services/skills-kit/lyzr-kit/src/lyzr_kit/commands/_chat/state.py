"""State management for chat streaming sessions."""

from dataclasses import dataclass, field

from lyzr_kit.commands._websocket import ChatEvent


@dataclass
class StreamState:
    """State for streaming chat session."""

    content: str = ""
    events: list[ChatEvent] = field(default_factory=list)
    is_streaming: bool = False
    start_time: float = 0.0
    first_chunk_time: float = 0.0
    end_time: float = 0.0
    tokens_in: int = 0
    tokens_out: int = 0
    error: str | None = None

    @property
    def latency_ms(self) -> float:
        """Calculate latency to first chunk in milliseconds."""
        if self.first_chunk_time > 0 and self.start_time > 0:
            return (self.first_chunk_time - self.start_time) * 1000
        return 0.0

    @property
    def total_time_ms(self) -> float:
        """Calculate total response time in milliseconds."""
        if self.end_time > 0 and self.start_time > 0:
            return (self.end_time - self.start_time) * 1000
        return 0.0

    def add_event(self, event: ChatEvent) -> None:
        """Add an event to the list."""
        self.events.append(event)

    def clear(self) -> None:
        """Clear state for next message."""
        self.content = ""
        self.events.clear()
        self.is_streaming = False
        self.start_time = 0.0
        self.first_chunk_time = 0.0
        self.end_time = 0.0
        self.tokens_in = 0
        self.tokens_out = 0
        self.error = None
