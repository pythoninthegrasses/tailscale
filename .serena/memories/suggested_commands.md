# Suggested Commands

## Install / Setup
```bash
uv sync --all-extras
```

## Testing
```bash
uv run pytest                          # unit tests (e2e excluded via addopts)
uv run pytest tests/test_unit.py       # single file
uv run pytest -m e2e                   # e2e (needs TAILSCALE_API_KEY, TAILSCALE_TAILNET)
```

## Linting & Formatting
```bash
uv run ruff check --fix --exit-non-zero-on-fix .   # lint + fix
uv run ruff format --check --diff .                 # format check
uv run ruff format .                                # apply formatting
```

## Type Checking
```bash
uv run mypy src/
```

## Pre-commit
```bash
prek run --all-files    # ruff, markdownlint, misc hooks; fail_fast: true
```

## System Utilities (macOS/Darwin)
- fd (find files), rg (ripgrep), ast-grep (code structure)
- fzf (fuzzy select), jq (JSON), yq (YAML/XML)
- mise for runtime management
