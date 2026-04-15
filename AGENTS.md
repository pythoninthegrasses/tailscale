# AGENTS.md

Async Python client library for the Tailscale API

## Toolchain

- **Package manager:** `uv` (CI workflow still uses Poetry -- ignore it, use uv locally)
- **Runtimes:** Python 3.13, ruff 0.12, uv 0.9 (pinned in `.tool-versions` via mise)
- **Build backend:** `uv_build`
- **pyproject.toml** `requires-python = ">=3.13,<4"`; ruff `target-version = "py311"`

## Installation

Not published to PyPI. Install directly from the repo:

```bash
# Remote install
uv pip install https://github.com/pythoninthegrass/tailscale.git

# Local install
uv pip install .

# Local install for development
uv pip install -e .
```

## Developer commands

```bash
# Install deps (creates .venv automatically)
uv sync --all-extras

# Run tests (e2e excluded by default via addopts)
uv run pytest

# Run a single test file or test
uv run pytest tests/test_unit.py
uv run pytest tests/test_unit.py::test_url_join

# Run e2e tests (requires TAILSCALE_API_KEY and TAILSCALE_TAILNET env vars)
uv run pytest -m e2e

# Lint (fix mode, exits non-zero if fixes applied)
uv run ruff check --fix --exit-non-zero-on-fix .

# Format check / apply
uv run ruff format --check --diff .
uv run ruff format .

# Type check
uv run mypy src/

# Pre-commit (runs ruff, markdownlint, misc hooks; fail_fast: true)
prek run --all-files
```

## Detailed documentation

Extended docs live in `docs/`. Pull these in when you need deeper context:

- **[Architecture](docs/architecture.md)** -- project layout, configuration resolution, model design
- **[Testing](docs/testing.md)** -- test categories, configuration, integration/hypothesis/e2e details
- **[Style](docs/style.md)** -- formatting rules, import ordering, model conventions

## No PII or secrets

Never commit or track personally identifiable information (PII) anywhere in the repo. This includes but is not limited to:

- **Email addresses** -- use placeholders like `user@example.com`
- **IP addresses** -- use RFC 5737 documentation ranges (`192.0.2.x`, `198.51.100.x`, `203.0.113.x`) or `<REDACTED_IP>`
- **Tailscale IPs** -- same as above; never use real `100.x.y.z` tailnet addresses
- **API keys and tokens** -- load from environment variables; never hardcode
- **Usernames, real names, or account identifiers** -- use generic placeholders

This applies to source code, tests, documentation, backlog tasks, commit messages, and any other tracked file. If PII is discovered in existing files, redact it immediately.

## Gotchas

- CI workflow (`.github/workflows/tests.yaml`) still uses Poetry and Python 3.11 but will be refactored to uv. Use uv locally.
- `.env` contains a Tailscale API key. Do not commit secrets or reference this key in code.
- prek `fail_fast: true` -- first hook failure stops the run.
- `ruff.toml` sets `fix-only = true` globally, so `ruff check` without `--fix` still applies fixes silently. Use `--exit-non-zero-on-fix` to detect changes.

## Context7

Always use Context7 MCP when I need library/API documentation, code generation, setup or configuration steps without me having to explicitly ask.

### Libraries

- astral-sh/uv
- astral-sh/ruff
- hbnetwork/python-decouple
- hypothesisworks/hypothesis
- jdx/mise
- mrlesk/backlog.md
- websites/tailscale
- websites/taskfile_dev

<!-- BACKLOG.MD MCP GUIDELINES START -->

<CRITICAL_INSTRUCTION>

## BACKLOG WORKFLOW INSTRUCTIONS

This project uses Backlog.md MCP for all task and project management activities.

**CRITICAL GUIDANCE**

- If your client supports MCP resources, read `backlog://workflow/overview` to understand when and how to use Backlog for this project.
- If your client only supports tools or the above request fails, call `backlog.get_workflow_overview()` tool to load the tool-oriented overview (it lists the matching guide tools).

- **First time working here?** Read the overview resource IMMEDIATELY to learn the workflow
- **Already familiar?** You should have the overview cached ("## Backlog.md Overview (MCP)")
- **When to read it**: BEFORE creating tasks, or when you're unsure whether to track work

These guides cover:

- Decision framework for when to create tasks
- Search-first workflow to avoid duplicates
- Links to detailed guides for task creation, execution, and finalization
- MCP tools reference

You MUST read the overview resource to understand the complete workflow. The information is NOT summarized here.

</CRITICAL_INSTRUCTION>

<!-- BACKLOG.MD MCP GUIDELINES END -->
