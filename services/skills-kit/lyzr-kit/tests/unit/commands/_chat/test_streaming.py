"""Tests for chat streaming helpers."""

from lyzr_kit.commands._chat import (
    StreamState,
    decode_sse_data,
    separate_thinking_content,
)


class TestSeparateThinkingContent:
    """Tests for thinking content extraction."""

    def test_with_think_tags(self):
        """Should extract thinking content from <think> tags."""
        content = "<think>I am analyzing the question</think>Here is my response"
        thinking, actual = separate_thinking_content(content)
        assert thinking == "I am analyzing the question"
        assert actual == "Here is my response"

    def test_without_think_tags(self):
        """Should return None for thinking when no <think> tags."""
        content = "Just a regular response"
        thinking, actual = separate_thinking_content(content)
        assert thinking is None
        assert actual == "Just a regular response"

    def test_multiline(self):
        """Should handle multiline thinking content."""
        content = "<think>Step 1: Analyze\nStep 2: Process</think>The answer is 42"
        thinking, actual = separate_thinking_content(content)
        assert thinking == "Step 1: Analyze\nStep 2: Process"
        assert actual == "The answer is 42"


class TestDecodeSSEData:
    """Tests for SSE data decoding."""

    def test_escapes(self):
        """Should decode common escape sequences."""
        data = 'Hello\\nWorld\\t"quoted"'
        decoded = decode_sse_data(data)
        assert decoded == 'Hello\nWorld\t"quoted"'

    def test_html_entities(self):
        """Should decode HTML entities."""
        data = "&lt;tag&gt; &amp; &quot;text&quot;"
        decoded = decode_sse_data(data)
        assert decoded == '<tag> & "text"'


class TestStreamState:
    """Tests for StreamState dataclass."""

    def test_initial_values(self):
        """StreamState should have correct initial values."""
        state = StreamState()
        assert state.content == ""
        assert state.events == []
        assert state.is_streaming is False
        assert state.start_time == 0.0
        assert state.first_chunk_time == 0.0
        assert state.end_time == 0.0
        assert state.tokens_in == 0
        assert state.tokens_out == 0
        assert state.error is None

    def test_latency_calculation(self):
        """StreamState should calculate latency correctly."""
        state = StreamState()
        state.start_time = 1000.0
        state.first_chunk_time = 1000.5
        state.end_time = 1002.0

        assert state.latency_ms == 500.0  # 0.5 seconds = 500ms
        assert state.total_time_ms == 2000.0  # 2 seconds = 2000ms

    def test_clear(self):
        """StreamState clear should reset all values."""
        state = StreamState()
        state.content = "test"
        state.is_streaming = True
        state.start_time = 100.0
        state.error = "some error"

        state.clear()

        assert state.content == ""
        assert state.is_streaming is False
        assert state.start_time == 0.0
        assert state.error is None
