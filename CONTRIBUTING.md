# Contributing to Allama

Thank you for your interest in contributing to Allama! We welcome contributions from the community.

## Getting Started

1. Fork the repository on GitHub
2. Clone your fork locally
3. Set up the development environment:

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -


# Install dependencies
poetry install

# Activate the virtual environment
poetry shell
```

## Development Workflow

1. Create a new branch for your feature or bugfix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes, following the code style (Black, isort, flake8)

3. Run tests and linters:
   ```bash
   # Run tests
   poetry run pytest
   
   # Format code
   poetry run black .
   poetry run isort .
   
   # Check code style
   poetry run flake8
   ```

4. Commit your changes with a descriptive commit message

5. Push your branch and create a pull request

## Code Style

- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Use type hints for all functions and methods
- Write docstrings following Google style
- Keep lines under 88 characters (Black will handle this)

## Testing

Please add tests for any new functionality. Run the test suite with:

```bash
poetry run pytest
```

## Pull Request Process

1. Ensure any install or build dependencies are removed before the end of the layer when doing a build.
2. Update the README.md with details of changes to the interface, this includes new environment variables, exposed ports, useful file locations, and container parameters.
3. Increase the version number in pyproject.toml and the allama/__init__.py to the new version that this Pull Request would represent.
4. The PR must pass all CI checks before it can be merged.

## Reporting Issues

When creating an issue, please include:
- A clear description of the problem
- Steps to reproduce the issue
- Expected behavior
- Actual behavior
- Any relevant error messages
- Your environment (OS, Python version, etc.)
