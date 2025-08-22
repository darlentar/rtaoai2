#+ Repository Guidelines

## Project Structure & Modules
- `src/rtaoai2/`: Python package (FastAPI server in `server.py`, OpenAI adapters under `openai/`, UI adapters under `ui/`).
- `tests/`: Pytest suite mirroring package layout (`tests/rtaoai/...`).
- `react-ui/`: Optional React frontend (dev server via `npm start`).
- `dumps/`: JSON event fixtures used by tests.
- Root: `pyproject.toml` (uv + deps), `uv.lock`, `README.md`.

## Build, Test, Run
```bash
# Setup (Python 3.13+, uv installed)
uv sync

# Run tests
uv run pytest

# Lint & format
uv run ruff check . --fix
uv run ruff format .

# Type check
uv run mypy src tests
uv run pyright

# Run backend (requires OPENAI_API_KEY)
OPENAI_API_KEY=... uv run fastapi dev src/rtaoai2/server.py

# Run frontend
cd react-ui && npm install && npm start
```

## Coding Style & Naming
- Python: 4-space indent, type hints required in new/changed code.
- Naming: modules `snake_case.py`, classes `PascalCase`, functions/vars `snake_case`.
- Imports: standard → third-party → local, separated by blank lines.
- Lint/format: use `ruff` for both checking and formatting before commits.

## Testing Guidelines
- Framework: `pytest` (+ `pytest-asyncio`). Async tests use `@pytest.mark.asyncio`.
- Layout: mirror `src/` structure; files named `test_*.py` and functions `test_*`.
- Fixtures: shared helpers in `tests/rtaoai/openai/conftest.py` (e.g., event dumps loader).
- Aim to cover parsing/streaming behaviors in `openai/` and `ui/`; add regression tests for bugs.

## Commit & PR Guidelines
- Messages: use concise, conventional prefixes: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`, `test:` (e.g., `feat(openai): add streaming consumer`).
- Scope one logical change per commit; keep PRs focused and small.
- PRs must include: clear description, testing steps/`uv run pytest` output, linked issues, and screenshots for UI changes.
- Run lint, format, and type checks locally; ensure CI would be green.

## Security & Configuration
- Secrets: never commit keys. Backend requires `OPENAI_API_KEY`; keep it in your shell env (README shows a local pattern) or a private `.env` not checked in.
- CORS/dev: server is configured for `localhost` origins; adjust only if necessary.
