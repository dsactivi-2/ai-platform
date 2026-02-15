"""Main @govern decorator for governance."""

from __future__ import annotations

import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union, cast

from governor.approval.handlers import ApprovalHandler
from governor.approval.manager import ApprovalManager
from governor.core.executor import Action, Executor
from governor.events.emitter import EventEmitter
from governor.policies.base import Policy
from governor.storage.base import StorageBackend


F = TypeVar("F", bound=Callable[..., Any])


def govern(
    pre: Optional[Union[Action, List[Action]]] = None,
    post: Optional[Union[Action, List[Action]]] = None,
    policies: Optional[Union[Policy, List[Policy]]] = None,
    capture_state: bool = True,
    storage: Optional[StorageBackend] = None,
    emitter: Optional[EventEmitter] = None,
    approval_manager: Optional[ApprovalManager] = None,
    approval_handler: Optional[ApprovalHandler] = None,
    context: Optional[Dict[str, Any]] = None,
    on_state_saved: Optional[Callable[[str, Dict[str, Any]], None]] = None,
) -> Callable[[F], F]:
    """
    Decorator for governance of functions, classes, and FastAPI endpoints.

    Provides comprehensive governance including:
    - Pre/post actions
    - Policy enforcement (validation, authorization, rate limiting, audit)
    - Human-in-the-loop approval
    - State capture and replay
    - Event emission

    Args:
        pre: Pre-action(s) to run before execution
        post: Post-action(s) to run after execution
        policies: Policy or list of policies to enforce
        capture_state: Whether to capture state snapshots
        storage: Storage backend (defaults to InMemoryStorage)
        emitter: Event emitter (defaults to global emitter)
        approval_manager: Approval manager (defaults to global manager)
        approval_handler: Handler for approval requests
        context: Additional context data to include
        on_state_saved: Callback function called when state is saved to database.
                       Receives (execution_id: str, state: Dict[str, Any])

    Returns:
        Decorated function with governance applied

    Example:
        ```python
        from governor import govern, ValidationPolicy, ApprovalPolicy

        # Callback to get execution_id when state is saved
        def handle_state_saved(execution_id: str, state: dict):
            print(f"State saved! Execution ID: {execution_id}")
            print(f"State snapshot: {state}")
            # Return execution_id to client for tracking
            # Or store in your own database
            # Or send to external system

        @govern(
            pre=[log_input],
            post=[log_output],
            policies=[
                ValidationPolicy(input_schema=MySchema),
                ApprovalPolicy(approvers=["admin@company.com"])
            ],
            capture_state=True,
            on_state_saved=handle_state_saved  # Get callback with execution_id
        )
        async def critical_operation(data: dict) -> dict:
            # Your function logic here
            return {"result": "success"}
        ```
    """

    # Normalize inputs to lists
    pre_actions: List[Action] = []
    if pre:
        pre_actions = pre if isinstance(pre, list) else [pre]

    post_actions: List[Action] = []
    if post:
        post_actions = post if isinstance(post, list) else [post]

    policy_list: List[Policy] = []
    if policies:
        policy_list = policies if isinstance(policies, list) else [policies]

    # Create executor
    executor = Executor(
        storage=storage,
        emitter=emitter,
        approval_manager=approval_manager,
        approval_handler=approval_handler,
        on_state_saved=on_state_saved,
    )

    def decorator(func: F) -> F:
        """Apply governance to a function."""

        # Check if function is async
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                f"@govern can only be applied to async functions. "
                f"'{func.__name__}' is not async. Use 'async def {func.__name__}(...)'"
            )

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Governed function wrapper."""
            return await executor.execute(
                func=func,
                args=args,
                kwargs=kwargs,
                pre_actions=pre_actions if pre_actions else None,
                post_actions=post_actions if post_actions else None,
                policies=policy_list if policy_list else None,
                capture_state=capture_state,
                context_data=context,
            )

        # Preserve function metadata
        wrapper.__governed__ = True  # type: ignore
        wrapper.__original__ = func  # type: ignore

        return cast(F, wrapper)

    return decorator


def govern_class(
    pre: Optional[Union[Action, List[Action]]] = None,
    post: Optional[Union[Action, List[Action]]] = None,
    policies: Optional[Union[Policy, List[Policy]]] = None,
    capture_state: bool = True,
    methods: Optional[List[str]] = None,
    **kwargs: Any,
) -> Callable[[type], type]:
    """
    Decorator for governing all methods of a class.

    Args:
        pre: Pre-action(s) to run before execution
        post: Post-action(s) to run after execution
        policies: Policy or list of policies to enforce
        capture_state: Whether to capture state snapshots
        methods: List of method names to govern (None = all public methods)
        **kwargs: Additional arguments passed to @govern

    Returns:
        Decorated class with governance applied to methods

    Example:
        ```python
        @govern_class(
            policies=[AuditPolicy()],
            methods=["process", "execute"]
        )
        class MyAgent:
            async def process(self, data):
                return data

            async def execute(self, cmd):
                return cmd
        ```
    """

    def decorator(cls: type) -> type:
        """Apply governance to class methods."""
        for name, method in inspect.getmembers(cls, predicate=inspect.isfunction):
            # Skip private methods unless explicitly included
            if methods is None:
                if name.startswith("_"):
                    continue
            else:
                if name not in methods:
                    continue

            # Only govern async methods
            if inspect.iscoroutinefunction(method):
                governed_method = govern(
                    pre=pre,
                    post=post,
                    policies=policies,
                    capture_state=capture_state,
                    **kwargs,
                )(method)
                setattr(cls, name, governed_method)

        return cls

    return decorator


# Alias for backward compatibility and clarity
govern_all = govern_class
