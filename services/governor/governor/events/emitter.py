"""Event emitter for async event handling."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Coroutine, Dict, List, Optional

from governor.events.base import Event, EventType


EventHandler = Callable[[Event], Coroutine[Any, Any, None]]


class EventEmitter:
    """
    Async event emitter for governance events.

    Supports multiple handlers per event type and async emission
    to storage backends, notification services, etc.
    """

    def __init__(self) -> None:
        """Initialize the event emitter."""
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._global_handlers: List[EventHandler] = []

    def on(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Register an event handler for a specific event type.

        Args:
            event_type: The event type to listen for
            handler: Async function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def on_any(self, handler: EventHandler) -> None:
        """
        Register a global event handler for all event types.

        Args:
            handler: Async function to handle any event
        """
        self._global_handlers.append(handler)

    def off(self, event_type: EventType, handler: EventHandler) -> None:
        """
        Unregister an event handler.

        Args:
            event_type: The event type
            handler: The handler to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
            except ValueError:
                pass

    def off_any(self, handler: EventHandler) -> None:
        """
        Unregister a global event handler.

        Args:
            handler: The handler to remove
        """
        try:
            self._global_handlers.remove(handler)
        except ValueError:
            pass

    async def emit(self, event: Event) -> None:
        """
        Emit an event to all registered handlers.

        Args:
            event: The event to emit
        """
        # Get handlers for this specific event type
        handlers = self._handlers.get(event.event_type, [])

        # Combine with global handlers
        all_handlers = handlers + self._global_handlers

        if not all_handlers:
            return

        # Execute all handlers concurrently
        await asyncio.gather(*[handler(event) for handler in all_handlers], return_exceptions=True)

    async def emit_and_wait(self, event: Event) -> List[Any]:
        """
        Emit an event and wait for all handlers to complete.

        Args:
            event: The event to emit

        Returns:
            List of results from handlers (including exceptions)
        """
        handlers = self._handlers.get(event.event_type, [])
        all_handlers = handlers + self._global_handlers

        if not all_handlers:
            return []

        results = await asyncio.gather(*[handler(event) for handler in all_handlers], return_exceptions=True)
        return list(results)

    def clear(self) -> None:
        """Clear all event handlers."""
        self._handlers.clear()
        self._global_handlers.clear()


# Global event emitter instance
_default_emitter: Optional[EventEmitter] = None


def get_default_emitter() -> EventEmitter:
    """Get or create the default global event emitter."""
    global _default_emitter
    if _default_emitter is None:
        _default_emitter = EventEmitter()
    return _default_emitter


def set_default_emitter(emitter: EventEmitter) -> None:
    """Set the default global event emitter."""
    global _default_emitter
    _default_emitter = emitter
