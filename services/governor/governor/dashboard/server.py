"""
FastAPI-based dashboard server for visualizing approval flows.

Provides a web UI to view:
- Registered approval flows
- Running approvals with stage visualization
- Approval history
- Interactive approve/reject buttons
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware
except ImportError:
    raise ImportError(
        "Dashboard requires FastAPI. Install with: pip install governor[fastapi]"
    )

from governor.storage.base import StorageBackend
from governor.storage.memory import InMemoryStorage
from governor.approval.manager import ApprovalManager, get_default_approval_manager


class DashboardServer:
    """
    Web dashboard for visualizing and managing approval flows.

    Features:
    - Visualize approval pipeline stages with React Flow
    - View pending approvals
    - Approve/reject from UI
    - Real-time updates via WebSocket
    - Approval history and audit trail
    """

    def __init__(
        self,
        storage: Optional[StorageBackend] = None,
        approval_manager: Optional[ApprovalManager] = None,
        host: str = "0.0.0.0",
        port: int = 8765,
    ):
        """
        Initialize dashboard server.

        Args:
            storage: Storage backend for executions
            approval_manager: Approval manager instance
            host: Host to bind to
            port: Port to bind to
        """
        self.storage = storage or InMemoryStorage()
        self.approval_manager = approval_manager or get_default_approval_manager()
        self.host = host
        self.port = port

        # Track registered flows
        self.registered_flows: Dict[str, Dict[str, Any]] = {}

        # WebSocket connections for real-time updates
        self.websocket_connections: List[WebSocket] = []

        # Create FastAPI app
        self.app = self._create_app()

    def _create_app(self) -> FastAPI:
        """Create and configure FastAPI application."""
        app = FastAPI(
            title="Governor Dashboard",
            description="Approval flow visualization and management",
            version="0.1.1",
        )

        # CORS middleware for React frontend
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # API Routes
        @app.get("/")
        async def root():
            """Serve React dashboard."""
            dashboard_path = Path(__file__).parent / "frontend" / "dist" / "index.html"
            if dashboard_path.exists():
                return FileResponse(dashboard_path)
            return HTMLResponse(self._get_dev_html())

        @app.get("/api/health")
        async def health():
            """Health check endpoint."""
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}

        @app.get("/api/flows")
        async def list_flows():
            """List all registered approval flows."""
            return {
                "flows": list(self.registered_flows.values()),
                "count": len(self.registered_flows),
            }

        @app.get("/api/flows/{flow_name}")
        async def get_flow(flow_name: str):
            """Get details of a specific flow."""
            if flow_name not in self.registered_flows:
                raise HTTPException(status_code=404, detail="Flow not found")
            return self.registered_flows[flow_name]

        @app.get("/api/approvals/pending")
        async def list_pending_approvals():
            """List all pending approvals."""
            # Get all pending approvals from storage
            executions = await self.storage.list_executions()

            pending = []
            for exec_ctx in executions:
                if exec_ctx.status == "awaiting_approval":
                    # Get flow definition if available
                    flow_def = self.registered_flows.get(exec_ctx.function_name, {})

                    pending.append({
                        "execution_id": exec_ctx.execution_id,
                        "function_name": exec_ctx.function_name,
                        "started_at": exec_ctx.started_at.isoformat(),
                        "inputs": exec_ctx.inputs,
                        "current_stage": exec_ctx.current_checkpoint,
                        "flow_definition": flow_def,
                        "approval_metadata": exec_ctx.metadata.get("approval_metadata", {}),
                    })

            return {
                "pending_approvals": pending,
                "count": len(pending),
            }

        @app.get("/api/approvals/history")
        async def approval_history(limit: int = 50):
            """Get approval history."""
            executions = await self.storage.list_executions()

            history = []
            for exec_ctx in executions[:limit]:
                if exec_ctx.status in ["completed", "rejected", "approved"]:
                    history.append({
                        "execution_id": exec_ctx.execution_id,
                        "function_name": exec_ctx.function_name,
                        "status": exec_ctx.status,
                        "started_at": exec_ctx.started_at.isoformat(),
                        "completed_at": exec_ctx.completed_at.isoformat() if exec_ctx.completed_at else None,
                        "duration_ms": exec_ctx.duration_ms,
                    })

            return {
                "history": history,
                "count": len(history),
            }

        @app.post("/api/approvals/{execution_id}/approve")
        async def approve_execution(
            execution_id: str,
            approver: str,
            reason: Optional[str] = None
        ):
            """Approve a pending execution."""
            # Provide approval decision
            self.approval_manager.provide_decision(
                execution_id=execution_id,
                approved=True,
                approver=approver,
                reason=reason or "Approved via dashboard"
            )

            # Broadcast to WebSocket clients
            await self._broadcast({
                "type": "approval_granted",
                "execution_id": execution_id,
                "approver": approver,
                "timestamp": datetime.now().isoformat(),
            })

            return {
                "status": "approved",
                "execution_id": execution_id,
                "approver": approver,
            }

        @app.post("/api/approvals/{execution_id}/reject")
        async def reject_execution(
            execution_id: str,
            approver: str,
            reason: Optional[str] = None
        ):
            """Reject a pending execution."""
            # Provide rejection decision
            self.approval_manager.provide_decision(
                execution_id=execution_id,
                approved=False,
                approver=approver,
                reason=reason or "Rejected via dashboard"
            )

            # Broadcast to WebSocket clients
            await self._broadcast({
                "type": "approval_rejected",
                "execution_id": execution_id,
                "approver": approver,
                "timestamp": datetime.now().isoformat(),
            })

            return {
                "status": "rejected",
                "execution_id": execution_id,
                "approver": approver,
            }

        @app.get("/api/executions/{execution_id}")
        async def get_execution(execution_id: str):
            """Get execution details."""
            exec_ctx = await self.storage.get_execution(execution_id)
            if not exec_ctx:
                raise HTTPException(status_code=404, detail="Execution not found")

            return {
                "execution_id": exec_ctx.execution_id,
                "function_name": exec_ctx.function_name,
                "status": exec_ctx.status,
                "started_at": exec_ctx.started_at.isoformat(),
                "completed_at": exec_ctx.completed_at.isoformat() if exec_ctx.completed_at else None,
                "inputs": exec_ctx.inputs,
                "outputs": exec_ctx.outputs,
                "checkpoints": exec_ctx.checkpoints,
                "duration_ms": exec_ctx.duration_ms,
            }

        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            await websocket.accept()
            self.websocket_connections.append(websocket)

            try:
                # Send initial state
                await websocket.send_json({
                    "type": "connected",
                    "timestamp": datetime.now().isoformat(),
                })

                # Keep connection alive
                while True:
                    data = await websocket.receive_text()
                    # Echo back for heartbeat
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat(),
                    })
            except WebSocketDisconnect:
                self.websocket_connections.remove(websocket)

        return app

    def register_flow(
        self,
        function_name: str,
        stages: List[Dict[str, Any]],
        description: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Register an approval flow for visualization.

        Args:
            function_name: Name of the governed function
            stages: List of stage definitions (name, approvers, etc.)
            description: Flow description
            metadata: Additional metadata
        """
        self.registered_flows[function_name] = {
            "function_name": function_name,
            "description": description or f"{function_name} approval flow",
            "stages": stages,
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
        }

    async def _broadcast(self, message: Dict[str, Any]):
        """Broadcast message to all WebSocket connections."""
        disconnected = []
        for ws in self.websocket_connections:
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(ws)

        # Remove disconnected clients
        for ws in disconnected:
            self.websocket_connections.remove(ws)

    def _get_dev_html(self) -> str:
        """Get development HTML (when frontend not built)."""
        return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Governor Dashboard</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        .card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        .approval {
            border-left: 4px solid #667eea;
            padding-left: 15px;
            margin: 15px 0;
        }
        button {
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .approve { background: #10b981; color: white; }
        .reject { background: #ef4444; color: white; }
        .status {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: 600;
        }
        .status.pending { background: #fef3c7; color: #92400e; }
        .status.approved { background: #d1fae5; color: #065f46; }
        .status.rejected { background: #fee2e2; color: #991b1b; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Governor Dashboard</h1>
        <p>Approval Flow Visualization & Management</p>
    </div>

    <div class="card">
        <h2>📋 Pending Approvals</h2>
        <div id="pending-approvals">Loading...</div>
    </div>

    <div class="card">
        <h2>📊 Registered Flows</h2>
        <div id="flows">Loading...</div>
    </div>

    <div class="card">
        <h2>📜 Approval History</h2>
        <div id="history">Loading...</div>
    </div>

    <script>
        async function fetchPendingApprovals() {
            const res = await fetch('/api/approvals/pending');
            const data = await res.json();
            const container = document.getElementById('pending-approvals');

            if (data.pending_approvals.length === 0) {
                container.innerHTML = '<p>No pending approvals</p>';
                return;
            }

            container.innerHTML = data.pending_approvals.map(approval => `
                <div class="approval">
                    <h3>${approval.function_name}</h3>
                    <p><strong>Execution ID:</strong> ${approval.execution_id}</p>
                    <p><strong>Started:</strong> ${new Date(approval.started_at).toLocaleString()}</p>
                    <p><strong>Stage:</strong> ${approval.current_stage || 'N/A'}</p>
                    <button class="approve" onclick="approveExecution('${approval.execution_id}')">
                        ✓ Approve
                    </button>
                    <button class="reject" onclick="rejectExecution('${approval.execution_id}')">
                        ✗ Reject
                    </button>
                </div>
            `).join('');
        }

        async function fetchFlows() {
            const res = await fetch('/api/flows');
            const data = await res.json();
            const container = document.getElementById('flows');

            if (data.flows.length === 0) {
                container.innerHTML = '<p>No flows registered</p>';
                return;
            }

            container.innerHTML = data.flows.map(flow => `
                <div style="margin: 15px 0; padding: 15px; background: #f9fafb; border-radius: 5px;">
                    <h3>${flow.function_name}</h3>
                    <p>${flow.description}</p>
                    <p><strong>Stages:</strong> ${flow.stages.length}</p>
                    <ul>
                        ${flow.stages.map((stage, i) => `
                            <li><strong>Stage ${i + 1}:</strong> ${stage.name} (${stage.approvers.join(', ')})</li>
                        `).join('')}
                    </ul>
                </div>
            `).join('');
        }

        async function fetchHistory() {
            const res = await fetch('/api/approvals/history?limit=10');
            const data = await res.json();
            const container = document.getElementById('history');

            if (data.history.length === 0) {
                container.innerHTML = '<p>No history available</p>';
                return;
            }

            container.innerHTML = '<table style="width: 100%; border-collapse: collapse;">' +
                '<tr style="text-align: left; border-bottom: 2px solid #e5e7eb;">' +
                '<th style="padding: 10px;">Function</th>' +
                '<th style="padding: 10px;">Status</th>' +
                '<th style="padding: 10px;">Started</th>' +
                '<th style="padding: 10px;">Duration</th>' +
                '</tr>' +
                data.history.map(item => `
                    <tr style="border-bottom: 1px solid #e5e7eb;">
                        <td style="padding: 10px;">${item.function_name}</td>
                        <td style="padding: 10px;">
                            <span class="status ${item.status}">${item.status}</span>
                        </td>
                        <td style="padding: 10px;">${new Date(item.started_at).toLocaleString()}</td>
                        <td style="padding: 10px;">${item.duration_ms ? item.duration_ms + 'ms' : 'N/A'}</td>
                    </tr>
                `).join('') +
                '</table>';
        }

        async function approveExecution(executionId) {
            const approver = prompt('Enter your name:');
            if (!approver) return;

            await fetch(`/api/approvals/${executionId}/approve?approver=${encodeURIComponent(approver)}`, {
                method: 'POST'
            });

            alert('Approved!');
            fetchPendingApprovals();
            fetchHistory();
        }

        async function rejectExecution(executionId) {
            const approver = prompt('Enter your name:');
            if (!approver) return;

            const reason = prompt('Rejection reason (optional):');

            await fetch(`/api/approvals/${executionId}/reject?approver=${encodeURIComponent(approver)}&reason=${encodeURIComponent(reason || '')}`, {
                method: 'POST'
            });

            alert('Rejected!');
            fetchPendingApprovals();
            fetchHistory();
        }

        // Initial load
        fetchPendingApprovals();
        fetchFlows();
        fetchHistory();

        // Refresh every 3 seconds
        setInterval(() => {
            fetchPendingApprovals();
            fetchHistory();
        }, 3000);

        // WebSocket connection for real-time updates
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.type === 'approval_granted' || data.type === 'approval_rejected') {
                fetchPendingApprovals();
                fetchHistory();
            }
        };
    </script>
</body>
</html>
        """

    async def start(self):
        """Start the dashboard server."""
        import uvicorn

        print(f"🚀 Governor Dashboard starting...")
        print(f"📊 Dashboard: http://{self.host}:{self.port}")
        print(f"📡 API: http://{self.host}:{self.port}/api")
        print(f"🔌 WebSocket: ws://{self.host}:{self.port}/ws")

        config = uvicorn.Config(
            self.app,
            host=self.host,
            port=self.port,
            log_level="info"
        )
        server = uvicorn.Server(config)
        await server.serve()


def create_dashboard(
    storage: Optional[StorageBackend] = None,
    approval_manager: Optional[ApprovalManager] = None,
    host: str = "0.0.0.0",
    port: int = 8765,
) -> DashboardServer:
    """
    Create a dashboard server instance.

    Args:
        storage: Storage backend
        approval_manager: Approval manager
        host: Host to bind to
        port: Port to bind to

    Returns:
        DashboardServer instance
    """
    return DashboardServer(
        storage=storage,
        approval_manager=approval_manager,
        host=host,
        port=port,
    )
