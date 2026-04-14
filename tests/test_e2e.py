"""End-to-end tests for the Tailscale API client.

These tests hit the real Tailscale API and require:
  - TAILSCALE_API_KEY env var
  - TAILSCALE_TAILNET env var

Run with: pytest -m e2e
"""

import pytest
from decouple import config
from tailscale import Tailscale

_HAS_API_KEY = config("TAILSCALE_API_KEY", default=None) is not None
_HAS_TAILNET = config("TAILSCALE_TAILNET", default=None) is not None

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(not _HAS_API_KEY, reason="TAILSCALE_API_KEY not set"),
    pytest.mark.skipif(not _HAS_TAILNET, reason="TAILSCALE_TAILNET not set"),
]


async def test_list_devices() -> None:
    """Fetch devices from the real API and check the shape of the response."""
    async with Tailscale() as client:
        devices = await client.devices()
        assert isinstance(devices, dict)
        for device_id, device in devices.items():
            assert isinstance(device_id, str)
            assert device.hostname
