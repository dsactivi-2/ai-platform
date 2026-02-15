"""End-to-end integration tests for the full agent lifecycle including chat.

These tests validate:
1. Agent creation (get command)
2. Agent update (set command)
3. Agent listing (ls command)
4. Chat API functionality (non-interactive mode)
5. API response accuracy

To run:
1. Create .env in project root with LYZR_API_KEY, LYZR_USER_ID, LYZR_MEMBERSTACK_TOKEN
2. Run: uv run pytest tests/integration/test_e2e_chat.py -v -s
"""

import shutil
import uuid
from pathlib import Path

import httpx
import pytest
from typer.testing import CliRunner

from lyzr_kit.main import app
from lyzr_kit.storage.manager import StorageManager
from lyzr_kit.utils.auth import load_auth

runner = CliRunner()

# Path to root .env file (gitignored, contains real credentials)
ROOT_DIR = Path(__file__).parent.parent.parent
ROOT_ENV_FILE = ROOT_DIR / ".env"

# Chat API endpoints
CHAT_API_ENDPOINT = "https://agent-prod.studio.lyzr.ai/v3/inference/chat/"
STREAM_API_ENDPOINT = "https://agent-prod.studio.lyzr.ai/v3/inference/stream/"


def _has_valid_credentials() -> bool:
    """Check if root .env has valid LYZR credentials."""
    if not ROOT_ENV_FILE.exists():
        return False
    content = ROOT_ENV_FILE.read_text()
    has_api_key = "LYZR_API_KEY=" in content
    is_placeholder = "test-placeholder" in content or "your-api-key" in content
    return has_api_key and not is_placeholder


# Skip all tests if no valid credentials in root .env
pytestmark = pytest.mark.skipif(
    not _has_valid_credentials(),
    reason="No valid .env file with LYZR credentials in project root. "
    "Create .env with LYZR_API_KEY to run integration tests.",
)


@pytest.fixture(autouse=True)
def clean_agents_dir():
    """Clean agents directory before and after each test."""
    agents_dir = Path.cwd() / "agents"
    if agents_dir.exists():
        shutil.rmtree(agents_dir)
    yield
    if agents_dir.exists():
        shutil.rmtree(agents_dir)


class TestE2EAgentLifecycle:
    """End-to-end tests for the complete agent lifecycle."""

    def test_agent_create_and_chat_lifecycle(self):
        """Test complete lifecycle: create agent -> verify -> chat -> verify response."""
        agent_id = f"e2e-test-{uuid.uuid4().hex[:8]}"

        # Step 1: Create agent from built-in template
        print(f"\n=== Step 1: Create agent '{agent_id}' ===")
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        print(get_result.output)

        assert get_result.exit_code == 0, f"Agent creation failed: {get_result.output}"
        assert "created successfully" in get_result.output
        assert "Agent ID:" in get_result.output
        assert "Platform URL:" in get_result.output
        assert "API Endpoint:" in get_result.output

        # Step 2: Verify local file structure
        print("\n=== Step 2: Verify local file structure ===")
        local_file = Path.cwd() / "agents" / f"{agent_id}.yaml"
        assert local_file.exists(), f"Local file not created: {local_file}"

        content = local_file.read_text()
        assert "platform_agent_id:" in content
        assert "platform_env_id:" in content
        assert "endpoint:" in content
        assert "is_active: true" in content
        print(f"Local file verified: {local_file}")

        # Step 3: Verify agent appears in list
        print("\n=== Step 3: Verify agent in list ===")
        ls_result = runner.invoke(app, ["agent", "ls"])
        print(ls_result.output)

        assert ls_result.exit_code == 0
        assert agent_id in ls_result.output
        assert "Your Agents" in ls_result.output  # Separate table for local agents
        # Endpoint URL may be truncated in table output
        assert "agent-prod.studio" in ls_result.output or "agent-prod" in ls_result.output

        # Step 4: Load agent and extract platform_agent_id for chat
        print("\n=== Step 4: Extract platform agent ID for chat ===")
        storage = StorageManager()
        agent = storage.get_agent(agent_id)
        assert agent is not None
        assert agent.platform_agent_id is not None
        platform_agent_id = agent.platform_agent_id
        print(f"Platform Agent ID: {platform_agent_id}")

        # Step 5: Test chat API directly (non-interactive)
        print("\n=== Step 5: Test Chat API ===")
        auth = load_auth()

        chat_result = _send_chat_message(
            api_key=auth.api_key,
            agent_id=platform_agent_id,
            message="Hello, please respond with just the word 'Hello' back.",
        )

        print(f"Chat API Response: {chat_result}")
        assert chat_result["success"], f"Chat API failed: {chat_result.get('error')}"
        assert chat_result["response"] is not None
        assert len(chat_result["response"]) > 0
        print(f"Agent response: {chat_result['response'][:200]}...")

        print("\n=== E2E Lifecycle Test Completed Successfully! ===")

    def test_agent_modify_and_update_lifecycle(self):
        """Test modify and update lifecycle: create -> modify -> set -> verify."""
        # Use shorter ID to avoid truncation in table output
        agent_id = f"mod-{uuid.uuid4().hex[:6]}"

        # Step 1: Create agent
        print(f"\n=== Step 1: Create agent '{agent_id}' ===")
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert get_result.exit_code == 0
        print("Agent created successfully")

        # Step 2: Modify local file
        print("\n=== Step 2: Modify agent config ===")
        local_file = Path.cwd() / "agents" / f"{agent_id}.yaml"
        content = local_file.read_text()

        # Update temperature
        original_temp = "temperature: 0.7"
        new_temp = "temperature: 0.5"
        if original_temp in content:
            updated_content = content.replace(original_temp, new_temp)
            local_file.write_text(updated_content)
            print("Updated temperature from 0.7 to 0.5")
        else:
            print("Original temperature not found, skipping modification")

        # Step 3: Update on platform
        print("\n=== Step 3: Update on platform ===")
        set_result = runner.invoke(app, ["agent", "set", agent_id])
        print(set_result.output)

        assert set_result.exit_code == 0
        assert "updated successfully" in set_result.output

        # Step 4: Verify agent still in list with endpoint
        print("\n=== Step 4: Verify agent still in list ===")
        ls_result = runner.invoke(app, ["agent", "ls"])
        # Check that agent ID appears (may be truncated in table)
        assert agent_id in ls_result.output or agent_id[:10] in ls_result.output
        assert "Your Agents" in ls_result.output  # Separate table for local agents
        # Endpoint URL may be truncated in table output
        assert "agent-prod.studio" in ls_result.output or "agent-prod" in ls_result.output

        print("\n=== Modify/Update Lifecycle Test Completed Successfully! ===")


class TestChatAPIDirectly:
    """Direct tests for the chat API to validate responses."""

    def test_chat_api_basic_response(self):
        """Test that chat API returns a valid response."""
        agent_id = f"chat-api-test-{uuid.uuid4().hex[:8]}"

        # Create agent
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert get_result.exit_code == 0

        # Get platform agent ID
        storage = StorageManager()
        agent = storage.get_agent(agent_id)
        auth = load_auth()

        # Test chat
        result = _send_chat_message(
            api_key=auth.api_key,
            agent_id=agent.platform_agent_id,
            message="What is 2 + 2?",
        )

        print(f"\nChat Response: {result}")
        assert result["success"], f"Chat failed: {result.get('error')}"
        assert result["response"] is not None
        # The response should mention "4" somewhere
        assert "4" in result["response"], f"Expected '4' in response: {result['response']}"

    def test_chat_api_session_continuity(self):
        """Test that chat maintains session context."""
        agent_id = f"session-test-{uuid.uuid4().hex[:8]}"

        # Create agent
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert get_result.exit_code == 0

        # Get platform agent ID
        storage = StorageManager()
        agent = storage.get_agent(agent_id)
        auth = load_auth()

        # Use same session ID for multiple messages
        session_id = str(uuid.uuid4())

        # First message - introduce a fact
        result1 = _send_chat_message(
            api_key=auth.api_key,
            agent_id=agent.platform_agent_id,
            message="Remember this number: 42. Just acknowledge with OK.",
            session_id=session_id,
        )
        print(f"\nFirst response: {result1.get('response', '')[:100]}")
        assert result1["success"]

        # Second message - ask about the fact
        result2 = _send_chat_message(
            api_key=auth.api_key,
            agent_id=agent.platform_agent_id,
            message="What number did I ask you to remember?",
            session_id=session_id,
        )
        print(f"Second response: {result2.get('response', '')[:100]}")
        assert result2["success"]
        # The response should mention 42
        assert "42" in result2["response"], f"Session context not maintained: {result2['response']}"

    def test_streaming_api_response(self):
        """Test that streaming API returns valid SSE events."""
        agent_id = f"stream-test-{uuid.uuid4().hex[:8]}"

        # Create agent
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert get_result.exit_code == 0

        # Get platform agent ID
        storage = StorageManager()
        agent = storage.get_agent(agent_id)
        auth = load_auth()

        # Test streaming endpoint
        result = _send_streaming_message(
            api_key=auth.api_key,
            agent_id=agent.platform_agent_id,
            message="Say hello in one word.",
        )

        print(f"\nStreaming Result: {result}")
        assert result["success"], f"Streaming failed: {result.get('error')}"
        assert result["chunks_received"] > 0, "No chunks received from stream"
        assert result["final_content"] is not None
        print(f"Received {result['chunks_received']} chunks")
        print(f"Final content: {result['final_content'][:200]}")


class TestErrorHandling:
    """Tests for error handling scenarios."""

    def test_chat_with_nonexistent_agent(self):
        """Test chat command fails gracefully for non-existent agent."""
        result = runner.invoke(app, ["agent", "chat", "nonexistent-agent-id"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_set_without_get(self):
        """Test set command fails when agent not in agents/."""
        result = runner.invoke(app, ["agent", "set", "never-created-agent"])

        assert result.exit_code == 1
        assert "not found" in result.output

    def test_get_with_duplicate_id(self):
        """Test get command fails when ID already exists."""
        agent_id = f"dup-test-{uuid.uuid4().hex[:8]}"

        # First get succeeds
        result1 = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert result1.exit_code == 0

        # Second get with same ID fails
        result2 = runner.invoke(app, ["agent", "get", "qa-agent", agent_id])
        assert result2.exit_code == 1
        assert "already exists" in result2.output


class TestSerialNumbers:
    """Tests for serial number functionality."""

    def test_serial_number_in_list(self):
        """Test that serial numbers appear in agent list."""
        # Create an agent with a short ID to avoid truncation
        agent_id = f"ser-{uuid.uuid4().hex[:6]}"
        get_result = runner.invoke(app, ["agent", "get", "chat-agent", agent_id])
        assert get_result.exit_code == 0

        # Run ls to see serial numbers
        ls_result = runner.invoke(app, ["agent", "ls"])
        assert ls_result.exit_code == 0

        # Verify two separate tables appear
        assert "Built-in Agents" in ls_result.output
        assert "Your Agents" in ls_result.output
        # Check for positive serials in both tables
        assert "│ 1 │" in ls_result.output or "│  1 │" in ls_result.output
        # Check local agent appears in Your Agents table
        assert agent_id in ls_result.output

        print(f"\nAgent list with serials:\n{ls_result.output}")


# Helper functions for direct API calls


def _send_chat_message(
    api_key: str,
    agent_id: str,
    message: str,
    session_id: str | None = None,
) -> dict:
    """Send a chat message to the agent API.

    Returns:
        Dict with 'success', 'response', and optionally 'error'.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "x-api-key": api_key,
    }

    payload = {
        "agent_id": agent_id,
        "session_id": session_id or str(uuid.uuid4()),
        "user_id": "test_user",
        "message": message,
    }

    try:
        response = httpx.post(
            CHAT_API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=60.0,
        )

        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}: {response.text}",
                "response": None,
            }

        data = response.json()
        return {
            "success": True,
            "response": data.get("response") or data.get("message") or str(data),
            "raw_data": data,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "response": None,
        }


def _send_streaming_message(
    api_key: str,
    agent_id: str,
    message: str,
    session_id: str | None = None,
) -> dict:
    """Send a streaming chat message to the agent API.

    Returns:
        Dict with 'success', 'chunks_received', 'final_content', and optionally 'error'.
    """
    headers = {
        "Content-Type": "application/json",
        "accept": "application/json",
        "x-api-key": api_key,
    }

    payload = {
        "agent_id": agent_id,
        "session_id": session_id or str(uuid.uuid4()),
        "user_id": "test_user",
        "message": message,
    }

    chunks_received = 0
    content_buffer = ""

    try:
        with httpx.stream(
            "POST",
            STREAM_API_ENDPOINT,
            json=payload,
            headers=headers,
            timeout=60.0,
        ) as response:
            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API returned status {response.status_code}",
                    "chunks_received": 0,
                    "final_content": None,
                }

            for line in response.iter_lines():
                if not line:
                    continue

                if line.startswith("data: "):
                    data = line[6:]
                    chunks_received += 1

                    if data == "[DONE]":
                        break

                    if data.startswith("[ERROR]"):
                        return {
                            "success": False,
                            "error": data,
                            "chunks_received": chunks_received,
                            "final_content": None,
                        }

                    # Decode and accumulate
                    decoded = _decode_sse_data(data)
                    content_buffer += decoded

        return {
            "success": True,
            "chunks_received": chunks_received,
            "final_content": content_buffer,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "chunks_received": chunks_received,
            "final_content": content_buffer if content_buffer else None,
        }


def _decode_sse_data(data: str) -> str:
    """Decode escape sequences from SSE data."""
    return (
        data.replace("\\n", "\n")
        .replace('\\"', '"')
        .replace("\\'", "'")
        .replace("\\&", "&")
        .replace("\\r", "\r")
        .replace("\\\\", "\\")
        .replace("\\t", "\t")
        .replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&amp;", "&")
    )
