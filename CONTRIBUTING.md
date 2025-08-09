# Contributing

Thank you for considering contributing to proc-format! This document describes how to set up a development environment and run tests.

## Development Setup

1. Ensure Python 3.2.5 or later is installed.
2. Clone the repository and install dependencies:
   ```bash
   pip install -e .[dev]
   ```

## Testing and Linting

* Run the test suite:
  ```bash
  pytest tests/
  ```
* Ensure code adheres to style and types. Use tools such as `ruff` or `flake8` and `mypy` if available.

## Commit Guidelines

* Keep commits focused and descriptive.
* Reference relevant issues in commit messages when appropriate.

## Pull Requests

* Include tests for any new features or bug fixes.
* Update documentation when changing behaviour or adding features.
