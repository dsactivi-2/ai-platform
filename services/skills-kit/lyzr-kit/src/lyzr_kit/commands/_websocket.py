"""WebSocket client for real-time event streaming."""

import asyncio
import contextlib
import json
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

# WebSocket endpoint for metrics/events
WEBSOCKET_BASE_URL = "wss://metrics.studio.lyzr.ai"

# Event types to ignore (noise)
IGNORED_EVENTS = {"keepalive", "ping", "pong"}


@dataclass
class ChatEvent:
    """Represents a single chat activity event."""

    event_type: str
    timestamp: datetime
    function_name: str | None = None
    arguments: dict[str, Any] | None = None
    response: str | None = None
    level: str = "INFO"
    message: str = ""
    data: dict[str, Any] | None = None  # Additional payload data

    def format_display(self) -> str:
        """Format event for terminal display."""
        # Tool events
        if self.event_type == "tool_call_prepare":
            name = self.function_name or "unknown"
            args_preview = self._format_args_preview()
            if args_preview:
                return f"[Tool] {name}({args_preview})"
            return f"[Tool] Calling {name}..."

        if self.event_type == "tool_response":
            name = self.function_name or "unknown"
            resp = self._truncate_response(self.response, 50)
            return f"[Tool] {name} → {resp}"

        # LLM events
        if self.event_type == "llm_response":
            return "[LLM] Generating response..."

        if self.event_type == "thinking":
            return "[LLM] Thinking..."

        # Memory events
        if self.event_type == "context_memory_updated":
            return "[Memory] Context updated"

        if self.event_type == "messages_retrieved":
            count = self._get_message_count()
            return f"[Memory] Retrieved {count} messages"

        if self.event_type == "messages_retrieved_redis":
            return "[Memory] Messages retrieved from cache"

        # Process events
        if self.event_type == "process_start":
            process_name = self.message or "process"
            return f"[Process] {process_name}"

        if self.event_type == "agent_process_start":
            return "[Agent] Processing started"

        if self.event_type == "agent_process_end":
            return "[Agent] Processing complete"

        # Artifact events
        if self.event_type == "artifact_create_success":
            name = self.arguments.get("name", "artifact") if self.arguments else "artifact"
            return f"[Artifact] Created: {name}"

        # Default: show event type and message
        if self.message:
            # Clean up the message - remove redundant info
            msg = self.message
            if len(msg) > 60:
                msg = msg[:57] + "..."
            return f"[{self._format_event_type()}] {msg}"

        return f"[{self._format_event_type()}]"

    def _format_event_type(self) -> str:
        """Format event type for display (convert snake_case to Title Case)."""
        # Map common event types to short labels
        type_map = {
            "agent_process_start": "Agent",
            "agent_process_end": "Agent",
            "process_start": "Process",
            "process_end": "Process",
            "messages_retrieved_redis": "Memory",
            "context_memory_updated": "Memory",
        }
        if self.event_type in type_map:
            return type_map[self.event_type]
        # Default: capitalize first letter
        return self.event_type.replace("_", " ").title()[:15]

    def _format_args_preview(self) -> str:
        """Format arguments preview for tool calls."""
        if not self.arguments:
            return ""
        # Show first few key-value pairs
        preview_items = []
        for key, value in list(self.arguments.items())[:2]:
            if isinstance(value, str) and len(value) > 20:
                value = value[:17] + "..."
            elif isinstance(value, (dict, list)):
                value = "..."
            preview_items.append(f"{key}={value}")
        return ", ".join(preview_items)

    def _get_message_count(self) -> str:
        """Get message count from arguments or data."""
        # Check arguments.data
        if self.arguments and "data" in self.arguments:
            data = self.arguments["data"]
            if isinstance(data, list):
                return str(len(data))
        # Check data field directly
        if self.data and isinstance(self.data, list):
            return str(len(self.data))
        return "?"

    def _truncate_response(self, resp: str | None, max_len: int) -> str:
        """Truncate response for display."""
        if not resp:
            return "(empty)"
        # Clean up JSON responses
        resp = resp.strip()
        is_json = resp.startswith("{") or resp.startswith("[")
        if is_json and len(resp) > max_len:
            # For JSON, just show a preview
            return resp[: max_len - 3] + "..."
        if len(resp) <= max_len:
            return resp
        return resp[: max_len - 3] + "..."


@dataclass
class EventState:
    """Thread-safe state for WebSocket events."""

    events: list[ChatEvent] = field(default_factory=list)
    is_connected: bool = False
    error: str | None = None
    _seen_hashes: set[int] = field(default_factory=set)

    def add_event(self, event: ChatEvent) -> bool:
        """Add event if not a duplicate. Returns True if added."""
        # Create hash for deduplication
        event_hash = hash(
            (event.event_type, event.function_name, event.response, event.timestamp.isoformat())
        )
        if event_hash in self._seen_hashes:
            return False
        self._seen_hashes.add(event_hash)
        self.events.append(event)
        return True

    def clear(self) -> None:
        """Clear all events."""
        self.events.clear()
        self._seen_hashes.clear()
        self.error = None


def parse_event(data: dict[str, Any], debug: bool = False) -> ChatEvent | None:
    """Parse raw WebSocket message into ChatEvent.

    Args:
        data: Raw WebSocket message data
        debug: If True, print raw event data for debugging

    Available fields in WebSocket events:
        - event_type: str - Type of event (e.g., "tool_call_prepare", "tool_response")
        - timestamp: str - ISO format timestamp
        - function_name: str - Name of tool/function being called
        - arguments: dict - Arguments passed to the function
        - response: str|dict - Response from the function/tool
        - level: str - Log level (INFO, ERROR, WARNING, SUCCESS)
        - message: str - Human-readable message
        - data: dict - Additional data payload (varies by event type)
        - session_id: str - Session identifier
        - agent_id: str - Agent identifier
        - user_id: str - User identifier
    """
    if debug:
        import sys

        print(f"[DEBUG WS] {json.dumps(data, indent=2, default=str)}", file=sys.stderr)

    event_type = data.get("event_type", "")

    if event_type in IGNORED_EVENTS:
        return None

    # Parse timestamp
    ts_str = data.get("timestamp")
    if ts_str:
        try:
            timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except ValueError:
            timestamp = datetime.now()
    else:
        timestamp = datetime.now()

    # Extract function name from various locations
    function_name = data.get("function_name")
    if not function_name:
        args = data.get("arguments", {})
        if isinstance(args, dict):
            function_name = args.get("name")

    # Extract response
    response = data.get("response")
    if isinstance(response, dict):
        response = json.dumps(response, ensure_ascii=False)
    elif response is not None:
        response = str(response)

    return ChatEvent(
        event_type=event_type,
        timestamp=timestamp,
        function_name=function_name,
        arguments=data.get("arguments"),
        response=response,
        data=data.get("data"),
        level=data.get("level", "INFO"),
        message=data.get("message", ""),
    )


async def connect_websocket(
    session_id: str,
    api_key: str,
    state: EventState,
    on_event: Callable[[ChatEvent], None] | None = None,
) -> None:
    """Connect to WebSocket and stream events.

    Args:
        session_id: Chat session ID
        api_key: API key for authentication
        state: EventState to update with events
        on_event: Optional callback for each new event
    """
    url = f"{WEBSOCKET_BASE_URL}/ws/{session_id}?x-api-key={api_key}"

    try:
        async with websockets.connect(url, close_timeout=5) as ws:
            state.is_connected = True
            state.error = None

            async for message in ws:
                try:
                    data = json.loads(message)
                    event = parse_event(data)
                    if event and state.add_event(event) and on_event:
                        on_event(event)
                except json.JSONDecodeError:
                    continue

    except ConnectionClosed:
        state.is_connected = False
    except WebSocketException as e:
        state.is_connected = False
        state.error = str(e)
    except Exception as e:
        state.is_connected = False
        state.error = str(e)


class WebSocketClient:
    """Manages WebSocket connection for chat events."""

    def __init__(self, session_id: str, api_key: str):
        self.session_id = session_id
        self.api_key = api_key
        self.state = EventState()
        self._task: asyncio.Task[None] | None = None
        self._on_event: Callable[[ChatEvent], None] | None = None

    def set_event_callback(self, callback: Callable[[ChatEvent], None]) -> None:
        """Set callback to be called for each new event."""
        self._on_event = callback

    async def start(self) -> None:
        """Start WebSocket connection in background."""
        self._task = asyncio.create_task(
            connect_websocket(self.session_id, self.api_key, self.state, self._on_event)
        )

    async def stop(self) -> None:
        """Stop WebSocket connection."""
        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None
        self.state.is_connected = False

    def get_events(self) -> list[ChatEvent]:
        """Get all received events."""
        return self.state.events.copy()

    def clear_events(self) -> None:
        """Clear all events."""
        self.state.clear()

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.state.is_connected

    @property
    def error(self) -> str | None:
        """Get last error message."""
        return self.state.error
