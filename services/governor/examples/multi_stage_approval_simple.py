"""
Simple Multi-Stage Approval Example

This example demonstrates how to create approval pipelines using the current framework
by chaining multiple governed functions together. Each function represents a stage.

Examples:
- Stage 1: AI Safety Team approval → Stage 2: Security Team approval
- Stage 1: Manager approval → Stage 2: Finance approval → Stage 3: CFO approval
"""

import asyncio
from datetime import datetime

from governor import govern, ApprovalPolicy, AuditPolicy, ValidationPolicy
from governor.approval.handlers import CallbackApprovalHandler
from governor.storage.memory import InMemoryStorage


# Shared storage
storage = InMemoryStorage()


# ==============================================================================
# EXAMPLE 1: AI Model Deployment with Sequential Approvals
# ==============================================================================
# AI Safety Team → Software Security Team → Executive Approval
# ==============================================================================

async def example_ai_model_deployment():
    """
    AI Model Deployment with 3-stage approval using function chaining.
    Each stage is a separate governed function that calls the next.
    """
    print("=" * 80)
    print("EXAMPLE 1: AI Model Deployment - 3 Stage Approval Pipeline")
    print("=" * 80)

    # Track approval history
    approval_history = []

    # Create approval handlers for each stage
    async def ai_safety_approval(exec_id, func_name, inputs, approvers):
        """Stage 1: AI Safety Team approval"""
        print(f"\n📋 STAGE 1: AI Safety Team Review")
        print(f"   Approvers: {', '.join(approvers)}")
        print(f"   Checking for bias, safety, and ethical concerns...")
        await asyncio.sleep(0.5)
        print(f"   ✓ Approved by {approvers[0]}")
        approval_history.append(("AI Safety Team", approvers[0]))
        return (True, approvers[0], "No safety concerns found")

    async def security_approval(exec_id, func_name, inputs, approvers):
        """Stage 2: Security Team approval"""
        print(f"\n📋 STAGE 2: Software Security Team Review")
        print(f"   Approvers: {', '.join(approvers)}")
        print(f"   Checking for vulnerabilities and data leaks...")
        await asyncio.sleep(0.5)
        print(f"   ✓ Approved by {approvers[0]}")
        approval_history.append(("Security Team", approvers[0]))
        return (True, approvers[0], "Security review passed")

    async def executive_approval(exec_id, func_name, inputs, approvers):
        """Stage 3: Executive approval"""
        print(f"\n📋 STAGE 3: Executive Team Review")
        print(f"   Approvers: {', '.join(approvers)}")
        print(f"   Business decision and final authorization...")
        await asyncio.sleep(0.5)
        print(f"   ✓ Approved by {approvers[0]}")
        approval_history.append(("Executive Team", approvers[0]))
        return (True, approvers[0], "Deployment authorized")

    # Stage 3: Executive approval (final stage)
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["cto@company.com"],
                timeout_seconds=7200,
                # Auto-approve for low-risk models
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("risk_level", "") == "low"
            ),
            AuditPolicy(compliance_tags=["STAGE_3_EXECUTIVE"])
        ],
        approval_handler=CallbackApprovalHandler(callback=executive_approval),
        storage=storage,
    )
    async def stage3_executive_approval(model_name, version, risk_level, target_env):
        """Final deployment after executive approval."""
        print(f"\n🚀 Deploying model: {model_name} v{version}")
        print(f"   Risk level: {risk_level}")
        print(f"   Target: {target_env}")

        await asyncio.sleep(0.3)

        return {
            "status": "deployed",
            "model": model_name,
            "version": version,
            "environment": target_env,
            "deployed_at": datetime.now().isoformat()
        }

    # Stage 2: Security approval → calls Stage 3
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["security-lead@company.com"],
                timeout_seconds=3600,
            ),
            AuditPolicy(compliance_tags=["STAGE_2_SECURITY"])
        ],
        approval_handler=CallbackApprovalHandler(callback=security_approval),
        storage=storage,
    )
    async def stage2_security_approval(model_name, version, risk_level, target_env):
        """Security approval, then move to executive."""
        # Call next stage
        return await stage3_executive_approval(model_name, version, risk_level, target_env)

    # Stage 1: AI Safety approval → calls Stage 2
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["ai-safety-lead@company.com"],
                timeout_seconds=3600,
                # Auto-approve test models
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("model_name", "").startswith("test-")
            ),
            AuditPolicy(
                compliance_tags=["STAGE_1_AI_SAFETY", "AI_GOVERNANCE"]
            )
        ],
        approval_handler=CallbackApprovalHandler(callback=ai_safety_approval),
        storage=storage,
    )
    async def deploy_ai_model(model_name, version, risk_level="medium", target_env="production"):
        """Entry point: AI Safety approval, then moves to next stage."""
        # Call next stage
        return await stage2_security_approval(model_name, version, risk_level, target_env)

    print("\n--- Scenario: Production Model (requires all 3 approvals) ---")

    result = await deploy_ai_model(
        model_name="gpt-custom-finance",
        version="2.0.1",
        risk_level="high",
        target_env="production"
    )

    print(f"\n✓ Deployment completed!")
    print(f"   Result: {result}")
    print(f"\n📊 Approval Pipeline:")
    for i, (stage, approver) in enumerate(approval_history, 1):
        print(f"   {i}. {stage} ✓ - {approver}")

    approval_history.clear()


# ==============================================================================
# EXAMPLE 2: Financial Transaction with Tiered Approvals
# ==============================================================================
# Manager → Finance Team → CFO
# ==============================================================================

async def example_financial_transaction():
    """
    Financial transaction with amount-based approval tiers.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 2: Financial Transaction - Tiered Approval Pipeline")
    print("=" * 80)

    # Stage 3: CFO approval (for very large amounts)
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["cfo@company.com"],
                # Only required for amounts >= $100,000
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("amount", 0) < 100000
            ),
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   💰 CFO approved ${i.get('kwargs', {}).get('amount', 0):,.2f} transaction"),
                (True, "cfo@company.com", "Approved")
            )[2]
        ),
        storage=storage,
    )
    async def stage3_cfo_approval(amount, recipient, purpose):
        """Final transaction after CFO approval."""
        print(f"\n✓ Transaction completed: ${amount:,.2f} to {recipient}")
        return {
            "status": "completed",
            "amount": amount,
            "recipient": recipient,
            "transaction_id": f"TXN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    # Stage 2: Finance team approval (for medium amounts)
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["finance-lead@company.com"],
                # Only required for amounts >= $25,000
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("amount", 0) < 25000
            ),
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   💼 Finance team approved ${i.get('kwargs', {}).get('amount', 0):,.2f} transaction"),
                (True, "finance-lead@company.com", "Approved")
            )[2]
        ),
        storage=storage,
    )
    async def stage2_finance_approval(amount, recipient, purpose):
        """Finance approval, then move to CFO."""
        return await stage3_cfo_approval(amount, recipient, purpose)

    # Stage 1: Manager approval
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["manager@company.com"],
                # Auto-approve small amounts
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("amount", 0) < 5000
            ),
            AuditPolicy(compliance_tags=["FINANCIAL", "TRANSACTION"])
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   👔 Manager approved ${i.get('kwargs', {}).get('amount', 0):,.2f} transaction"),
                (True, "manager@company.com", "Approved")
            )[2]
        ),
        storage=storage,
    )
    async def process_wire_transfer(amount, recipient, purpose):
        """Entry point: Manager approval first."""
        return await stage2_finance_approval(amount, recipient, purpose)

    print("\n--- Scenario 1: Small transfer ($3,000 - auto-approved) ---")
    result = await process_wire_transfer(3000, "Vendor ABC", "Office supplies")
    print(f"   Transaction ID: {result['transaction_id']}")

    print("\n--- Scenario 2: Medium transfer ($50,000 - Manager + Finance) ---")
    result = await process_wire_transfer(50000, "Contractor XYZ", "Q4 consulting")
    print(f"   Transaction ID: {result['transaction_id']}")

    print("\n--- Scenario 3: Large transfer ($250,000 - All 3 tiers) ---")
    result = await process_wire_transfer(250000, "BigCorp Inc", "Strategic partnership")
    print(f"   Transaction ID: {result['transaction_id']}")


# ==============================================================================
# EXAMPLE 3: Data Access with Conditional Stages
# ==============================================================================
# Team Lead → Privacy Team → Legal (based on sensitivity)
# ==============================================================================

async def example_data_access():
    """
    Data access request with privacy and compliance reviews.
    """
    print("\n" + "=" * 80)
    print("EXAMPLE 3: Data Access Request - Privacy & Compliance Pipeline")
    print("=" * 80)

    # Stage 3: Legal approval (for highly sensitive data)
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["legal@company.com"],
                # Only required for highly confidential data
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("sensitivity", "") != "highly-confidential"
            ),
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   ⚖️  Legal approved access to {i.get('kwargs', {}).get('data_type', '')}"),
                (True, "legal@company.com", "Legal review passed")
            )[2]
        ),
        storage=storage,
    )
    async def stage3_legal_approval(user_id, data_type, sensitivity, contains_pii):
        """Grant access after legal approval."""
        print(f"\n✓ Access granted to {data_type}")
        return {
            "status": "granted",
            "user_id": user_id,
            "data_type": data_type,
            "access_token": f"TOKEN-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        }

    # Stage 2: Privacy team approval (for PII data)
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["privacy-officer@company.com"],
                # Skip if no PII
                auto_approve_condition=lambda inputs:
                    not inputs.get("kwargs", {}).get("contains_pii", True)
            ),
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   🔒 Privacy team approved PII access for {i.get('kwargs', {}).get('data_type', '')}"),
                (True, "privacy-officer@company.com", "GDPR compliant")
            )[2]
        ),
        storage=storage,
    )
    async def stage2_privacy_approval(user_id, data_type, sensitivity, contains_pii):
        """Privacy approval, then move to legal."""
        return await stage3_legal_approval(user_id, data_type, sensitivity, contains_pii)

    # Stage 1: Team lead approval
    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["team-lead@company.com"],
                # Auto-approve public data
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("sensitivity", "") == "public"
            ),
            AuditPolicy(compliance_tags=["DATA_ACCESS", "PRIVACY"])
        ],
        approval_handler=CallbackApprovalHandler(
            callback=lambda e, f, i, a: (
                asyncio.sleep(0.3),
                print(f"   👥 Team lead approved access to {i.get('kwargs', {}).get('data_type', '')}"),
                (True, "team-lead@company.com", "Business need verified")
            )[2]
        ),
        storage=storage,
    )
    async def grant_data_access(user_id, data_type, sensitivity="confidential", contains_pii=True):
        """Entry point: Team lead approval first."""
        return await stage2_privacy_approval(user_id, data_type, sensitivity, contains_pii)

    print("\n--- Scenario 1: Public data (auto-approved) ---")
    result = await grant_data_access("user123", "public-analytics", "public", False)
    print(f"   Access token: {result['access_token']}")

    print("\n--- Scenario 2: Internal PII (Team Lead + Privacy) ---")
    result = await grant_data_access("user456", "employee-records", "internal", True)
    print(f"   Access token: {result['access_token']}")

    print("\n--- Scenario 3: Customer PII (All 3 stages) ---")
    result = await grant_data_access("user789", "customer-financials", "highly-confidential", True)
    print(f"   Access token: {result['access_token']}")


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
    print("\nHow It Works:")
    print("  • Each approval stage is a separate governed function")
    print("  • Stages are chained: Stage 1 → Stage 2 → Stage 3")
    print("  • Each stage can have auto-approve conditions")
    print("  • Full audit trail maintained across all stages")
    print("\nKey Benefits:")
    print("  • Different approvers for each stage")
    print("  • Different timeouts per stage")
    print("  • Conditional stage skipping (auto-approve)")
    print("  • Complete compliance and audit tracking")
    print("\nUse Cases:")
    print("  • AI model deployment (Safety → Security → Executive)")
    print("  • Financial transactions (Manager → Finance → CFO)")
    print("  • Data access (Team Lead → Privacy → Legal)")
    print("  • Code deployment (Tech Lead → Security → DevOps)")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
