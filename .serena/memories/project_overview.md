# Tailscale Python Client

Async Python client library for the Tailscale API.

## Tech Stack
- Python 3.13+ (target-version py311 for ruff)
- aiohttp for async HTTP
- mashumaro + orjson for data models/serialization
- python-decouple for config
- yarl for URL handling
- uv as package manager and build backend (uv_build)

## Project Structure
```
src/tailscale/
  __init__.py
  tailscale.py    # Main client
  models.py       # Data models (mashumaro)
  exceptions.py   # Custom exceptions
tests/
docs/
examples/
```

## Key Config Files
- pyproject.toml - project metadata, deps, pytest/coverage/mypy config
- ruff.toml - linting/formatting (line-length=130, indent=4 spaces, LF endings)
- .tool-versions - mise runtime pins (python 3.13, ruff 0.12, uv 0.9)
