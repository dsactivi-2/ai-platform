"""Project structure initialization."""

from pathlib import Path

# README content for the project root
PROJECT_README = """# Lyzr Kit Project

This directory contains your Lyzr Kit configuration and agents.

## Structure

```
project-root/
├── .env          # Your API credentials (keep secret!)
├── .gitignore    # Ignores sensitive files
├── README.md     # This file
└── agents/       # Your cloned agents
```

## Commands

- `lk auth` - Configure API credentials
- `lk agent ls` - List all agents (built-in + yours)
- `lk agent get <source> [new-id]` - Clone an agent
- `lk agent set <id>` - Update agent on platform
- `lk agent chat <id>` - Chat with an agent

## Important

- Do NOT modify the `serial` field in agent YAML files
- Keep your `.env` file secret (it contains API keys)

## Need Help?

Run `lk --help` for more information.
"""

# .gitignore content
GITIGNORE_CONTENT = """# Lyzr Kit
.env
*.pyc
__pycache__/
.DS_Store
"""


def init_project_structure() -> None:
    """Initialize project structure with README and .gitignore.

    Creates:
    - README.md (if not exists)
    - .gitignore (if not exists)
    - agents/ directory (if not exists)
    """
    try:
        cwd = Path.cwd()

        # Create README.md
        readme_path = cwd / "README.md"
        if not readme_path.exists():
            readme_path.write_text(PROJECT_README)

        # Create .gitignore
        gitignore_path = cwd / ".gitignore"
        if not gitignore_path.exists():
            gitignore_path.write_text(GITIGNORE_CONTENT)

        # Create agents directory
        agents_dir = cwd / "agents"
        agents_dir.mkdir(exist_ok=True)

    except (FileNotFoundError, OSError):
        pass  # Silently ignore errors
