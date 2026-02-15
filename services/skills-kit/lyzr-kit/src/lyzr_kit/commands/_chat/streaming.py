"""SSE streaming and WebSocket integration for chat."""

import asyncio
import json
import re
import threading
import time
from datetime import datetime

import httpx
from rich.live import Live

from lyzr_kit.commands._chat.state import StreamState
from lyzr_kit.commands._chat.ui import build_agent_box, format_timestamp
from lyzr_kit.commands._console import console
from lyzr_kit.commands._websocket import WEBSOCKET_BASE_URL, ChatEvent, parse_event
from lyzr_kit.schemas.agent import Agent
from lyzr_kit.utils.auth import AuthConfig

# Chat API endpoints
STREAM_API_ENDPOINT = "https://agent-prod.studio.lyzr.ai/v3/inference/stream/"


def decode_sse_data(data: str) -> str:
    """Decode escape sequences from SSE data."""
    return (
        data.replace("\\n", "\n")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\&", "&")
        .replace("\\r", "\r")
        .replace("\\\\", "\\")
        .replace("\\t", "\t")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
    )


def separate_thinking_content(content: str) -> tuple[str | None, str]:
    """Extract thinking content from <think> tags."""
    think_match = re.search(r"<think>([\s\S]*?)</think>", content)
    if think_match:
        thinking = think_match.group(1).strip()
        actual_content = re.sub(r"<think>[\s\S]*?</think>", "", content).strip()
        return thinking, actual_content
    return None, content


class ChatStreamer:
    """Handles SSE streaming with WebSocket event integration."""

    def __init__(self, auth: AuthConfig, agent: Agent, session_id: str):
        """Initialize the chat streamer.

        Args:
            auth: Authentication config.
            agent: Agent to chat with.
            session_id: Chat session ID.
        """
        self.auth = auth
        self.agent = agent
        self.session_id = session_id
        self.state = StreamState()

    def stream_message(self, message: str, user_timestamp: str | None = None) -> None:
        """Stream message from inference API with live display and WebSocket events.

        Args:
            message: User message to send.
            user_timestamp: Timestamp when user submitted the message.
        """
        headers = {
            "Content-Type": "application/json",
            "accept": "application/json",
            "x-api-key": self.auth.api_key,
        }

        payload = {
            "agent_id": self.agent.platform_agent_id,
            "session_id": self.session_id,
            "user_id": self.auth.user_id or "default_user",
            "message": message,
        }

        # Clear state for new message
        self.state.clear()
        self.state.is_streaming = True
        self.state.start_time = time.time()

        # Use provided timestamp or generate new one
        timestamp = user_timestamp or format_timestamp()
        buffer = ""

        # WebSocket event handling
        ws_events: list[ChatEvent] = []
        ws_stop_event = threading.Event()

        def receive_ws_events() -> None:
            """Receive events from WebSocket in a daemon thread."""
            try:
                import websockets

                async def _ws_loop() -> None:
                    try:
                        url = f"{WEBSOCKET_BASE_URL}/ws/{self.session_id}?x-api-key={self.auth.api_key}"
                        async with websockets.connect(url, close_timeout=2) as ws:
                            while not ws_stop_event.is_set():
                                try:
                                    msg = await asyncio.wait_for(ws.recv(), timeout=0.5)
                                    data = json.loads(msg)
                                    event = parse_event(data)
                                    if event:
                                        ws_events.append(event)
                                except asyncio.TimeoutError:
                                    continue
                                except Exception:
                                    break
                    except Exception:
                        pass

                asyncio.run(_ws_loop())
            except Exception:
                # WebSocket is optional - continue without it
                pass

        # Start WebSocket in daemon thread
        ws_thread = threading.Thread(target=receive_ws_events, daemon=True)
        ws_thread.start()

        try:
            with httpx.stream(
                "POST",
                STREAM_API_ENDPOINT,
                json=payload,
                headers=headers,
                timeout=120.0,
            ) as response:
                if response.status_code != 200:
                    self.state.error = f"API returned status {response.status_code}"
                    self.state.is_streaming = False
                    self.state.end_time = time.time()
                    console.print(build_agent_box(self.state, timestamp))
                    return

                with Live(
                    build_agent_box(self.state, timestamp), console=console, refresh_per_second=10
                ) as live:
                    for line in response.iter_lines():
                        # Merge WebSocket events
                        while ws_events:
                            event = ws_events.pop(0)
                            self.state.add_event(event)
                            live.update(build_agent_box(self.state, timestamp))

                        if not line:
                            continue

                        if line.startswith("data: "):
                            data = line[6:]

                            if data == "[DONE]":
                                break

                            if data.startswith("[ERROR]"):
                                self.state.error = data[7:].strip()
                                break

                            decoded_data = decode_sse_data(data)
                            if not decoded_data:
                                continue

                            # Mark first chunk time
                            if self.state.first_chunk_time == 0:
                                self.state.first_chunk_time = time.time()

                            buffer += decoded_data
                            thinking, content = separate_thinking_content(buffer)

                            # If we have thinking content, add it as an event
                            if thinking and not any(
                                e.event_type == "thinking" for e in self.state.events
                            ):
                                self.state.add_event(
                                    ChatEvent(
                                        event_type="thinking",
                                        timestamp=datetime.now(),
                                        message=thinking[:100] + "..."
                                        if len(thinking) > 100
                                        else thinking,
                                    )
                                )

                            self.state.content = content
                            live.update(build_agent_box(self.state, timestamp))

                    # Drain remaining WebSocket events
                    while ws_events:
                        event = ws_events.pop(0)
                        self.state.add_event(event)

                    self.state.is_streaming = False
                    self.state.end_time = time.time()
                    live.update(build_agent_box(self.state, timestamp))

        except httpx.TimeoutException:
            self.state.error = "Request timed out. The agent may be processing a complex query."
            self.state.is_streaming = False
            self.state.end_time = time.time()
        except Exception as e:
            self.state.error = str(e)
            self.state.is_streaming = False
            self.state.end_time = time.time()
        finally:
            # Signal WebSocket thread to stop
            ws_stop_event.set()
            # Give the thread a moment to clean up
            ws_thread.join(timeout=0.5)

        console.print()
