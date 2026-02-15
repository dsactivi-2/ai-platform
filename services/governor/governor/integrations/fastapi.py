"""FastAPI integration for governor."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from fastapi import APIRouter, HTTPException, Request, Response
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
except ImportError:
    raise ImportError(
        "FastAPI integration requires 'fastapi' package. "
        "Install with: pip install governor[fastapi]"
    )

from pydantic import BaseModel

from governor.approval.handlers import WebhookApprovalHandler
from governor.approval.manager import ApprovalManager, get_default_approval_manager
from governor.core.context import ExecutionContext
from governor.replay.engine import ReplayEngine
from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage


class ApprovalRequest(BaseModel):
    """Model for approval decision request."""

    approver: str
    approved: bool
    reason: Optional[str] = None


class ApprovalResponse(BaseModel):
    """Model for approval response."""

    success: bool
    message: str
    execution_id: str


def create_approval_router(
    approval_handler: Optional[WebhookApprovalHandler] = None,
    approval_manager: Optional[ApprovalManager] = None,
    storage: Optional[StorageBackend] = None,
    prefix: str = "/govern",
) -> APIRouter:
    """
    Create FastAPI router for approval endpoints.

    Provides REST API for:
    - Listing pending approvals
    - Approving/rejecting executions
    - Viewing execution details

    Args:
        approval_handler: WebhookApprovalHandler instance
        approval_manager: ApprovalManager instance
        storage: Storage backend
        prefix: URL prefix for routes

    Returns:
        Configured APIRouter

    Example:
        ```python
        from fastapi import FastAPI
        from governor.integrations.fastapi import create_approval_router

        app = FastAPI()
        app.include_router(create_approval_router())
        ```
    """
    router = APIRouter(prefix=prefix, tags=["governance"])

    # Use defaults if not provided
    manager = approval_manager or get_default_approval_manager()
    store = storage or InMemoryStorage()
    handler = approval_handler or WebhookApprovalHandler(manager=manager)

    @router.get("/approvals/pending")
    async def list_pending_approvals() -> Dict[str, Any]:
        """List all pending approval requests."""
        pending = manager.get_pending_approvals()
        return {
            "count": len(pending),
            "approvals": [
                {
                    "execution_id": p.execution_id,
                    "function_name": p.function_name,
                    "approvers": p.approvers,
                    "created_at": p.created_at.isoformat(),
                    "timeout_seconds": p.timeout_seconds,
                }
                for p in pending
            ],
        }

    @router.get("/approvals/{execution_id}")
    async def get_approval_details(execution_id: str) -> Dict[str, Any]:
        """Get details for a specific approval request."""
        # Check if pending
        pending = [p for p in manager.get_pending_approvals() if p.execution_id == execution_id]

        if not pending:
            # Check if already decided
            decision = manager.get_decision(execution_id)
            if decision:
                return {
                    "execution_id": execution_id,
                    "status": "decided",
                    "approved": decision.approved,
                    "approver": decision.approver,
                    "reason": decision.reason,
                    "decided_at": decision.decided_at.isoformat(),
                }

            raise HTTPException(status_code=404, detail="Approval request not found")

        p = pending[0]
        context = await store.get_execution(execution_id)

        return {
            "execution_id": execution_id,
            "status": "pending",
            "function_name": p.function_name,
            "inputs": p.inputs,
            "approvers": p.approvers,
            "created_at": p.created_at.isoformat(),
            "timeout_seconds": p.timeout_seconds,
            "context": context.to_dict() if context else None,
        }

    @router.post("/approvals/{execution_id}/approve")
    async def approve_execution(
        execution_id: str, request: ApprovalRequest
    ) -> ApprovalResponse:
        """Approve an execution."""
        success = handler.approve(
            execution_id=execution_id,
            approver=request.approver,
            reason=request.reason,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="No pending approval found for this execution"
            )

        return ApprovalResponse(
            success=True,
            message="Execution approved",
            execution_id=execution_id,
        )

    @router.post("/approvals/{execution_id}/reject")
    async def reject_execution(
        execution_id: str, request: ApprovalRequest
    ) -> ApprovalResponse:
        """Reject an execution."""
        success = handler.reject(
            execution_id=execution_id,
            approver=request.approver,
            reason=request.reason,
        )

        if not success:
            raise HTTPException(
                status_code=404, detail="No pending approval found for this execution"
            )

        return ApprovalResponse(
            success=True,
            message="Execution rejected",
            execution_id=execution_id,
        )

    @router.get("/executions")
    async def list_executions(
        function_name: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List executions with optional filtering."""
        executions = await store.list_executions(
            function_name=function_name, status=status, limit=limit
        )

        return {
            "count": len(executions),
            "executions": [e.to_dict() for e in executions],
        }

    @router.get("/executions/{execution_id}")
    async def get_execution(execution_id: str) -> Dict[str, Any]:
        """Get details for a specific execution."""
        context = await store.get_execution(execution_id)
        if not context:
            raise HTTPException(status_code=404, detail="Execution not found")

        # Get snapshots
        replay = ReplayEngine(storage=store)
        snapshots = await replay.get_snapshots(execution_id)

        return {
            "execution": context.to_dict(),
            "snapshots": [
                {
                    "checkpoint": s.checkpoint,
                    "captured_at": s.captured_at.isoformat(),
                }
                for s in snapshots
            ],
        }

    return router


class GovernMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for governance.

    Automatically adds governance context (user, request info)
    to governed endpoints.
    """

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Process request and add governance context."""
        # Extract user info from request (customize based on your auth)
        # This is a simple example - adapt to your authentication system
        user_context = {
            "id": request.headers.get("X-User-ID"),
            "email": request.headers.get("X-User-Email"),
            "roles": request.headers.get("X-User-Roles", "").split(","),
        }

        # Add to request state
        request.state.govern_context = {
            "user": user_context,
            "request_id": request.headers.get("X-Request-ID"),
            "ip_address": request.client.host if request.client else None,
        }

        response = await call_next(request)
        return response
