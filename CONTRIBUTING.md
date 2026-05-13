# Contributing

Thank you for your interest in contributing to the AI EHR Assistant!

## Getting Started

1. **Fork** the repository and clone your fork:

   ```bash
   git clone https://github.com/<your-username>/ai-ehr-assistant.git
   cd ai-ehr-assistant
   ```

2. **Rehydrate the checkout** — sync dev dependencies and install pre-commit hooks:

   ```bash
   just refresh
   ```

   `just refresh` is the canonical setup command. Run it after a fresh clone,
   after `git worktree add`, or after pulling a branch that changed
   `pyproject.toml` or `uv.lock`. Under the hood it runs `uv sync --extra dev`
   and `uv run pre-commit install`. You can still run `just install-hooks` alone
   if you only need to (re-)register hooks.

3. **Set up your environment**:

   ```bash
   cp .env.example .env
   # Edit .env with your OPENAI_API_KEY
   ```

4. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

## Per-checkout virtual environments

The `.venv` directory is git-ignored and lives inside each checkout. A new
`git worktree add` produces a worktree with **no** `.venv` until you run
`just refresh` there. After a dependency change lands on `main`, run `just refresh`
again so type checks and tests use the updated environment.

If you suddenly see unresolved imports or missing commands after switching
branches or adding a worktree, run `just refresh` before debugging further.

## Development Workflow

- Write code following existing patterns in `src/ehr_assistant/`.
- Add or update tests in `tests/`.
- Run the test suite before submitting:

  ```bash
  python3 -m pytest tests/ -v --tb=short
  ```

## Submitting Changes

1. Commit your changes with a clear message.
2. Push to your fork and open a Pull Request against `main`.
3. Describe what changed and why in the PR description.

## Code Style

- Use type hints where appropriate.
- Follow existing project conventions.
- Keep business logic verbatim from the notebook source — structural refactors only.

## Running Tests

Unit tests (no API key needed):

```bash
python3 -m pytest tests/ -v --tb=short
```

Integration tests (requires `OPENAI_API_KEY`):

```bash
OPENAI_API_KEY=your-key python3 -m pytest tests/ -v --tb=short
```

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
