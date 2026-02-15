# Contributing to lyzr-kit

Thank you for your interest in contributing to lyzr-kit! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/LyzrCore/lyzr-kit.git
   cd lyzr-kit
   ```

2. Install dependencies with uv:
   ```bash
   uv sync --all-extras
   ```

3. Verify installation:
   ```bash
   uv run lk --help
   ```

## Development Workflow

### Running Tests

```bash
uv run pytest tests/ -v
```

With coverage:
```bash
uv run pytest tests/ -v --cov=src/lyzr_kit
```

### Code Quality

**Linting:**
```bash
uv run ruff check src/ tests/
```

**Auto-fix lint issues:**
```bash
uv run ruff check --fix src/ tests/
```

**Formatting:**
```bash
uv run ruff format src/ tests/
```

**Type checking:**
```bash
uv run mypy src/
```

### Adding Dependencies

```bash
uv add <package>           # Runtime dependency
uv add --dev <package>     # Development dependency
```

## Code Style

- Follow [PEP 8](https://peps.python.org/pep-0008/) conventions
- Use type hints for all function signatures
- Write docstrings for public functions and classes
- Keep functions focused and small
- Use meaningful variable names

## Pull Request Process

1. **Fork** the repository and create a feature branch
2. **Make changes** following the code style guidelines
3. **Add tests** for new functionality
4. **Run all checks**:
   ```bash
   uv run ruff check src/ tests/
   uv run ruff format --check src/ tests/
   uv run mypy src/
   uv run pytest tests/ -v
   ```
5. **Commit** with a clear message describing the change
6. **Open a PR** against the `main` branch

## Commit Messages

Use clear, descriptive commit messages:

```
Add agent validation for required fields

- Add schema validation in AgentConfig
- Update tests for edge cases
- Fix type hints in storage manager
```

## Project Structure

```
src/lyzr_kit/
├── schemas/        # Pydantic data models
├── collection/     # Built-in YAML resources
├── modules/
│   ├── cli/       # CLI entry point
│   ├── commands/  # CLI command implementations
│   └── storage/   # Storage management
└── utils/         # Shared utilities
```

## Contributor Roles

We welcome contributions in two key areas:

### Collection Contributors

Help improve the built-in agent, tool, and feature definitions in `src/lyzr_kit/collection/`.

**How to contribute:**
- Add new agent YAML definitions
- Improve existing agent configurations
- Add examples and use cases
- Review and test collection resources

### Codebase Maintainers

Help maintain and improve the SDK codebase.

**How to contribute:**
- Fix bugs and issues
- Implement new features (Phase 3: Tools, Phase 4: Features)
- Improve test coverage
- Enhance documentation
- Review pull requests

## Questions?

- Open an issue for bugs or feature requests
- Check existing issues before creating new ones

## Maintainers

- [@harshit-vibes](https://github.com/harshit-vibes) - Lead maintainer

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
