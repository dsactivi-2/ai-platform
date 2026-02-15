"""Keyboard bindings for chat prompt using prompt_toolkit."""

from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.keys import Keys
from prompt_toolkit.styles import Style


def create_key_bindings() -> KeyBindings:
    """Create custom key bindings for chat prompt.

    Supports:
    - Ctrl+Left / Option+Left: Move word backward
    - Ctrl+Right / Option+Right: Move word forward
    - Option+Backspace: Delete word backward
    - Option+D / Alt+D: Delete word forward
    """
    bindings = KeyBindings()

    @bindings.add(Keys.ControlLeft)  # Ctrl+Left - move word backward
    @bindings.add("escape", "b")  # Option+Left on macOS (sends Escape+b)
    def _move_word_backward(event: Any) -> None:
        """Move cursor to the beginning of the previous word."""
        buff = event.current_buffer
        buff.cursor_position += buff.document.find_previous_word_beginning() or 0

    @bindings.add(Keys.ControlRight)  # Ctrl+Right - move word forward
    @bindings.add("escape", "f")  # Option+Right on macOS (sends Escape+f)
    def _move_word_forward(event: Any) -> None:
        """Move cursor to the end of the next word."""
        buff = event.current_buffer
        buff.cursor_position += buff.document.find_next_word_ending() or 0

    @bindings.add("escape", Keys.Backspace)  # Option+Backspace - delete word backward
    def _delete_word_backward(event: Any) -> None:
        """Delete the word before the cursor."""
        buff = event.current_buffer
        pos = buff.document.find_previous_word_beginning() or 0
        if pos:
            buff.delete_before_cursor(count=-pos)

    @bindings.add("escape", "d")  # Option+Delete / Alt+D - delete word forward
    def _delete_word_forward(event: Any) -> None:
        """Delete the word after the cursor."""
        buff = event.current_buffer
        pos = buff.document.find_next_word_ending() or 0
        if pos:
            buff.delete(count=pos)

    return bindings


def create_prompt_session() -> PromptSession[str]:
    """Create a configured prompt session for chat input.

    Returns:
        PromptSession with history, styling, and custom key bindings.
    """
    prompt_style = Style.from_dict(
        {
            "prompt": "cyan",
        }
    )
    history = InMemoryHistory()
    bindings = create_key_bindings()

    return PromptSession(
        history=history,
        style=prompt_style,
        key_bindings=bindings,
        enable_system_prompt=False,
        enable_open_in_editor=False,
    )
