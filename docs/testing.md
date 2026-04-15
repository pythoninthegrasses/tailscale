# Testing

## Running tests

```bash
# Run all tests (e2e tests auto-skip when env vars are absent)
uv run pytest

# Run a single test file or test
uv run pytest tests/test_unit.py
uv run pytest tests/test_unit.py::test_url_join

# Run e2e tests (requires TAILSCALE_API_KEY and TAILSCALE_TAILNET env vars)
uv run pytest -m e2e
```

## Test configuration

- `asyncio_mode = "auto"` -- async test functions run without `@pytest.mark.asyncio`
- `--cov` is on by default via `addopts`
- `addopts` does **not** filter by marker -- e2e tests are collected but skipped via `skipif`

## Test categories

| File | Purpose | Network? |
| --- | --- | --- |
| `test_unit.py` | Pure-logic tests | No |
| `test_integration.py` | HTTP tests with `aresponses` mock server | Mocked |
| `test_hypothesis.py` | Property-based tests (model roundtrips, exception messages) | No |
| `test_e2e.py` | Real API tests, skipped without env vars | Yes |

## Integration tests

Integration tests use `aresponses` (mock aiohttp server).
The fixture is injected as `aresponses: ResponsesMockServer`.

## Hypothesis tests

Hypothesis tests use `@settings(max_examples=20-50)` to keep runs fast.

## E2E tests

E2E tests require the following environment variables:

- `TAILSCALE_API_KEY`
- `TAILSCALE_TAILNET`

E2E tests use `pytestmark` with two `skipif` conditions that check for the env vars
at import time via `python-decouple`. When either var is absent, all tests in the
file are skipped (shown as `s` in output). This means `uv run pytest` collects e2e
tests but skips them -- no marker filter is needed.

Run only e2e tests with `uv run pytest -m e2e`.

## CI workflow

The GitHub Actions workflow (`.github/workflows/pytest.yml`) runs on Blacksmith
runners and has two test steps:

1. **Run unit tests** (`uv run pytest -s`) -- collects all 78 tests; e2e tests
   auto-skip because the secrets env vars are not injected into this step.
2. **Run e2e tests** (`uv run pytest -m e2e -s`) -- runs only on `push` (not PRs)
   with `TAILSCALE_API_KEY` and `TAILSCALE_TAILNET` injected from repo secrets.

### Caching

`astral-sh/setup-uv@v6` caches the uv download cache (`~/.cache/uv`) by default.
The `.venv` is recreated each run but packages are linked from the cache, so
`uv sync --all-extras` typically completes in ~1 second. Caching the venv itself
is not currently necessary given the fast install times.
