"""Criteria-based conditional governance examples."""

import asyncio
from governor import (
    govern,
    ValidationPolicy,
    AuthorizationPolicy,
    RateLimitPolicy,
    AuditPolicy,
    ApprovalPolicy,
)
from governor.core.context import ExecutionContext


# Example 1: Conditional approval based on amount thresholds
async def example_threshold_based_approval() -> None:
    """
    Apply different governance based on transaction amount.

    Small amounts: Auto-approve
    Medium amounts: Require team lead approval
    Large amounts: Require executive approval
    """
    print("=" * 70)
    print("Example 1: Threshold-Based Approval")
    print("=" * 70)

    @govern(
        policies=[
            ValidationPolicy(input_validator=lambda x: x.get("kwargs", {}).get("amount", 0) > 0),
            AuditPolicy(compliance_tags=["financial", "SOC2"]),
            # Auto-approve if less than $1000
            ApprovalPolicy(
                name="SmallTransactionApproval",
                approvers=["team-lead@company.com"],
                auto_approve_condition=lambda inputs: inputs.get("kwargs", {}).get("amount", float("inf")) < 1000,
            ),
        ]
    )
    async def process_transaction(amount: float, account: str, _description: str) -> dict:
        """Process financial transaction with conditional approval."""
        print(f"💰 Processing ${amount} to {account}")
        return {
            "transaction_id": "TXN123",
            "amount": amount,
            "account": account,
            "status": "completed",
        }

    # Small transaction - auto-approved
    print("\n1. Small transaction ($500) - auto-approved:")
    result = await process_transaction(500.0, "ACC001", "Office supplies")
    print(f"   ✓ {result}")

    # Large transaction - would require approval (commented for demo)
    # print("\n2. Large transaction ($5000) - requires approval:")
    # result = await process_transaction(5000.0, "ACC002", "Equipment purchase")
    # print(f"   ✓ {result}")


# Example 2: Environment-based governance (dev vs prod)
async def example_environment_based() -> None:
    """Apply stricter governance in production environments."""
    print("\n" + "=" * 70)
    print("Example 2: Environment-Based Governance")
    print("=" * 70)

    async def get_policies_for_environment(environment: str) -> list:
        """Return appropriate policies based on environment."""
        base_policies = [
            ValidationPolicy(input_validator=lambda x: len(x.get("kwargs", {})) > 0),
            AuditPolicy(),
        ]

        if environment == "production":
            # Production: Strict rate limits, authorization required
            return base_policies + [
                AuthorizationPolicy(required_roles={"admin"}),
                RateLimitPolicy(max_calls=10, window_seconds=60),
                ApprovalPolicy(approvers=["sre@company.com"]),
            ]
        elif environment == "staging":
            # Staging: Moderate rate limits
            return base_policies + [
                RateLimitPolicy(max_calls=100, window_seconds=60),
            ]
        else:
            # Development: No additional restrictions
            return base_policies

    # Production deployment (would require approval)
    @govern(
        policies=await get_policies_for_environment("development"),
        context={"environment": "development"},
    )
    async def deploy_service(service_name: str, version: str) -> dict:
        """Deploy a service to specified environment."""
        print(f"🚀 Deploying {service_name} v{version}")
        return {"deployed": True, "service": service_name, "version": version}

    print("\n1. Development deployment - minimal governance:")
    result = await deploy_service("api-service", "1.2.3")
    print(f"   ✓ {result}")


# Example 3: Risk-based governance
async def example_risk_based() -> None:
    """Apply governance based on calculated risk level."""
    print("\n" + "=" * 70)
    print("Example 3: Risk-Based Governance")
    print("=" * 70)

    def calculate_risk_score(operation: str, data_size: int, user_role: str) -> int:
        """Calculate risk score for an operation."""
        score = 0

        # Operation risk
        if operation == "delete":
            score += 50
        elif operation == "modify":
            score += 30
        elif operation == "read":
            score += 10

        # Data size risk
        if data_size > 1000:
            score += 30
        elif data_size > 100:
            score += 15

        # User role risk mitigation
        if user_role == "admin":
            score -= 20
        elif user_role == "power_user":
            score -= 10

        return max(0, score)

    @govern(
        policies=[
            AuditPolicy(compliance_tags=["data_ops"]),
            # Approval required if risk score > 50
            ApprovalPolicy(
                approvers=["data-admin@company.com"],
                auto_approve_condition=lambda inputs: calculate_risk_score(
                    inputs.get("kwargs", {}).get("operation", "read"),
                    inputs.get("kwargs", {}).get("data_size", 0),
                    inputs.get("kwargs", {}).get("user_role", "user"),
                )
                <= 50,
            ),
        ]
    )
    async def data_operation(
        operation: str, dataset_id: str, data_size: int, user_role: str
    ) -> dict:
        """Perform data operation with risk-based governance."""
        risk_score = calculate_risk_score(operation, data_size, user_role)
        print(
            f"📊 {operation.upper()} operation on {dataset_id} "
            f"(size: {data_size}, role: {user_role}) - Risk Score: {risk_score}"
        )
        return {
            "operation": operation,
            "dataset_id": dataset_id,
            "risk_score": risk_score,
            "status": "completed",
        }

    # Low risk: Small read operation by admin
    print("\n1. Low risk operation (score: 10) - auto-approved:")
    result = await data_operation("read", "dataset-001", 50, "admin")
    print(f"   ✓ {result}")

    # Medium risk: Modify operation
    print("\n2. Medium risk operation (score: 45) - auto-approved:")
    result = await data_operation("modify", "dataset-002", 200, "power_user")
    print(f"   ✓ {result}")

    # High risk would require approval (commented for demo)
    # print("\n3. High risk operation (score: 80) - requires approval:")
    # result = await data_operation("delete", "dataset-003", 2000, "user")
    # print(f"   ✓ {result}")


# Example 4: Time-based governance (business hours vs off-hours)
async def example_time_based() -> None:
    """Apply different governance during business hours vs off-hours."""
    print("\n" + "=" * 70)
    print("Example 4: Time-Based Governance")
    print("=" * 70)

    from datetime import datetime

    def is_business_hours() -> bool:
        """Check if current time is during business hours (9 AM - 5 PM weekdays)."""
        now = datetime.now()
        return (
            now.weekday() < 5  # Monday-Friday
            and 9 <= now.hour < 17  # 9 AM - 5 PM
        )

    @govern(
        policies=[
            AuditPolicy(log_inputs=True, log_outputs=True),
            # Off-hours deployments require approval
            ApprovalPolicy(
                approvers=["on-call@company.com"],
                auto_approve_condition=lambda inputs: is_business_hours(),
            ),
        ]
    )
    async def production_deployment(service: str, commit_hash: str) -> dict:
        """Deploy to production with time-based approval."""
        is_bh = is_business_hours()
        print(f"🕐 Deploying {service}@{commit_hash[:8]} ({'business hours' if is_bh else 'off-hours'})")
        return {
            "service": service,
            "commit": commit_hash,
            "deployed_at": datetime.now().isoformat(),
            "auto_approved": is_bh,
        }

    print("\n1. Deployment (check if business hours):")
    result = await production_deployment("api-gateway", "abc123def456")
    print(f"   ✓ {result}")


# Example 5: Multi-criteria conditional governance
async def example_multi_criteria() -> None:
    """Combine multiple criteria for complex governance decisions."""
    print("\n" + "=" * 70)
    print("Example 5: Multi-Criteria Governance")
    print("=" * 70)

    def should_require_approval(
        cost: float, environment: str, user_role: str, urgency: str
    ) -> bool:
        """
        Complex approval logic based on multiple factors.

        Auto-approve if:
        - Cost < $500 in any environment
        - User is admin in dev/staging
        - Urgent request < $2000 by power_user or admin
        """
        # Small cost - always auto-approve
        if cost < 500:
            return False

        # Admin in non-prod
        if user_role == "admin" and environment != "production":
            return False

        # Urgent with reasonable cost and proper role
        if urgency == "high" and cost < 2000 and user_role in ("admin", "power_user"):
            return False

        # Everything else requires approval
        return True

    @govern(
        policies=[
            ValidationPolicy(
                input_validator=lambda x: all(
                    k in x.get("kwargs", {})
                    for k in ["cost", "environment", "user_role", "urgency"]
                )
            ),
            AuditPolicy(compliance_tags=["resource_provisioning"]),
            ApprovalPolicy(
                approvers=["resource-admin@company.com"],
                auto_approve_condition=lambda inputs: not should_require_approval(
                    inputs.get("kwargs", {}).get("cost", 0),
                    inputs.get("kwargs", {}).get("environment", "production"),
                    inputs.get("kwargs", {}).get("user_role", "user"),
                    inputs.get("kwargs", {}).get("urgency", "low"),
                ),
            ),
        ]
    )
    async def provision_resources(
        resource_type: str,
        cost: float,
        environment: str,
        user_role: str,
        urgency: str,
    ) -> dict:
        """Provision cloud resources with multi-criteria governance."""
        needs_approval = should_require_approval(cost, environment, user_role, urgency)
        print(
            f"☁️  Provisioning {resource_type} in {environment} "
            f"(${cost}, role: {user_role}, urgency: {urgency}) "
            f"{'⚠️  Needs approval' if needs_approval else '✓ Auto-approved'}"
        )
        return {
            "resource_type": resource_type,
            "cost": cost,
            "environment": environment,
            "needed_approval": needs_approval,
            "status": "provisioned",
        }

    # Scenario 1: Small cost - auto-approved
    print("\n1. Small cost ($300) - auto-approved:")
    result = await provision_resources("t3.micro", 300, "production", "user", "low")
    print(f"   ✓ {result}")

    # Scenario 2: Admin in staging - auto-approved
    print("\n2. Admin in staging ($1500) - auto-approved:")
    result = await provision_resources("t3.large", 1500, "staging", "admin", "low")
    print(f"   ✓ {result}")

    # Scenario 3: Urgent request by power_user - auto-approved
    print("\n3. Urgent request by power_user ($1800) - auto-approved:")
    result = await provision_resources("t3.xlarge", 1800, "production", "power_user", "high")
    print(f"   ✓ {result}")

    # Scenario 4: Would require approval (commented for demo)
    # print("\n4. Expensive non-urgent by regular user - requires approval:")
    # result = await provision_resources("t3.2xlarge", 3000, "production", "user", "low")
    # print(f"   ✓ {result}")


# Example 6: Dynamic policy selection based on criteria
async def example_dynamic_policies() -> None:
    """Dynamically select which policies to apply based on request criteria."""
    print("\n" + "=" * 70)
    print("Example 6: Dynamic Policy Selection")
    print("=" * 70)

    async def log_action(ctx: ExecutionContext) -> None:
        """Log the action being performed."""
        action_type = ctx.metadata.get("action_type", "unknown")
        print(f"   [LOG] {action_type} action initiated - execution {ctx.execution_id[:8]}")

    # Sensitive actions get full governance
    @govern(
        pre=[log_action],
        policies=[
            ValidationPolicy(input_validator=lambda x: x.get("kwargs", {}).get("action_type") in ["read", "write", "delete"]),
            AuditPolicy(sensitive_fields=["api_key", "password"]),
            # Only sensitive actions require approval
            ApprovalPolicy(
                approvers=["security@company.com"],
                auto_approve_condition=lambda inputs: inputs.get("kwargs", {}).get("action_type", "") != "delete",
            ),
        ],
        context=lambda **kwargs: {"action_type": kwargs.get("action_type", "unknown")},
    )
    async def execute_action(action_type: str, resource_id: str, _data: dict) -> dict:
        """Execute action with criteria-based governance."""
        print(f"   ⚡ Executing {action_type.upper()} on {resource_id}")
        return {
            "action": action_type,
            "resource_id": resource_id,
            "status": "completed",
        }

    print("\n1. Read action - auto-approved:")
    result = await execute_action("read", "resource-001", {"key": "value"})
    print(f"   ✓ {result}")

    print("\n2. Write action - auto-approved:")
    result = await execute_action("write", "resource-002", {"key": "new_value"})
    print(f"   ✓ {result}")

    # Delete would require approval (commented for demo)
    # print("\n3. Delete action - requires approval:")
    # result = await execute_action("delete", "resource-003", {})
    # print(f"   ✓ {result}")


# Example 7: ADDITIVE Criteria - Criteria PLUS Approval
async def example_additive_criteria() -> None:
    """
    Demonstrate ADDITIVE criteria where multiple conditions must ALL pass.

    This shows governance that requires:
    1. Criteria A to be met AND
    2. Criteria B to be met AND
    3. Approval from specific person
    """
    print("\n" + "=" * 70)
    print("Example 7: ADDITIVE Criteria (Criteria + Approval)")
    print("=" * 70)

    @govern(
        policies=[
            # CRITERION 1: Must be valid amount
            ValidationPolicy(
                name="AmountValidation",
                input_validator=lambda x: x.get("kwargs", {}).get("amount", 0) > 0
            ),
            # CRITERION 2: Must have proper authorization
            AuthorizationPolicy(
                name="RoleCheck",
                required_roles={"finance", "admin"},
            ),
            # CRITERION 3: Rate limit must not be exceeded
            RateLimitPolicy(
                name="TransactionRateLimit",
                max_calls=5,
                window_seconds=60
            ),
            # CRITERION 4: Must pass audit requirements
            AuditPolicy(
                name="ComplianceAudit",
                compliance_tags=["SOC2", "PCI-DSS"],
                sensitive_fields=["account_number"]
            ),
            # CRITERION 5: PLUS approval for large amounts
            # Even if all above pass, still needs approval if amount >= $10,000
            ApprovalPolicy(
                name="LargeAmountApproval",
                approvers=["cfo@company.com"],
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("amount", 0) < 10000
            ),
        ],
        context={"user": {"roles": ["finance"], "id": "user123"}},
    )
    async def secure_wire_transfer(amount: float, _account_number: str, recipient: str) -> dict:
        """
        Wire transfer that requires ALL criteria:
        - Valid amount (>0)
        - User has finance/admin role
        - Within rate limit
        - Audit trail created
        - CFO approval for amounts >= $10k
        """
        print(f"💸 Wire transfer: ${amount} to {recipient}")
        return {
            "transfer_id": "WIRE123",
            "amount": amount,
            "recipient": recipient,
            "status": "completed"
        }

    print("\n1. Small transfer ($5,000) - all criteria pass, auto-approved:")
    result = await secure_wire_transfer(5000, "ACC-123-456", "Vendor Corp")
    print(f"   ✓ {result}")

    print("\n2. Medium transfer ($9,500) - all criteria pass, auto-approved:")
    result = await secure_wire_transfer(9500, "ACC-789-012", "Supplier Inc")
    print(f"   ✓ {result}")

    # Large transfer would require approval (commented for demo)
    # print("\n3. Large transfer ($50,000) - all criteria must pass PLUS CFO approval:")
    # result = await secure_wire_transfer(50000, "ACC-345-678", "Major Vendor")
    # print(f"   ✓ {result}")


# Example 8: Layered Criteria - Each layer must pass to proceed
async def example_layered_criteria() -> None:
    """
    Demonstrate LAYERED criteria where each level filters the next.

    Layer 1: Basic validation
    Layer 2: Business rules
    Layer 3: Security checks
    Layer 4: Approval (if needed)
    """
    print("\n" + "=" * 70)
    print("Example 8: LAYERED Criteria (Progressive Filtering)")
    print("=" * 70)

    def meets_business_rules(operation: str, data_classification: str) -> bool:
        """Layer 2: Business logic validation."""
        # Can't delete production data without proper classification
        if operation == "delete" and data_classification != "approved_for_deletion":
            return False
        return True

    def passes_security_scan(operation: str, user_clearance: str) -> bool:
        """Layer 3: Security validation."""
        security_levels = {
            "read": 1,
            "write": 2,
            "delete": 3,
        }
        clearance_levels = {
            "basic": 1,
            "elevated": 2,
            "admin": 3,
        }
        return clearance_levels.get(user_clearance, 0) >= security_levels.get(operation, 99)

    @govern(
        policies=[
            # LAYER 1: Input validation (must pass to continue)
            ValidationPolicy(
                name="InputValidation",
                input_validator=lambda x: all(
                    k in x.get("kwargs", {})
                    for k in ["operation", "dataset", "data_classification", "user_clearance"]
                )
            ),
            # LAYER 2: Business rules (must pass to continue)
            ValidationPolicy(
                name="BusinessRules",
                input_validator=lambda x: meets_business_rules(
                    x.get("kwargs", {}).get("operation", ""),
                    x.get("kwargs", {}).get("data_classification", "")
                )
            ),
            # LAYER 3: Security check (must pass to continue)
            ValidationPolicy(
                name="SecurityCheck",
                input_validator=lambda x: passes_security_scan(
                    x.get("kwargs", {}).get("operation", ""),
                    x.get("kwargs", {}).get("user_clearance", "")
                )
            ),
            # LAYER 4: Approval (required for delete operations)
            ApprovalPolicy(
                name="DeletionApproval",
                approvers=["data-governance@company.com"],
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("operation", "") != "delete"
            ),
            # ALWAYS: Audit everything
            AuditPolicy(compliance_tags=["data_governance"]),
        ]
    )
    async def data_operation(
        operation: str,
        dataset: str,
        data_classification: str,
        user_clearance: str
    ) -> dict:
        """
        Data operation with layered governance.

        Each layer must pass:
        1. Valid inputs
        2. Business rules
        3. Security clearance
        4. Approval (for deletes)
        5. Audit trail
        """
        print(f"🔐 {operation.upper()} on {dataset} (classification: {data_classification}, clearance: {user_clearance})")
        return {
            "operation": operation,
            "dataset": dataset,
            "status": "completed",
            "governance_layers_passed": 4 if operation != "delete" else 5
        }

    print("\n1. Read operation - passes all layers:")
    result = await data_operation("read", "customer_data", "standard", "basic")
    print(f"   ✓ {result}")

    print("\n2. Write operation with elevated clearance - passes all layers:")
    result = await data_operation("write", "analytics_data", "standard", "elevated")
    print(f"   ✓ {result}")

    # Delete would require passing all layers + approval (commented for demo)
    # print("\n3. Delete operation - must pass ALL layers + approval:")
    # result = await data_operation("delete", "temp_data", "approved_for_deletion", "admin")
    # print(f"   ✓ {result}")


# Example 9: Composite Criteria - Multiple independent checks
async def example_composite_criteria() -> None:
    """
    Demonstrate COMPOSITE criteria where multiple independent checks all run.

    All checks are independent but ALL must pass.
    """
    print("\n" + "=" * 70)
    print("Example 9: COMPOSITE Criteria (Multiple Independent Checks)")
    print("=" * 70)

    @govern(
        policies=[
            # CHECK 1: Input format validation
            ValidationPolicy(
                name="FormatValidation",
                input_validator=lambda x: isinstance(
                    x.get("kwargs", {}).get("config", {}), dict
                )
            ),
            # CHECK 2: Resource quota check
            ValidationPolicy(
                name="QuotaCheck",
                input_validator=lambda x:
                    x.get("kwargs", {}).get("cpu_cores", 0) <= 16 and
                    x.get("kwargs", {}).get("memory_gb", 0) <= 64
            ),
            # CHECK 3: Cost limit check
            ValidationPolicy(
                name="CostCheck",
                input_validator=lambda x:
                    x.get("kwargs", {}).get("estimated_cost", 0) <= 5000
            ),
            # CHECK 4: Region compliance
            ValidationPolicy(
                name="RegionCompliance",
                input_validator=lambda x:
                    x.get("kwargs", {}).get("region", "") in ["us-east-1", "us-west-2", "eu-west-1"]
            ),
            # CHECK 5: Rate limiting
            RateLimitPolicy(max_calls=10, window_seconds=3600),
            # CHECK 6: Audit trail
            AuditPolicy(compliance_tags=["resource_provisioning", "cost_control"]),
            # CHECK 7: Approval for production
            ApprovalPolicy(
                approvers=["infra-lead@company.com"],
                auto_approve_condition=lambda inputs:
                    inputs.get("kwargs", {}).get("environment", "") != "production"
            ),
        ]
    )
    async def provision_cluster(
        environment: str,
        region: str,
        cpu_cores: int,
        memory_gb: int,
        estimated_cost: float,
        _config: dict
    ) -> dict:
        """
        Provision cluster - ALL checks must pass:
        1. Config is valid dict
        2. Resources within quota (CPU ≤ 16, RAM ≤ 64GB)
        3. Cost ≤ $5000
        4. Approved region
        5. Rate limit not exceeded
        6. Audit trail created
        7. Approval if production
        """
        print(
            f"☁️  Provisioning {cpu_cores} cores, {memory_gb}GB RAM in {region} "
            f"({environment}, ${estimated_cost})"
        )
        return {
            "cluster_id": "CLUSTER-789",
            "environment": environment,
            "region": region,
            "cost": estimated_cost,
            "status": "provisioned",
            "checks_passed": 7
        }

    print("\n1. Development cluster - all checks pass:")
    result = await provision_cluster(
        environment="development",
        region="us-east-1",
        cpu_cores=8,
        memory_gb=32,
        estimated_cost=1200,
        config={"tier": "dev"}
    )
    print(f"   ✓ {result}")

    print("\n2. Staging cluster - all checks pass:")
    result = await provision_cluster(
        environment="staging",
        region="us-west-2",
        cpu_cores=12,
        memory_gb=48,
        estimated_cost=2500,
        config={"tier": "staging"}
    )
    print(f"   ✓ {result}")

    # Production would require all checks + approval (commented for demo)
    # print("\n3. Production cluster - ALL checks + approval required:")
    # result = await provision_cluster(
    #     environment="production",
    #     region="eu-west-1",
    #     cpu_cores=16,
    #     memory_gb=64,
    #     estimated_cost=4800,
    #     config={"tier": "production", "ha": True}
    # )
    # print(f"   ✓ {result}")


async def main() -> None:
    """Run all criteria-based governance examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "CRITERIA-BASED GOVERNANCE EXAMPLES" + " " * 19 + "║")
    print("╚" + "═" * 68 + "╝")

    await example_threshold_based_approval()
    await example_environment_based()
    await example_risk_based()
    await example_time_based()
    await example_multi_criteria()
    await example_dynamic_policies()

    print("\n" + "━" * 70)
    print("🎯 ADDITIVE & COMPOSITE CRITERIA EXAMPLES")
    print("━" * 70)

    await example_additive_criteria()
    await example_layered_criteria()
    await example_composite_criteria()

    print("\n" + "=" * 70)
    print("✓ All criteria-based governance examples completed!")
    print("  - 6 conditional criteria patterns")
    print("  - 3 additive/composite patterns")
    print("  - Total: 9 comprehensive examples")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
