"""
Governor Dashboard - Web UI for approval flow visualization.

Provides a web-based dashboard to:
- Visualize approval flows and stages
- View pending approvals
- Approve/reject from browser
- Real-time updates via WebSocket
- Audit trail and history
"""

from governor.dashboard.server import DashboardServer, create_dashboard

__all__ = [
    "DashboardServer",
    "create_dashboard",
]
