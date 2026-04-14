# Contributing

Thank you for your interest in contributing to the AI EHR Assistant!

## Getting Started

1. **Fork** the repository and clone your fork:
   ```bash
   git clone https://github.com/<your-username>/ai-ehr-assistant.git
   cd ai-ehr-assistant
   ```

2. **Create a virtual environment** and install dependencies:
   ```bash
   uv venv .venv
   source .venv/bin/activate
   uv sync --extra dev
   ```

3. **Set up your environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your OPENAI_API_KEY
   ```

4. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

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
