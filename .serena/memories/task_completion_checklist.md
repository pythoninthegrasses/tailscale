# Task Completion Checklist

When finishing a task:

1. Run tests: `uv run pytest`
2. Run linter: `uv run ruff check --fix --exit-non-zero-on-fix .`
3. Run formatter: `uv run ruff format .`
4. Run type check: `uv run mypy src/`
5. Verify all acceptance criteria are met
6. Update backlog task status to Done
7. Use conventional commits (feat/fix/refactor/etc.)
