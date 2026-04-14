"""
Update a shared-user grant to allow SSH (tcp:22) alongside Resilio Sync (tcp:28888).

Also aligns the grant dst with the SSH rule dst (tag:nas instead of host alias)
and ensures the target device has the required tag applied.

Required env vars (or .env file):
    TAILSCALE_API_KEY
    TAILSCALE_TAILNET
    TAILSCALE_SHARED_USER       email of the shared user to update
    TAILSCALE_TARGET_DEVICE     hostname substring to match (e.g. "ds920")
"""

import asyncio
import json
import sys
from decouple import config
from tailscale import Tailscale

SHARED_USER = config("TAILSCALE_SHARED_USER", default=None)
TARGET_DEVICE = config("TAILSCALE_TARGET_DEVICE", default=None)
REQUIRED_TAG = "tag:nas"
GRANT_DST = [REQUIRED_TAG]
GRANT_PORTS = ["tcp:22", "tcp:28888"]  # SSH + Resilio Sync


def _redact(email: str) -> str:
    """Replace the local part of an email with '***'."""
    local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"***@{domain}"


async def _ensure_device_tag(client: Tailscale, hostname: str, tag: str) -> None:
    """Apply *tag* to the device matching *hostname* if not already present."""
    data = await client._request(f"tailnet/{client.tailnet}/devices")
    devices = json.loads(data)

    for device in devices.get("devices", []):
        if hostname.lower() not in device.get("name", "").lower():
            continue

        existing_tags = device.get("tags") or []
        if tag in existing_tags:
            print(f"device already has {tag}")
            return

        device_id = device["id"]
        new_tags = [*existing_tags, tag]
        await client._request(
            f"device/{device_id}/tags",
            method="POST",
            data={"tags": new_tags},
        )
        print(f"applied {tag} to device {device['name']}")
        return

    print(f"warning: no device matching '{hostname}' found", file=sys.stderr)


async def main() -> None:
    """Read ACL, patch the shared-user grant, ensure device tag, push changes."""
    if SHARED_USER is None:
        print("error: set TAILSCALE_SHARED_USER env var", file=sys.stderr)
        sys.exit(1)
    if TARGET_DEVICE is None:
        print("error: set TAILSCALE_TARGET_DEVICE env var", file=sys.stderr)
        sys.exit(1)

    redacted = _redact(SHARED_USER)

    async with Tailscale() as client:
        # Ensure the target device has the required tag
        await _ensure_device_tag(client, TARGET_DEVICE, REQUIRED_TAG)

        policy = await client.acl()

        # Find the existing grant for the shared user
        target = None
        for grant in policy.grants:
            if SHARED_USER in grant.src:
                target = grant
                break

        if target is None:
            print(f"no existing grant found for {redacted}", file=sys.stderr)
            sys.exit(1)

        print("before:")
        print(json.dumps({"dst": target.dst, "ip": target.ip}, indent=2))

        target.dst = GRANT_DST
        target.ip = GRANT_PORTS

        print("\nafter:")
        print(json.dumps({"dst": target.dst, "ip": target.ip}, indent=2))

        updated = await client.set_acl(policy)

        # Verify the write stuck
        for grant in updated.grants:
            if SHARED_USER in grant.src:
                assert grant.dst == GRANT_DST, f"dst mismatch: {grant.dst}"
                assert grant.ip == GRANT_PORTS, f"ip mismatch: {grant.ip}"
                print(f"\nverified: grant for {redacted} updated successfully")
                return

        print("error: grant missing from API response", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
