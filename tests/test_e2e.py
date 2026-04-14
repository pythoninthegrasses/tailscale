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


async def test_get_acl() -> None:
    """Fetch the ACL policy from the real API and check the shape."""
    async with Tailscale() as client:
        from tailscale.models import PolicyFile

        policy = await client.acl()
        assert isinstance(policy, PolicyFile)
        # Every tailnet has at least an empty groups dict.
        assert isinstance(policy.groups, dict)
        assert isinstance(policy.tag_owners, dict)
        assert isinstance(policy.hosts, dict)
        assert isinstance(policy.ssh, list)
        assert isinstance(policy.grants, list)
        assert isinstance(policy.node_attrs, list)


async def test_get_single_device() -> None:
    """Fetch a single device from the real API by looking up the first device ID."""
    async with Tailscale() as client:
        devices = await client.devices()
        assert devices, "tailnet has no devices"
        first_id = next(iter(devices))
        device = await client.device(first_id)
        assert device.device_id == first_id
        assert device.hostname


async def test_acl_roundtrip() -> None:
    """Read ACL, write it back unchanged, verify no drift."""
    async with Tailscale() as client:
        original = await client.acl()
        updated = await client.set_acl(original)
        assert updated.tag_owners == original.tag_owners
        assert updated.hosts == original.hosts
        assert len(updated.ssh) == len(original.ssh)
        assert len(updated.grants) == len(original.grants)
