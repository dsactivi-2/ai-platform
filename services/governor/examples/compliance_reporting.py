"""Comprehensive compliance and reporting examples for GDPR and SOC 2."""

import asyncio
from datetime import datetime, timedelta, timezone

from governor import (
    govern,
    ValidationPolicy,
    AuthorizationPolicy,
    RateLimitPolicy,
    AuditPolicy,
    ApprovalPolicy,
)
from governor.compliance.reporter import ComplianceReporter
from governor.compliance.gdpr import GDPRCompliance
from governor.compliance.soc2 import SOC2Compliance
from governor.storage.memory import InMemoryStorage


# Shared storage for all examples
storage = InMemoryStorage()


async def example_gdpr_compliant_operations() -> None:
    """
    Demonstrate GDPR-compliant data processing with full audit trail.
    """
    print("=" * 70)
    print("Example 1: GDPR-Compliant User Data Processing")
    print("=" * 70)

    @govern(
        policies=[
            # Input validation
            ValidationPolicy(
                input_validator=lambda x: all(
                    k in x.get("kwargs", {}) for k in ["user_id", "data"]
                )
            ),
            # Sensitive data logging with redaction
            AuditPolicy(
                log_inputs=True,
                log_outputs=True,
                sensitive_fields=["email", "ssn", "credit_card"],
                compliance_tags=["GDPR", "personal_data"],
            ),
        ],
        storage=storage,
        context={"user": {"id": "user123", "email": "user@example.com"}},
    )
    async def process_user_data(user_id: str, data: dict) -> dict:
        """Process user data with GDPR compliance."""
        print(f"  Processing data for user: {user_id}")
        return {
            "user_id": user_id,
            "processed": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Process some user data
    print("\n1. Processing user data:")
    result = await process_user_data("user123", {"name": "John", "age": 30})
    print(f"   ✓ {result}")

    result = await process_user_data("user456", {"name": "Jane", "age": 25})
    print(f"   ✓ {result}")

    # Demonstrate GDPR rights
    print("\n2. GDPR Data Subject Rights:")
    gdpr = GDPRCompliance(storage)

    # Right to access
    print("\n   a) Right to Access (Article 15):")
    access_data = await gdpr.right_to_access("user123")
    print(f"      User has {access_data['executions']['total_count']} executions")
    print(f"      User has {access_data['events']['total_count']} events")

    # Right to data portability
    print("\n   b) Right to Data Portability (Article 20):")
    portable_data = await gdpr.right_to_data_portability("user123")
    print(f"      Exported {len(portable_data)} bytes of data in JSON format")

    # Right to erasure
    print("\n   c) Right to Erasure (Article 17):")
    erasure_result = await gdpr.right_to_erasure("user123", reason="User request")
    print(f"      Status: {erasure_result['status']}")
    print(f"      Deleted: {erasure_result['deleted_count']}")


async def example_soc2_compliant_operations() -> None:
    """
    Demonstrate SOC 2 compliant operations with all Trust Service Criteria.
    """
    print("\n" + "=" * 70)
    print("Example 2: SOC 2 Compliant Operations")
    print("=" * 70)

    @govern(
        policies=[
            # Security: Authorization required
            AuthorizationPolicy(
                required_roles={"admin", "operator"},
            ),
            # Availability: Rate limiting
            RateLimitPolicy(max_calls=100, window_seconds=60),
            # Processing Integrity: Input validation
            ValidationPolicy(
                input_validator=lambda x: x.get("kwargs", {}).get("amount", 0) > 0
            ),
            # Confidentiality: Audit logging
            AuditPolicy(
                compliance_tags=["SOC2", "financial"],
                sensitive_fields=["account_number"],
            ),
            # Privacy: Approval for sensitive operations
            ApprovalPolicy(
                approvers=["compliance@company.com"],
                auto_approve_condition=lambda x: x.get("kwargs", {}).get("amount", 0) < 10000,
            ),
        ],
        storage=storage,
        context={"user": {"id": "admin1", "roles": ["admin"], "email": "admin@company.com"}},
    )
    async def process_transaction(
        amount: float, account_number: str, description: str
    ) -> dict:
        """Process financial transaction with SOC 2 compliance."""
        print(f"  Processing ${amount} transaction")
        return {
            "transaction_id": "TXN123",
            "amount": amount,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    # Process transactions
    print("\n1. Processing transactions with full SOC 2 controls:")
    result = await process_transaction(5000, "ACC-123", "Payment")
    print(f"   ✓ Transaction 1: {result['transaction_id']}")

    result = await process_transaction(7500, "ACC-456", "Invoice")
    print(f"   ✓ Transaction 2: {result['transaction_id']}")

    # Generate SOC 2 reports
    print("\n2. SOC 2 Trust Service Criteria Reports:")
    soc2 = SOC2Compliance(storage)

    # Security report
    print("\n   a) Security Controls:")
    security_report = await soc2.security_controls_report(period_days=30)
    print(f"      Access control enabled: {security_report['controls']['access_controls_enabled']}")
    print(f"      Authorization success rate: {security_report['metrics']['authorization_success_rate']:.2f}%")

    # Availability report
    print("\n   b) Availability:")
    availability_report = await soc2.availability_report(period_days=30)
    print(f"      Uptime: {availability_report['metrics']['uptime_percentage']:.2f}%")
    print(f"      SLA Met: {availability_report['sla_compliance']['sla_met']}")

    # Processing Integrity report
    print("\n   c) Processing Integrity:")
    integrity_report = await soc2.processing_integrity_report(period_days=30)
    print(f"      Validation enabled: {integrity_report['controls']['input_validation_enabled']}")
    print(f"      Data quality score: {integrity_report['metrics']['data_quality_score']:.2f}%")


async def example_comprehensive_compliance_reporting() -> None:
    """
    Generate comprehensive compliance reports for auditors.
    """
    print("\n" + "=" * 70)
    print("Example 3: Comprehensive Compliance Reporting")
    print("=" * 70)

    reporter = ComplianceReporter(storage)

    # Generate reports for last 30 days
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(days=30)

    print("\n1. General Compliance Report (Last 30 Days):")
    general_report = await reporter.generate_report(
        report_type="custom",
        period_start=period_start,
        period_end=now,
    )

    summary = await reporter.export_report_summary(general_report)
    print(summary)

    print("\n2. GDPR-Specific Report:")
    gdpr_report = await reporter.generate_gdpr_report(period_start, now)
    print(f"   Report ID: {gdpr_report.report_id}")
    print(f"   Total Executions: {gdpr_report.total_executions}")
    print(f"   Policy Violations: {gdpr_report.policy_violations}")
    print(f"   Audit Trail Complete: {'✓ Yes' if gdpr_report.audit_trail_complete else '✗ No'}")
    print(f"   GDPR Metadata: {gdpr_report.metadata.get('gdpr', {})}")

    print("\n3. SOC 2 Comprehensive Report:")
    soc2 = SOC2Compliance(storage)
    soc2_comprehensive = await soc2.generate_comprehensive_soc2_report(period_days=30)

    print(f"   Report Type: {soc2_comprehensive['report_type']}")
    print(f"   Report ID: {soc2_comprehensive['report_id']}")
    print("\n   Trust Service Criteria Compliance:")
    compliance = soc2_comprehensive['overall_compliance']
    print(f"      Security: {'✓' if compliance['security_compliant'] else '✗'}")
    print(f"      Availability: {'✓' if compliance['availability_compliant'] else '✗'}")
    print(f"      Processing Integrity: {'✓' if compliance['processing_integrity_compliant'] else '✗'}")
    print(f"      Confidentiality: {'✓' if compliance['confidentiality_compliant'] else '✗'}")
    print(f"      Privacy: {'✓' if compliance['privacy_compliant'] else '✗'}")

    print("\n4. Export Reports for Auditors:")
    # Export as JSON
    json_export = await reporter.export_report_json(general_report)
    print(f"   JSON Export: {len(json_export)} bytes")

    # Export SOC 2 evidence
    soc2_evidence = soc2.export_soc2_evidence(soc2_comprehensive)
    print(f"   SOC 2 Evidence: {len(soc2_evidence)} bytes")


async def example_privacy_and_consent() -> None:
    """
    Demonstrate privacy notice and consent management.
    """
    print("\n" + "=" * 70)
    print("Example 4: Privacy Notice and Consent Management")
    print("=" * 70)

    gdpr = GDPRCompliance(storage)

    print("\n1. GDPR Consent Policy:")
    consent_policy = gdpr.get_consent_policy(
        purpose="AI agent governance and monitoring",
        data_categories=["execution_logs", "user_actions", "timestamps"],
        retention_period_days=365,
    )
    print(f"   Consent ID: {consent_policy['consent_id']}")
    print(f"   Purpose: {consent_policy['purpose']}")
    print(f"   Data Categories: {', '.join(consent_policy['data_categories'])}")
    print(f"   Retention: {consent_policy['retention_period_days']} days")
    print(f"   Rights: {len(consent_policy['data_subject_rights'])} rights guaranteed")

    print("\n2. Privacy Notice:")
    privacy_notice = gdpr.create_privacy_notice(
        data_controller="Example Corp",
        purposes=[
            "AI agent monitoring and governance",
            "Security and compliance",
            "Performance optimization",
        ],
        data_categories=[
            "User identifiers",
            "Execution metadata",
            "Timestamps",
            "Function names",
        ],
        recipients=["Internal teams", "Cloud storage provider"],
        retention_period="365 days",
    )
    print(privacy_notice)

    print("\n3. Data Breach Logging (if needed):")
    # This is just an example - no actual breach
    print("   (Example only - no actual breach detected)")
    # breach = await gdpr.log_data_breach(
    #     breach_type="unauthorized_access",
    #     affected_users=["user123", "user456"],
    #     description="Example breach for documentation purposes",
    #     severity="high"
    # )


async def main() -> None:
    """Run all compliance and reporting examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "COMPLIANCE & REPORTING EXAMPLES" + " " * 22 + "║")
    print("╚" + "═" * 68 + "╝")

    await example_gdpr_compliant_operations()
    await example_soc2_compliant_operations()
    await example_comprehensive_compliance_reporting()
    await example_privacy_and_consent()

    print("\n" + "=" * 70)
    print("✓ All compliance and reporting examples completed!")
    print("\nKey Features Demonstrated:")
    print("  • GDPR compliance (Articles 15, 17, 20)")
    print("  • SOC 2 Trust Service Criteria (all 5)")
    print("  • Comprehensive audit trails")
    print("  • Sensitive data redaction")
    print("  • Privacy notices and consent")
    print("  • Compliance reporting for auditors")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
