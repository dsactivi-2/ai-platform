"""
Governor Dashboard Example

This example demonstrates the web-based dashboard for visualizing and
managing approval flows in real-time.

The dashboard provides:
- Visual representation of approval pipelines
- List of pending approvals
- Interactive approve/reject buttons
- Real-time updates via WebSocket
- Approval history and audit trail

Run this example and open http://localhost:8765 in your browser to see the dashboard.
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy, AuditPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.storage.memory import InMemoryStorage
from governor.dashboard import create_dashboard


# Shared storage
storage = InMemoryStorage()


async def main():
    """Run dashboard example with multiple approval flows."""

    print("\n" + "=" * 80)
    print("Governor Dashboard Example")
    print("=" * 80)

    # Create dashboard
    dashboard = create_dashboard(
        storage=storage,
        host="0.0.0.0",
        port=8765
    )

    # Register approval flows for visualization
    dashboard.register_flow(
        function_name="deploy_ai_model",
        description="AI Model Deployment Pipeline",
        stages=[
            {
                "name": "AI Safety Team",
                "approvers": ["ai-safety-lead@company.com"],
                "description": "Review for bias, safety, and ethical concerns",
            },
            {
                "name": "Software Security Team",
                "approvers": ["security-lead@company.com"],
                "description": "Security vulnerability and data leak review",
            },
            {
                "name": "Executive Team",
                "approvers": ["cto@company.com"],
                "description": "Business decision and final authorization",
            },
        ],
        metadata={
            "category": "AI/ML",
            "risk_level": "high",
        }
    )

    dashboard.register_flow(
        function_name="process_wire_transfer",
        description="Financial Wire Transfer Approval",
        stages=[
            {
                "name": "Manager Approval",
                "approvers": ["manager@company.com"],
                "description": "Direct manager approval",
            },
            {
                "name": "Finance Team",
                "approvers": ["finance-lead@company.com"],
                "description": "Finance compliance and budget check",
            },
            {
                "name": "CFO Approval",
                "approvers": ["cfo@company.com"],
                "description": "C-level authorization for large transactions",
            },
        ],
        metadata={
            "category": "Financial",
            "compliance": ["SOC2", "PCI-DSS"],
        }
    )

    dashboard.register_flow(
        function_name="grant_data_access",
        description="Data Access Request Pipeline",
        stages=[
            {
                "name": "Team Lead",
                "approvers": ["team-lead@company.com"],
                "description": "Verify legitimate business need",
            },
            {
                "name": "Privacy Team",
                "approvers": ["privacy-officer@company.com"],
                "description": "PII and GDPR compliance review",
            },
            {
                "name": "Legal & Compliance",
                "approvers": ["legal@company.com"],
                "description": "Regulatory and legal approval",
            },
        ],
        metadata={
            "category": "Data Access",
            "compliance": ["GDPR", "HIPAA"],
        }
    )

    # Define some governed functions that will create pending approvals
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["ai-safety-lead@company.com"],
                timeout_seconds=3600,
            ),
            AuditPolicy(compliance_tags=["AI_DEPLOYMENT"])
        ],
        storage=storage,
    )
    async def deploy_ai_model(model_name: str, version: str, risk_level: str = "medium"):
        """Deploy AI model after approval."""
        print(f"   Deploying model: {model_name} v{version}")
        return {
            "status": "deployed",
            "model": model_name,
            "version": version,
            "deployed_at": datetime.now().isoformat()
        }

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["manager@company.com"],
                timeout_seconds=1800,
            ),
            AuditPolicy(compliance_tags=["FINANCIAL"])
        ],
        storage=storage,
    )
    async def process_wire_transfer(amount: float, recipient: str, purpose: str):
        """Process wire transfer after approval."""
        print(f"   Processing ${amount:,.2f} transfer to {recipient}")
        return {
            "status": "completed",
            "amount": amount,
            "recipient": recipient,
            "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["team-lead@company.com"],
                timeout_seconds=7200,
            ),
            AuditPolicy(compliance_tags=["DATA_ACCESS", "GDPR"])
        ],
        storage=storage,
    )
    async def grant_data_access(
        user_id: str,
        data_type: str,
        sensitivity: str = "confidential"
    ):
        """Grant data access after approval."""
        print(f"   Granting access to {data_type} for {user_id}")
        return {
            "status": "granted",
            "user_id": user_id,
            "data_type": data_type,
            "access_token": f"TOKEN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    # Create some pending approvals in the background
    async def create_pending_approvals():
        """Create some pending approval requests."""
        await asyncio.sleep(2)  # Wait for dashboard to start

        print("\n📝 Creating pending approval requests...")

        # These will timeout and wait for approval
        try:
            await asyncio.wait_for(
                deploy_ai_model("gpt-custom-finance", "2.0.1", "high"),
                timeout=1
            )
        except asyncio.TimeoutError:
            print("   ✓ AI model deployment pending approval")

        try:
            await asyncio.wait_for(
                process_wire_transfer(250000, "BigCorp Inc", "Strategic partnership"),
                timeout=1
            )
        except asyncio.TimeoutError:
            print("   ✓ Wire transfer pending approval")

        try:
            await asyncio.wait_for(
                grant_data_access("user789", "customer-financial-records", "highly-confidential"),
                timeout=1
            )
        except asyncio.TimeoutError:
            print("   ✓ Data access request pending approval")

        print("\n✅ Pending approvals created!")
        print("📊 Go to http://localhost:8765 to view and manage approvals\n")

    # Start creating pending approvals in background
    asyncio.create_task(create_pending_approvals())

    # Start dashboard server
    print("\n🚀 Starting Governor Dashboard...")
    print("=" * 80)
    print("📊 Dashboard URL: http://localhost:8765")
    print("📡 API Docs: http://localhost:8765/docs")
    print("🔌 WebSocket: ws://localhost:8765/ws")
    print("=" * 80)
    print("\nThe dashboard will show:")
    print("  • Registered approval flows with stages")
    print("  • Pending approvals (you can approve/reject from browser)")
    print("  • Real-time updates when approvals change")
    print("  • Approval history and audit trail")
    print("\nPress Ctrl+C to stop the server")
    print("=" * 80 + "\n")

    # Start server (this will block)
    await dashboard.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 Dashboard stopped")
