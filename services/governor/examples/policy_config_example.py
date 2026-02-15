"""Examples of using policy configuration files (JSON/YAML)."""

import asyncio
from pathlib import Path

from governor import govern
from governor.config import load_policies_from_file, load_policies_from_dict


# Example 1: Load policies from YAML file
async def example_yaml_config() -> None:
    """Load governance policies from YAML configuration."""
    print("=" * 70)
    print("Example 1: Load Policies from YAML File")
    print("=" * 70)

    # Load policies from YAML
    policies_dir = Path(__file__).parent / "policies"
    yaml_file = policies_dir / "governance.yaml"

    print(f"\nLoading policies from: {yaml_file}")
    policies = load_policies_from_file(yaml_file)

    print(f"Loaded {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy.name} ({policy.get_policy_type()})")

    # Use policies in governance
    @govern(policies=policies, context={"user": {"id": "user123", "roles": ["admin"]}})
    async def process_payment(amount: float, account: str) -> dict:
        """Process payment with policies from YAML config."""
        print(f"\n  Processing ${amount} payment to {account}")
        return {"transaction_id": "TXN123", "amount": amount, "status": "completed"}

    print("\nExecuting governed function:")
    result = await process_payment(1000.0, "ACC-123")
    print(f"✓ Result: {result}")


# Example 2: Load policies from JSON file
async def example_json_config() -> None:
    """Load governance policies from JSON configuration."""
    print("\n" + "=" * 70)
    print("Example 2: Load Policies from JSON File")
    print("=" * 70)

    # Load policies from JSON
    policies_dir = Path(__file__).parent / "policies"
    json_file = policies_dir / "governance.json"

    print(f"\nLoading policies from: {json_file}")
    policies = load_policies_from_file(json_file)

    print(f"Loaded {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy.name} ({policy.get_policy_type()})")

    # Use policies
    @govern(policies=policies, context={"user": {"id": "admin1", "roles": ["admin"]}})
    async def deploy_service(service: str, version: str) -> dict:
        """Deploy service with policies from JSON config."""
        print(f"\n  Deploying {service} version {version}")
        return {"deployed": True, "service": service, "version": version}

    print("\nExecuting governed function:")
    result = await deploy_service("api-gateway", "2.1.0")
    print(f"✓ Result: {result}")


# Example 3: Environment-specific policies
async def example_environment_policies() -> None:
    """Load different policies based on environment."""
    print("\n" + "=" * 70)
    print("Example 3: Environment-Specific Policy Loading")
    print("=" * 70)

    import os

    # Simulate different environments
    environments = ["development", "production"]

    for env in environments:
        print(f"\n--- {env.upper()} Environment ---")

        # Load environment-specific policies
        policies_dir = Path(__file__).parent / "policies"
        config_file = policies_dir / f"{env}.yaml"

        if config_file.exists():
            policies = load_policies_from_file(config_file)
            print(f"Loaded {len(policies)} policies for {env}:")
            for policy in policies:
                print(f"  - {policy.name}")

            # Apply to function
            @govern(policies=policies)
            async def env_specific_operation(data: dict) -> dict:
                return {"env": env, "processed": True}

            result = await env_specific_operation({"key": "value"})
            print(f"✓ Executed with {env} policies: {result}")
        else:
            print(f"⚠️  No config file for {env}")


# Example 4: Load from dictionary (dynamic configuration)
async def example_dict_config() -> None:
    """Load policies from a dictionary (e.g., from database or API)."""
    print("\n" + "=" * 70)
    print("Example 4: Load Policies from Dictionary")
    print("=" * 70)

    # Could come from database, API, environment variables, etc.
    config = {
        "policies": [
            {
                "type": "validation",
                "name": "DynamicValidation",
                "enabled": True,
                "phase": "pre_execution",
                "strict": True,
            },
            {
                "type": "rate_limit",
                "name": "DynamicRateLimit",
                "enabled": True,
                "max_calls": 50,
                "window_seconds": 60,
                "per_user": True,
            },
            {
                "type": "audit",
                "name": "DynamicAudit",
                "enabled": True,
                "log_inputs": True,
                "log_outputs": True,
                "compliance_tags": ["dynamic", "runtime"],
            },
        ]
    }

    print("\nLoading policies from dictionary:")
    policies = load_policies_from_dict(config)

    print(f"Loaded {len(policies)} policies:")
    for policy in policies:
        print(f"  - {policy.name} ({policy.get_policy_type()})")

    @govern(policies=policies)
    async def dynamic_operation(value: int) -> int:
        """Operation with dynamically loaded policies."""
        print(f"\n  Processing value: {value}")
        return value * 2

    print("\nExecuting governed function:")
    result = await dynamic_operation(42)
    print(f"✓ Result: {result}")


# Example 5: Industry-specific policies
async def example_industry_policies() -> None:
    """Load industry-specific compliance policies."""
    print("\n" + "=" * 70)
    print("Example 5: Financial Services Compliance Policies")
    print("=" * 70)

    # Load financial services policies
    policies_dir = Path(__file__).parent / "policies"
    financial_config = policies_dir / "financial-services.yaml"

    if financial_config.exists():
        print(f"\nLoading financial services policies from: {financial_config}")
        policies = load_policies_from_file(financial_config)

        print(f"Loaded {len(policies)} financial compliance policies:")
        for policy in policies:
            print(f"  - {policy.name} ({policy.get_policy_type()})")

        # Apply to financial transaction
        @govern(
            policies=policies,
            context={
                "user": {
                    "id": "trader123",
                    "roles": ["finance", "compliance"],
                    "permissions": ["transaction.execute", "financial.write"],
                }
            },
        )
        async def execute_trade(
            symbol: str, quantity: int, price: float, account_number: str
        ) -> dict:
            """Execute financial trade with full compliance governance."""
            total_value = quantity * price
            print(f"\n  Executing trade: {quantity} shares of {symbol} @ ${price}")
            print(f"  Total value: ${total_value}")
            return {
                "trade_id": "TRADE-789",
                "symbol": symbol,
                "quantity": quantity,
                "price": price,
                "total_value": total_value,
                "status": "executed",
            }

        print("\nExecuting governed financial transaction:")
        result = await execute_trade("AAPL", 100, 150.0, "ACC-456-789")
        print(f"✓ Trade Result: {result}")
    else:
        print(f"⚠️  Financial services config not found: {financial_config}")


# Example 6: Combining file config with code-based policies
async def example_hybrid_config() -> None:
    """Combine policies from config file with code-based policies."""
    print("\n" + "=" * 70)
    print("Example 6: Hybrid Configuration (File + Code)")
    print("=" * 70)

    from governor import ValidationPolicy

    # Load base policies from file
    policies_dir = Path(__file__).parent / "policies"
    config_file = policies_dir / "governance.yaml"

    if config_file.exists():
        base_policies = load_policies_from_file(config_file)
        print(f"\nLoaded {len(base_policies)} policies from config file")

        # Add custom policy in code
        custom_policy = ValidationPolicy(
            name="CustomCodePolicy",
            input_validator=lambda x: x.get("kwargs", {}).get("value", 0) > 0,
        )

        # Combine
        all_policies = base_policies + [custom_policy]
        print(f"Total policies (file + code): {len(all_policies)}")

        @govern(policies=all_policies)
        async def hybrid_operation(value: int) -> int:
            """Operation with hybrid policy configuration."""
            return value + 100

        print("\nExecuting with hybrid policies:")
        result = await hybrid_operation(42)
        print(f"✓ Result: {result}")


async def main() -> None:
    """Run all policy configuration examples."""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "POLICY CONFIGURATION EXAMPLES" + " " * 24 + "║")
    print("╚" + "═" * 68 + "╝")

    await example_yaml_config()
    await example_json_config()
    await example_environment_policies()
    await example_dict_config()
    await example_industry_policies()
    await example_hybrid_config()

    print("\n" + "=" * 70)
    print("✓ All policy configuration examples completed!")
    print("\nKey Features Demonstrated:")
    print("  • Load policies from YAML files")
    print("  • Load policies from JSON files")
    print("  • Environment-specific configurations")
    print("  • Dynamic policy loading from dictionaries")
    print("  • Industry-specific compliance policies")
    print("  • Hybrid configuration (file + code)")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
