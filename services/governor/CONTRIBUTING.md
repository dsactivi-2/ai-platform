# Contributing to Governor

Thank you for your interest in contributing to Governor! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## Getting Started

### Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/shreyas-lyzr/governor.git
   cd governor
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install development dependencies**
   ```bash
   pip install -e .[dev]
   ```

4. **Run tests to verify setup**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Make Changes

- Write clean, readable code
- Follow existing code style
- Add docstrings to all public APIs
- Keep functions focused and small

### 3. Write Tests

All new features and bug fixes should include tests:

```python
# tests/test_your_feature.py
import pytest
from governor import govern

@pytest.mark.asyncio
async def test_your_feature():
    """Test description."""
    # Your test code here
    assert result == expected
```

### 4. Run Tests and Linting

```bash
# Run tests
pytest tests/ -v --cov=governor

# Run linter
ruff check governor/ tests/

# Format code
ruff format governor/ tests/

# Type checking (optional but recommended)
mypy governor/ --ignore-missing-imports
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add approval timeout configuration

- Add timeout_seconds parameter to ApprovalPolicy
- Update documentation with timeout examples
- Add tests for timeout behavior"
```

**Commit Message Format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Adding or updating tests
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference any related issues
- Screenshots if UI-related
- Test results/coverage

## Code Style Guidelines

### Python Style

- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use `async`/`await` for asynchronous code

### Documentation

- All public APIs must have docstrings
- Use Google-style docstrings:

```python
async def approve_request(
    request_id: str,
    approver: str,
    reason: str
) -> bool:
    """
    Approve a pending request.

    Args:
        request_id: Unique identifier for the request
        approver: Email or ID of the approver
        reason: Reason for approval

    Returns:
        True if approval was successful

    Raises:
        ValueError: If request_id is invalid
    """
    pass
```

### Testing

- Aim for >80% code coverage
- Write unit tests for all new code
- Include integration tests for features
- Test both success and failure cases
- Use descriptive test names

```python
@pytest.mark.asyncio
async def test_approval_policy_blocks_execution_without_approval():
    """Test that ApprovalPolicy blocks execution when approval is not provided."""
    # Test implementation
```

## Project Structure

```
governor/
├── governor/           # Main package
│   ├── core/          # Core execution engine
│   ├── policies/      # Policy implementations
│   ├── approval/      # Approval system
│   ├── background/    # Background job queue
│   ├── storage/       # Storage backends
│   ├── events/        # Event system
│   ├── compliance/    # Compliance modules
│   └── utils/         # Utilities
├── tests/             # Test suite
├── examples/          # Example code
└── docs/              # Documentation

```

## Adding a New Policy

1. Create policy file in `governor/policies/`
2. Inherit from `Policy` base class
3. Implement `evaluate()` method
4. Add to `governor/policies/__init__.py`
5. Write tests in `tests/test_policies.py`
6. Add example in `examples/`
7. Update documentation

## Adding a New Storage Backend

1. Create backend file in `governor/storage/`
2. Inherit from `StorageBackend` base class
3. Implement all abstract methods
4. Add to `governor/storage/__init__.py`
5. Write tests in `tests/test_storage.py`
6. Update `pyproject.toml` with optional dependency
7. Add documentation

## Documentation

- Keep README.md up to date
- Add examples for new features
- Update DEPLOYMENT.md for infrastructure changes
- Include docstrings in all public APIs

## Reporting Issues

### Bug Reports

Include:
- Governor version
- Python version
- Operating system
- Minimal reproducible example
- Expected vs actual behavior
- Stack trace if applicable

### Feature Requests

Include:
- Use case description
- Proposed API/interface
- Example code showing usage
- Alternative solutions considered

## Questions?

- Open a [Discussion](https://github.com/shreyas-lyzr/governor/discussions)
- Join our community chat (if available)
- Check existing issues and documentation

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
