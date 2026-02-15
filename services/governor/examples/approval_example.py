"""Human-in-the-loop approval example."""

import asyncio
from governor import govern, ApprovalPolicy
from governor.approval.handlers import CLIApprovalHandler


# Example 1: Simple approval with CLI
async def main_cli() -> None:
    """Example with CLI approval."""
    # Set up CLI approval handler
    handler = CLIApprovalHandler()

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["admin@company.com"],
                timeout_seconds=300,  # 5 minutes
            )
        ],
        approval_handler=handler,
    )
    async def critical_operation(data: dict) -> dict:
        """Operation that requires approval."""
        print(f"Executing critical operation with: {data}")
        return {"status": "completed", "data": data}

    print("=" * 70)
    print("Human-in-the-Loop Approval Example (CLI)")
    print("=" * 70)

    try:
        result = await critical_operation({"action": "delete_database", "confirm": True})
        print(f"\nOperation completed: {result}")
    except PermissionError as e:
        print(f"\nOperation rejected: {e}")


# Example 2: Approval with custom callback
async def slack_approval_callback(
    execution_id: str, function_name: str, inputs: dict, approvers: list
) -> tuple[bool, str, str]:
    """
    Simulate Slack approval notification.

    In reality, this would send a Slack message and wait for response.
    For demo, we'll auto-approve after a delay.
    """
    print(f"\n📱 Slack notification sent to: {', '.join(approvers)}")
    print(f"   Function: {function_name}")
    print(f"   Execution ID: {execution_id}")
    print(f"   Inputs: {inputs}")

    # Simulate waiting for Slack response
    await asyncio.sleep(1)

    # Simulate approval from Slack
    return (True, "john@company.com", "Approved via Slack")


async def main_callback() -> None:
    """Example with custom callback."""
    from governor.approval.handlers import CallbackApprovalHandler

    handler = CallbackApprovalHandler(callback=slack_approval_callback)

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["john@company.com", "jane@company.com"],
                timeout_seconds=300,
            )
        ],
        approval_handler=handler,
    )
    async def deploy_model(model_name: str, environment: str) -> dict:
        """Deploy ML model to production."""
        print(f"\n🚀 Deploying {model_name} to {environment}")
        return {"deployed": True, "model": model_name, "env": environment}

    print("\n" + "=" * 70)
    print("Human-in-the-Loop Approval Example (Custom Callback)")
    print("=" * 70)

    try:
        result = await deploy_model("gpt-agent-v2", "production")
        print(f"\nDeployment result: {result}")
    except PermissionError as e:
        print(f"\nDeployment rejected: {e}")


# Example 3: Auto-approve condition
async def main_auto_approve() -> None:
    """Example with conditional auto-approval."""

    @govern(
        policies=[
            ApprovalPolicy(
                approvers=["admin@company.com"],
                # Auto-approve if amount is less than $100
                auto_approve_condition=lambda inputs: inputs.get("kwargs", {}).get(
                    "amount", float("inf")
                )
                < 100,
            )
        ]
    )
    async def transfer_funds(amount: float, to_account: str) -> dict:
        """Transfer funds with approval for large amounts."""
        print(f"💸 Transferring ${amount} to {to_account}")
        return {"transferred": True, "amount": amount, "to": to_account}

    print("\n" + "=" * 70)
    print("Auto-Approval Example")
    print("=" * 70)

    # Small amount - auto-approved
    print("\n1. Small transfer (auto-approved):")
    result = await transfer_funds(50.0, "ACC123")
    print(f"   Result: {result}")

    # Large amount - would require approval (commented out for demo)
    # print("\n2. Large transfer (requires approval):")
    # result = await transfer_funds(5000.0, "ACC456")
    # print(f"   Result: {result}")


async def main() -> None:
    """Run all examples."""
    # Example 1: CLI (interactive - commented out for non-interactive demo)
    # await main_cli()

    # Example 2: Custom callback
    await main_callback()

    # Example 3: Auto-approve
    await main_auto_approve()

    print("\n" + "=" * 70)


if __name__ == "__main__":
    # Note: CLI example requires interactive terminal
    # Uncomment main_cli() in main() to test interactively
    asyncio.run(main())
