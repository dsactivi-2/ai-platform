"""Pytest configuration and shared fixtures."""

import os
import shutil
from pathlib import Path

import pytest

SANDBOX_DIR = Path(__file__).parent / "sandbox"
ROOT_DIR = Path(__file__).parent.parent
ROOT_ENV_FILE = ROOT_DIR / ".env"
SANDBOX_ENV_FILE = SANDBOX_DIR / ".env"


def _clean_sandbox():
    """Remove all files from sandbox except .gitignore and .gitkeep."""
    if SANDBOX_DIR.exists():
        for item in SANDBOX_DIR.iterdir():
            if item.name not in (".gitignore", ".gitkeep"):
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()


def _setup_env_for_tests():
    """Set up .env for tests.

    For unit tests: Creates minimal .env with test placeholder.
    For integration tests: Copies from root .env if available.

    Root .env is gitignored and contains real credentials for local development.
    """
    if ROOT_ENV_FILE.exists():
        # Use real credentials from root .env for integration tests
        shutil.copy(ROOT_ENV_FILE, SANDBOX_ENV_FILE)
    else:
        # Create minimal .env for unit tests (mocked anyway)
        SANDBOX_ENV_FILE.write_text("LYZR_API_KEY=test-placeholder-key\n")


@pytest.fixture(autouse=True)
def setup_sandbox():
    """Clean sandbox, setup .env, and cd into it before each test."""
    _clean_sandbox()
    SANDBOX_DIR.mkdir(exist_ok=True)
    _setup_env_for_tests()
    os.chdir(SANDBOX_DIR)
    yield
