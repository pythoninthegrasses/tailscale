# Python: Asynchronous client for the Tailscale API

Asynchronous client for the Tailscale API.

## About

This package allows you to control and monitor Tailscale clients
programmatically. It is mainly created to allow third-party programs to
integrate with Tailscale.

## Installation

```bash
uv pip install https://github.com/pythoninthegrass/tailscale.git
```

## Usage

```python
import asyncio

from tailscale import Tailscale


async def main():
    """Show example on using the Tailscale API client."""
    async with Tailscale(
        tailnet="frenck",
        api_key="tskey-somethingsomething",
    ) as tailscale:

        devices = await tailscale.devices()
        print(devices)


if __name__ == "__main__":
    asyncio.run(main())
```

## Changelog & Releases

This repository keeps a changelog using [GitHub's releases](https://github.com/pythoninthegrass/tailscale/releases) functionality. The format of the log is based on [Keep a Changelog](https://keepachangelog.com/).

Releases are based on [Semantic Versioning](https://semver.org/), and use the format of `MAJOR.MINOR.PATCH`. In a nutshell, the version will be incremented based on the following:

- `MAJOR`: Incompatible or major changes.
- `MINOR`: Backwards-compatible new features and enhancements.
- `PATCH`: Backwards-compatible bugfixes and package updates.

## Contributing

Thank you for being involved! :heart_eyes:

## Minimum Requirements

- [Python 3.13+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [mise](https://mise.jdx.dev/getting-started.html)

To install all packages, including all development requirements:

```bash
# runtimes/tooling
mise install

# python virtual environment w/deps
uv sync --all-extras
```

## Development

As this repository uses the [prek](https://prek.j178.dev/installation/) framework, all changes are linted and tested with each commit. You can run all checks and tests manually, using the following command:

```bash
prek run --all-files
```

To run just the Python tests:

```bash
uv run pytest
```

## Authors & contributors

The original setup of this repository is by [Franck Nijhof](https://github.com/frenck).

## License

[MIT License](LICENSE)
