"""
Multi-Stage Sequential Approval Example

This example demonstrates how to create approval pipelines with multiple stages:
- Stage 1: AI Safety Team approval
- Stage 2: Software Security Team approval
- Stage 3: Executive/Legal approval

Each stage must approve before moving to the next stage.
Perfect for AI model deployment, data access, financial transactions, etc.
"""

import asyncio
from datetime import datetime

from governor import govern, SequentialApprovalPolicy, ApprovalStage, AuditPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.storage.memory import InMemoryStorage


# Shared storage
storage = InMemoryStorage()


# ==============================================================================
# EXAMPLE 1: AI Model Deployment Pipeline
# ==============================================================================
# Stage 1: AI Safety Team → Stage 2: Security Team → Stage 3: Executive
# ==============================================================================

async def example_ai_model_deployment():
    """
    AI Model Deployment with 3-stage approval:
    1. AI Safety Team - checks for bias, safety issues
    2. Software Security Team - checks for vulnerabilities, data leaks
    3. Executive Team - business decision
    """
    print("=" * 80)
    print("EXAMPLE 1: AI Model Deployment - 3 Stage Approval Pipeline")
    print("=" * 80)

    # Simulate approval handlers for each stage
    approval_history = []

    async def stage_approval_handler(exec_id, func_name, inputs, approvers):
        """Simulates approval from different teams."""
        stage_name = ", ".join(approvers)
        print(f"\n📋 Approval request sent to: {stage_name}")
        print(f"   Function: {func_name}")
        print(f"   Model: {inputs.get('kwargs', {}).get('model_name', 'unknown')}")
        print(f"   Waiting for {stage_name} to review...")

        # Simulate review time
        await asyncio.sleep(1)

        # Approve
        print(f"   ✓ Approved by {approvers[0]}")
        approval_history.append({
            "stage": stage_name,
            "approver": approvers[0],
            "timestamp": datetime.now(),
            "execution_id": exec_id
        })
        return (True, approvers[0], f"Approved by {stage_name}")

    handler = CallbackApprovalHandler(callback=stage_approval_handler)

    # Define the 3-stage approval pipeline
    @govern(
        policies=[
            SequentialApprovalPolicy(
                stages=[
                    ApprovalStage(
                        name="AI Safety Team",
                        approvers=["ai-safety-lead@company.com", "ethics-team@company.com"],
                        timeout_seconds=3600,
                        description="Review model for bias, fairness, and safety concerns",
                        # Auto-approve for test models
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("model_name", "").startswith("test-")
                    ),
                    ApprovalStage(
                        name="Software Security Team",
                        approvers=["security-lead@company.com", "infosec@company.com"],
                        timeout_seconds=3600,
                        description="Review for security vulnerabilities and data leaks",
                    ),
                    ApprovalStage(
                        name="Executive Team",
                        approvers=["cto@company.com", "ceo@company.com"],
                        timeout_seconds=7200,
                        description="Business decision and final authorization",
                        # Auto-approve for low-risk models
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("risk_level", "high") == "low"
                    ),
                ]
            ),
            AuditPolicy(
                log_inputs=True,
                log_outputs=True,
                compliance_tags=["AI_GOVERNANCE", "MODEL_DEPLOYMENT"]
            )
        ],
        approval_handler=handler,
        storage=storage,
        capture_state=True,
    )
    async def deploy_ai_model(
        model_name: str,
        version: str,
        risk_level: str = "medium",
        target_env: str = "production"
    ) -> dict:
        """Deploy AI model to production after multi-stage approval."""
        print(f"\n🚀 Deploying model: {model_name} v{version}")
        print(f"   Risk level: {risk_level}")
        print(f"   Target: {target_env}")

        # Simulate deployment
        await asyncio.sleep(0.5)

        return {
            "status": "deployed",
            "model": model_name,
            "version": version,
            "environment": target_env,
            "deployed_at": datetime.now().isoformat()
        }

    print("\n--- Scenario 1: Production Model (requires all 3 approvals) ---")

    result = await deploy_ai_model(
        model_name="gpt-custom-finance",
        version="2.0.1",
        risk_level="high",
        target_env="production"
    )

    print(f"\n✓ Deployment completed!")
    print(f"   Result: {result}")
    print(f"\n📊 Approval History:")
    for i, approval in enumerate(approval_history, 1):
        print(f"   {i}. {approval['stage']} - {approval['approver']}")

    approval_history.clear()

    print("\n--- Scenario 2: Test Model (auto-approved by AI Safety) ---")

    result = await deploy_ai_model(
        model_name="test-experimental-v1",
        version="0.1.0",
        risk_level="high",
        target_env="staging"
    )

    print(f"\n✓ Deployment completed!")
    print(f"   Result: {result}")


# ==============================================================================
# EXAMPLE 2: Financial Transaction Pipeline
# ==============================================================================
# Stage 1: Manager → Stage 2: Finance → Stage 3: CFO
# ==============================================================================

async def example_financial_transaction():
    """
    Large financial transaction with tiered approvals:
    1. Direct Manager - first line approval
    2. Finance Team - compliance and budget check
    3. CFO - final authorization for large amounts
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Financial Transaction - Tiered Approval Pipeline")
    print("=" * 80)

    async def finance_approval_handler(exec_id, func_name, inputs, approvers):
        """Simulates finance approval workflow."""
        amount = inputs.get('kwargs', {}).get('amount', 0)
        print(f"\n💰 Approval request: ${amount:,.2f} transaction")
        print(f"   Approvers: {', '.join(approvers)}")
        await asyncio.sleep(0.5)
        print(f"   ✓ Approved by {approvers[0]}")
        return (True, approvers[0], f"Transaction approved")

    handler = CallbackApprovalHandler(callback=finance_approval_handler)

    @govern(
        policies=[
            SequentialApprovalPolicy(
                stages=[
                    ApprovalStage(
                        name="Manager Approval",
                        approvers=["manager@company.com"],
                        timeout_seconds=1800,
                        description="Direct manager approval",
                        # Auto-approve small amounts
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("amount", 0) < 5000
                    ),
                    ApprovalStage(
                        name="Finance Team",
                        approvers=["finance-lead@company.com"],
                        timeout_seconds=3600,
                        description="Finance compliance and budget check",
                        # Auto-approve if under department budget
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("amount", 0) < 25000
                    ),
                    ApprovalStage(
                        name="CFO Approval",
                        approvers=["cfo@company.com"],
                        timeout_seconds=7200,
                        description="C-level authorization for large transactions",
                        # Only required for very large amounts
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("amount", 0) < 100000
                    ),
                ]
            ),
            AuditPolicy(
                compliance_tags=["FINANCIAL", "SOC2", "TRANSACTION"]
            )
        ],
        approval_handler=handler,
        storage=storage,
    )
    async def process_wire_transfer(
        amount: float,
        recipient: str,
        purpose: str
    ) -> dict:
        """Process wire transfer with tiered approvals."""
        print(f"\n💸 Processing wire transfer")
        print(f"   Amount: ${amount:,.2f}")
        print(f"   Recipient: {recipient}")
        print(f"   Purpose: {purpose}")

        await asyncio.sleep(0.3)

        return {
            "status": "completed",
            "amount": amount,
            "recipient": recipient,
            "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    print("\n--- Scenario 1: Small transfer ($3,000 - auto-approved) ---")
    result = await process_wire_transfer(3000, "Vendor ABC", "Office supplies")
    print(f"✓ Transaction: {result['transaction_id']}")

    print("\n--- Scenario 2: Medium transfer ($50,000 - Manager + Finance) ---")
    result = await process_wire_transfer(50000, "Contractor XYZ", "Q4 consulting")
    print(f"✓ Transaction: {result['transaction_id']}")

    print("\n--- Scenario 3: Large transfer ($250,000 - All 3 stages) ---")
    result = await process_wire_transfer(250000, "BigCorp Inc", "Strategic partnership")
    print(f"✓ Transaction: {result['transaction_id']}")


# ==============================================================================
# EXAMPLE 3: Data Access Request Pipeline
# ==============================================================================
# Stage 1: Team Lead → Stage 2: Privacy Team → Stage 3: Legal/Compliance
# ==============================================================================

async def example_data_access():
    """
    Sensitive data access with privacy and compliance reviews:
    1. Team Lead - verify business need
    2. Privacy Team - PII and GDPR compliance
    3. Legal/Compliance - regulatory approval
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Data Access Request - Privacy & Compliance Pipeline")
    print("=" * 80)

    async def data_access_handler(exec_id, func_name, inputs, approvers):
        """Simulates data access approval workflow."""
        data_type = inputs.get('kwargs', {}).get('data_type', 'unknown')
        print(f"\n🔐 Data access request for: {data_type}")
        print(f"   Reviewers: {', '.join(approvers)}")
        await asyncio.sleep(0.5)
        print(f"   ✓ Approved by {approvers[0]}")
        return (True, approvers[0], f"Access granted")

    handler = CallbackApprovalHandler(callback=data_access_handler)

    @govern(
        policies=[
            SequentialApprovalPolicy(
                stages=[
                    ApprovalStage(
                        name="Team Lead",
                        approvers=["team-lead@company.com"],
                        description="Verify legitimate business need",
                        # Auto-approve for non-sensitive data
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("sensitivity", "") == "public"
                    ),
                    ApprovalStage(
                        name="Privacy Team",
                        approvers=["privacy-officer@company.com", "dpo@company.com"],
                        description="PII and GDPR compliance review",
                        # Skip for non-PII data
                        auto_approve_condition=lambda inputs:
                            not inputs.get("kwargs", {}).get("contains_pii", True)
                    ),
                    ApprovalStage(
                        name="Legal & Compliance",
                        approvers=["legal@company.com", "compliance@company.com"],
                        timeout_seconds=7200,
                        description="Regulatory and legal approval",
                        # Skip for internal-only data
                        auto_approve_condition=lambda inputs:
                            inputs.get("kwargs", {}).get("data_type", "").startswith("internal-")
                    ),
                ]
            ),
            AuditPolicy(
                compliance_tags=["DATA_ACCESS", "GDPR", "PRIVACY"],
                log_inputs=True
            )
        ],
        approval_handler=handler,
        storage=storage,
    )
    async def grant_data_access(
        user_id: str,
        data_type: str,
        sensitivity: str = "confidential",
        contains_pii: bool = True,
        purpose: str = ""
    ) -> dict:
        """Grant access to sensitive data after approvals."""
        print(f"\n🔓 Granting data access")
        print(f"   User: {user_id}")
        print(f"   Data: {data_type}")
        print(f"   Sensitivity: {sensitivity}")

        await asyncio.sleep(0.3)

        return {
            "status": "granted",
            "user_id": user_id,
            "data_type": data_type,
            "access_token": f"TOKEN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "expires_in": 3600
        }

    print("\n--- Scenario 1: Public data (auto-approved) ---")
    result = await grant_data_access(
        "user123",
        "public-analytics",
        sensitivity="public",
        contains_pii=False,
        purpose="Dashboard reporting"
    )
    print(f"✓ Access granted: {result['access_token']}")

    print("\n--- Scenario 2: Internal data (Team Lead + Privacy) ---")
    result = await grant_data_access(
        "user456",
        "internal-employee-directory",
        sensitivity="internal",
        contains_pii=True,
        purpose="Org chart analysis"
    )
    print(f"✓ Access granted: {result['access_token']}")

    print("\n--- Scenario 3: Customer PII (All 3 stages) ---")
    result = await grant_data_access(
        "user789",
        "customer-financial-records",
        sensitivity="highly-confidential",
        contains_pii=True,
        purpose="Fraud investigation"
    )
    print(f"✓ Access granted: {result['access_token']}")


# ==============================================================================
# MAIN
# ==============================================================================

async def main():
    """Run all multi-stage approval examples."""
    print("\n")
    print("╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "MULTI-STAGE APPROVAL PIPELINES" + " " * 28 + "║")
    print("╚" + "═" * 78 + "╝")

    await example_ai_model_deployment()
    await example_financial_transaction()
    await example_data_access()

    print("\n" + "=" * 80)
    print("✓ All examples completed!")
    print("\nKey Features:")
    print("  • Sequential approval stages (each must approve before next)")
    print("  • Auto-approve conditions (skip stages based on criteria)")
    print("  • Different approvers for each stage")
    print("  • Different timeouts per stage")
    print("  • Full audit trail for compliance")
    print("\nUse Cases:")
    print("  • AI model deployment (Safety → Security → Executive)")
    print("  • Financial transactions (Manager → Finance → CFO)")
    print("  • Data access (Team Lead → Privacy → Legal)")
    print("  • Code deployment (Tech Lead → Security → DevOps)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
