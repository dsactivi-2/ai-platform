"""Tests for chat UI component builders."""

from datetime import datetime
from unittest.mock import MagicMock

from rich.panel import Panel

from lyzr_kit.commands._chat import StreamState, build_agent_box, build_session_box, build_user_box
from lyzr_kit.commands._websocket import ChatEvent


class TestBuildSessionBox:
    """Tests for _build_session_box function."""

    def test_returns_panel(self):
        """_build_session_box should return a Panel with session info."""
        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = "gpt-4o"

        panel = build_session_box(mock_agent, "abc12345-def6-7890", "14:32:15")

        assert isinstance(panel, Panel)
        assert panel.title is not None
        assert "Session" in str(panel.title)
        assert panel.border_style == "blue"

    def test_with_default_model(self):
        """_build_session_box should handle None model."""
        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = None

        # Should not raise
        panel = build_session_box(mock_agent, "session-id", "12:00:00")
        assert panel is not None

    def test_with_model_config(self):
        """_build_session_box should extract model name from ModelConfig."""
        mock_model = MagicMock()
        mock_model.name = "gpt-4o-mini"

        mock_agent = MagicMock()
        mock_agent.name = "Test Agent"
        mock_agent.model = mock_model

        # Should not raise and should use model.name
        panel = build_session_box(mock_agent, "session-id", "12:00:00")
        assert panel is not None


class TestBuildUserBox:
    """Tests for _build_user_box function."""

    def test_returns_panel(self):
        """_build_user_box should return a Panel with user message."""
        panel = build_user_box("Hello, world!", "14:32:20")

        assert isinstance(panel, Panel)
        assert panel.border_style == "cyan"
        assert "You" in str(panel.title)


class TestBuildAgentBox:
    """Tests for _build_agent_box function."""

    def test_returns_panel(self):
        """_build_agent_box should return a Panel."""
        state = StreamState()
        state.content = "This is the response"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.5

        panel = build_agent_box(state, "14:32:21")

        assert isinstance(panel, Panel)
        assert panel.border_style == "green"
        assert "Agent" in str(panel.title)

    def test_error_style(self):
        """_build_agent_box should use red style for error-only state."""
        state = StreamState()
        state.error = "API error occurred"
        state.content = ""  # No content, error only
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.0

        panel = build_agent_box(state, "14:32:21")

        assert panel.border_style == "red"
        assert "Error" in str(panel.title)

    def test_streaming_state(self):
        """_build_agent_box should show waiting message when streaming with no content."""
        state = StreamState()
        state.is_streaming = True
        state.content = ""

        panel = build_agent_box(state, "14:32:21")

        assert panel.border_style == "green"
        # Subtitle should be None during streaming (no metrics yet)

    def test_with_events(self):
        """_build_agent_box should include events in content."""
        state = StreamState()
        state.content = "Response text"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.0
        state.add_event(
            ChatEvent(
                event_type="tool_call_prepare",
                timestamp=datetime.now(),
                function_name="search_web",
            )
        )

        panel = build_agent_box(state, "14:32:21")

        assert panel is not None
        assert len(state.events) == 1

    def test_shows_latency(self):
        """_build_agent_box should show latency in subtitle after streaming."""
        state = StreamState()
        state.content = "Response"
        state.is_streaming = False
        state.start_time = 1000.0
        state.end_time = 1001.5  # 1.5 seconds

        panel = build_agent_box(state, "14:32:21")

        # Subtitle should contain latency
        assert panel.subtitle is not None
        assert "1.50s" in str(panel.subtitle)
