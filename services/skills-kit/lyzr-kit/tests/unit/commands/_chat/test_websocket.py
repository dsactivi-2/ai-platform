"""Tests for WebSocket event handling."""

from datetime import datetime

from lyzr_kit.commands._websocket import ChatEvent, EventState, parse_event


class TestChatEventFormatting:
    """Tests for ChatEvent format_display method."""

    def test_format_tool_call(self):
        """ChatEvent should format tool call events."""
        event = ChatEvent(
            event_type="tool_call_prepare",
            timestamp=datetime.now(),
            function_name="search_web",
        )
        assert event.format_display() == "[Tool] Calling search_web..."

    def test_format_tool_response(self):
        """ChatEvent should format tool response events."""
        event = ChatEvent(
            event_type="tool_response",
            timestamp=datetime.now(),
            function_name="search_web",
            response='{"results": [1, 2, 3]}',
        )
        display = event.format_display()
        assert "[Tool] search_web →" in display

    def test_format_llm_response(self):
        """ChatEvent should format LLM response events."""
        event = ChatEvent(
            event_type="llm_response",
            timestamp=datetime.now(),
        )
        assert event.format_display() == "[LLM] Generating response..."

    def test_format_memory(self):
        """ChatEvent should format memory events."""
        event = ChatEvent(
            event_type="context_memory_updated",
            timestamp=datetime.now(),
        )
        assert event.format_display() == "[Memory] Context updated"

    def test_format_artifact(self):
        """ChatEvent should format artifact events."""
        event = ChatEvent(
            event_type="artifact_create_success",
            timestamp=datetime.now(),
            arguments={"name": "chart.png"},
        )
        assert event.format_display() == "[Artifact] Created: chart.png"


class TestParseEvent:
    """Tests for parse_event function."""

    def test_parse_basic(self):
        """parse_event should parse basic event data."""
        data = {
            "event_type": "tool_call_prepare",
            "function_name": "test_func",
            "timestamp": "2024-01-01T12:00:00Z",
        }
        event = parse_event(data)
        assert event is not None
        assert event.event_type == "tool_call_prepare"
        assert event.function_name == "test_func"

    def test_ignores_keepalive(self):
        """parse_event should ignore keepalive events."""
        data = {"event_type": "keepalive"}
        event = parse_event(data)
        assert event is None


class TestEventState:
    """Tests for EventState class."""

    def test_deduplication(self):
        """EventState should deduplicate events."""
        state = EventState()
        event = ChatEvent(
            event_type="test",
            timestamp=datetime(2024, 1, 1, 12, 0, 0),
            function_name="func1",
        )

        # First add should succeed
        assert state.add_event(event) is True
        assert len(state.events) == 1

        # Duplicate should be rejected
        assert state.add_event(event) is False
        assert len(state.events) == 1

    def test_clear(self):
        """EventState clear should reset all state."""
        state = EventState()
        state.add_event(ChatEvent(event_type="test", timestamp=datetime.now()))
        state.error = "test error"

        state.clear()

        assert len(state.events) == 0
        assert state.error is None
