"""Chat module - UI, streaming, and input handling for agent chat."""

from lyzr_kit.commands._chat.keybindings import create_key_bindings, create_prompt_session
from lyzr_kit.commands._chat.state import StreamState
from lyzr_kit.commands._chat.streaming import (
    STREAM_API_ENDPOINT,
    ChatStreamer,
    decode_sse_data,
    separate_thinking_content,
)
from lyzr_kit.commands._chat.ui import (
    build_agent_box,
    build_session_box,
    build_user_box,
    format_timestamp,
)

__all__ = [
    # State
    "StreamState",
    # UI
    "build_agent_box",
    "build_session_box",
    "build_user_box",
    "format_timestamp",
    # Streaming
    "STREAM_API_ENDPOINT",
    "ChatStreamer",
    "decode_sse_data",
    "separate_thinking_content",
    # Keybindings
    "create_key_bindings",
    "create_prompt_session",
]
