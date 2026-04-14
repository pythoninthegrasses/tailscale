# Testing

## Running tests

```bash
# Run tests (e2e excluded by default via addopts)
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

These are excluded by default via pytest `addopts`. Run with `uv run pytest -m e2e`.
