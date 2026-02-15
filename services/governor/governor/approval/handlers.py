"""Approval handlers for different approval mechanisms."""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Coroutine, Dict, Optional

from governor.approval.manager import ApprovalManager, get_default_approval_manager


class ApprovalHandler(ABC):
    """Base class for approval handlers."""

    def __init__(self, manager: Optional[ApprovalManager] = None):
        """
        Initialize approval handler.

        Args:
            manager: ApprovalManager instance (uses default if None)
        """
        self.manager = manager or get_default_approval_manager()

    @abstractmethod
    async def handle_approval_request(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        approvers: list[str],
    ) -> None:
        """
        Handle an approval request.

        This method should present the approval request to users
        and eventually call manager.provide_decision().

        Args:
            execution_id: Execution ID
            function_name: Function name
            inputs: Function inputs
            approvers: List of approvers
        """
        pass


class CLIApprovalHandler(ApprovalHandler):
    """
    CLI-based approval handler.

    Prompts for approval in the terminal (useful for development).
    """

    async def handle_approval_request(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        approvers: list[str],
    ) -> None:
        """Handle approval request via CLI prompt."""
        print("\n" + "=" * 70)
        print("🔔 APPROVAL REQUIRED")
        print("=" * 70)
        print(f"Execution ID: {execution_id}")
        print(f"Function: {function_name}")
        print(f"Approvers: {', '.join(approvers)}")
        print(f"\nInputs:")
        for key, value in inputs.items():
            print(f"  {key}: {value}")
        print("=" * 70)

        # Run in thread pool to avoid blocking event loop
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None,
            lambda: input("\nApprove? (y/n): ").strip().lower(),
        )

        approved = response in ("y", "yes")
        reason = None

        if not approved:
            reason = await loop.run_in_executor(
                None,
                lambda: input("Reason for rejection: ").strip(),
            )

        self.manager.provide_decision(
            execution_id=execution_id,
            approved=approved,
            approver="cli_user",
            reason=reason,
        )


class WebhookApprovalHandler(ApprovalHandler):
    """
    Webhook-based approval handler.

    Stores pending approvals and provides API for external systems
    to submit decisions via webhook.
    """

    def __init__(
        self,
        manager: Optional[ApprovalManager] = None,
        notification_callback: Optional[Callable[[Dict[str, Any]], Coroutine[Any, Any, None]]] = None,
    ):
        """
        Initialize webhook handler.

        Args:
            manager: ApprovalManager instance
            notification_callback: Optional callback to notify external systems
        """
        super().__init__(manager)
        self.notification_callback = notification_callback

    async def handle_approval_request(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        approvers: list[str],
    ) -> None:
        """Handle approval request by notifying external system."""
        # Prepare notification payload
        payload = {
            "execution_id": execution_id,
            "function_name": function_name,
            "inputs": inputs,
            "approvers": approvers,
            "webhook_url": f"/approvals/{execution_id}/decide",  # Placeholder
        }

        # Notify external system if callback provided
        if self.notification_callback:
            try:
                await self.notification_callback(payload)
            except Exception as e:
                print(f"Warning: Failed to send approval notification: {e}")

    def approve(
        self,
        execution_id: str,
        approver: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Approve an execution (called by webhook endpoint).

        Args:
            execution_id: Execution ID
            approver: Approver identifier
            reason: Optional reason

        Returns:
            True if successful, False if no pending approval
        """
        return self.manager.provide_decision(
            execution_id=execution_id,
            approved=True,
            approver=approver,
            reason=reason,
        )

    def reject(
        self,
        execution_id: str,
        approver: str,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Reject an execution (called by webhook endpoint).

        Args:
            execution_id: Execution ID
            approver: Approver identifier
            reason: Optional reason

        Returns:
            True if successful, False if no pending approval
        """
        return self.manager.provide_decision(
            execution_id=execution_id,
            approved=False,
            approver=approver,
            reason=reason,
        )


class CallbackApprovalHandler(ApprovalHandler):
    """
    Custom callback-based approval handler.

    Allows users to provide custom async functions for approval logic
    (e.g., Slack notifications, email, custom UI).
    """

    def __init__(
        self,
        callback: Callable[[str, str, Dict[str, Any], list[str]], Coroutine[Any, Any, tuple[bool, str, Optional[str]]]],
        manager: Optional[ApprovalManager] = None,
    ):
        """
        Initialize callback handler.

        Args:
            callback: Async function that handles approval.
                      Should return (approved, approver, reason)
            manager: ApprovalManager instance
        """
        super().__init__(manager)
        self.callback = callback

    async def handle_approval_request(
        self,
        execution_id: str,
        function_name: str,
        inputs: Dict[str, Any],
        approvers: list[str],
    ) -> None:
        """Handle approval request via custom callback."""
        try:
            approved, approver, reason = await self.callback(
                execution_id, function_name, inputs, approvers
            )

            self.manager.provide_decision(
                execution_id=execution_id,
                approved=approved,
                approver=approver,
                reason=reason,
            )
        except Exception as e:
            # On error, reject the approval
            self.manager.provide_decision(
                execution_id=execution_id,
                approved=False,
                approver="system",
                reason=f"Approval callback error: {e}",
            )
