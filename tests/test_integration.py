"""Integration tests for the Tailscale API client.

Tests that exercise the HTTP layer with aresponses mocks.
"""

# pylint: disable=protected-access
import aiohttp
import asyncio
import pytest
from aresponses import Response, ResponsesMockServer
from tailscale import Tailscale
from tailscale.exceptions import (
    TailscaleAuthenticationError,
    TailscaleConnectionError,
    TailscaleError,
)
from unittest.mock import patch


def _no_decouple(key: str, **kw: object) -> object:
    """Stub decouple so .env is never consulted."""
    return kw.get("default")


async def test_json_request(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        response = await tailscale._request("test")
        assert response == '{"status": "ok"}'
        await tailscale.close()


async def test_internal_session(aresponses: ResponsesMockServer) -> None:
    """Test JSON response is handled correctly."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/test",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with Tailscale(tailnet="frenck", api_key="abc") as tailscale:
        response = await tailscale._request("test")
        assert response == '{"status": "ok"}'


async def test_put_request(aresponses: ResponsesMockServer) -> None:
    """Test PUT requests are handled correctly."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/test",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text='{"status": "ok"}',
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        response = await tailscale._request(
            "test",
            method=aiohttp.hdrs.METH_POST,
            data={},
        )
        assert response == '{"status": "ok"}'


async def test_timeout(aresponses: ResponsesMockServer) -> None:
    """Test request timeout from the Tailscale API."""

    # Faking a timeout by sleeping
    async def response_handler(_: aiohttp.ClientResponse) -> Response:
        """Response handler for this test."""
        await asyncio.sleep(2)
        return aresponses.Response(body="Goodmorning!")

    aresponses.add("api.tailscale.com", "/api/v2/test", "GET", response_handler)

    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(
            tailnet="frenck",
            api_key="abc",
            session=session,
            request_timeout=1,
        )
        with pytest.raises(TailscaleConnectionError):
            assert await tailscale._request("test")


async def test_http_error400(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 404 response handling."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/test",
        "GET",
        aresponses.Response(text="OMG PUPPIES!", status=404),
    )

    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        with pytest.raises(TailscaleError):
            assert await tailscale._request("test")


async def test_http_error401(aresponses: ResponsesMockServer) -> None:
    """Test HTTP 401 response handling."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/test",
        "GET",
        aresponses.Response(text="Access denied!", status=401),
    )

    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        with pytest.raises(TailscaleAuthenticationError):
            assert await tailscale._request("test")


# -- ACL endpoint integration tests -------------------------------------------

_ACL_RESPONSE = """{
    "groups": {},
    "tagOwners": {"tag:nas": ["autogroup:admin"]},
    "hosts": {"ds920": "100.75.120.75"},
    "ssh": [
        {
            "action": "accept",
            "src": ["autogroup:admin"],
            "dst": ["autogroup:self"],
            "users": ["autogroup:nonroot", "root"]
        }
    ],
    "nodeAttrs": [
        {"target": ["autogroup:members"], "attr": ["funnel"]}
    ],
    "grants": [
        {"src": ["autogroup:admin"], "dst": ["*"], "ip": ["*"]}
    ]
}"""


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_get_acl(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """GET /tailnet/{tailnet}/acl returns a PolicyFile."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/tailnet/frenck/acl",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=_ACL_RESPONSE,
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        policy = await tailscale.acl()
        assert policy.tag_owners == {"tag:nas": ["autogroup:admin"]}
        assert policy.hosts == {"ds920": "100.75.120.75"}
        assert len(policy.ssh) == 1
        assert policy.ssh[0].action == "accept"
        assert len(policy.grants) == 1
        assert policy.grants[0].src == ["autogroup:admin"]


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_set_acl(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """POST /tailnet/{tailnet}/acl updates the policy."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/tailnet/frenck/acl",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=_ACL_RESPONSE,
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        from tailscale.models import AclGrant, AclSshRule, NodeAttr, PolicyFile

        policy = PolicyFile(
            tag_owners={"tag:nas": ["autogroup:admin"]},
            hosts={"ds920": "100.75.120.75"},
            ssh=[
                AclSshRule(action="accept", src=["autogroup:admin"], dst=["autogroup:self"], users=["autogroup:nonroot", "root"])
            ],
            node_attrs=[NodeAttr(target=["autogroup:members"], attr=["funnel"])],
            grants=[AclGrant(src=["autogroup:admin"], dst=["*"], ip=["*"])],
        )
        result = await tailscale.set_acl(policy)
        assert result.tag_owners == {"tag:nas": ["autogroup:admin"]}


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_set_acl_authentication_error(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """POST /tailnet/{tailnet}/acl with bad key raises TailscaleAuthenticationError."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/tailnet/frenck/acl",
        "POST",
        aresponses.Response(text="Forbidden", status=403),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="bad-key", session=session)
        from tailscale.models import PolicyFile

        with pytest.raises(TailscaleAuthenticationError):
            await tailscale.set_acl(PolicyFile())


# -- Single device endpoint integration tests ---------------------------------

_SINGLE_DEVICE_RESPONSE = """{
    "addresses": ["100.75.120.75"],
    "authorized": true,
    "blocksIncomingConnections": false,
    "clientConnectivity": {
        "clientSupports": {
            "hairPinning": true,
            "ipv6": true,
            "pcp": false,
            "pmp": false,
            "udp": true,
            "upnp": false
        },
        "endpoints": ["1.2.3.4:5678"],
        "mappingVariesByDestIP": false
    },
    "clientVersion": "1.60.0",
    "created": "2023-01-01T00:00:00Z",
    "id": "12345",
    "expires": "2025-01-01T00:00:00Z",
    "hostname": "ds920",
    "isExternal": false,
    "keyExpiryDisabled": true,
    "lastSeen": "2024-06-01T12:00:00Z",
    "machineKey": "mkey:abc",
    "name": "ds920.tail.ts.net",
    "nodeKey": "nodekey:def",
    "os": "linux",
    "updateAvailable": false,
    "user": "lance@example.com",
    "tags": ["tag:nas"]
}"""


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_get_device(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """GET /device/{deviceId} returns a Device."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/device/12345",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=_SINGLE_DEVICE_RESPONSE,
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        device = await tailscale.device("12345")
        assert device.device_id == "12345"
        assert device.hostname == "ds920"
        assert device.tags == ["tag:nas"]
        assert device.blocks_incoming_connections is False


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_get_device_not_found(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """GET /device/{deviceId} with invalid ID raises TailscaleError."""
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/device/nonexistent",
        "GET",
        aresponses.Response(text="Not found", status=404),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        with pytest.raises(TailscaleError):
            await tailscale.device("nonexistent")


# -- Shared-user grant mutation integration tests (mirrors fix_nas_grant.py) ---

_MULTI_GRANT_ACL_RESPONSE = """{
    "groups": {},
    "tagOwners": {"tag:nas": ["autogroup:admin"]},
    "hosts": {"mbp": "100.71.214.58", "ds920": "100.75.120.75"},
    "ssh": [
        {
            "action": "accept",
            "src": ["autogroup:admin"],
            "dst": ["autogroup:self"],
            "users": ["autogroup:nonroot", "root"]
        },
        {
            "action": "accept",
            "src": ["shared@example.com"],
            "dst": ["tag:nas"],
            "users": ["autogroup:nonroot"]
        }
    ],
    "nodeAttrs": [
        {"target": ["autogroup:members"], "attr": ["funnel"]}
    ],
    "grants": [
        {"src": ["autogroup:admin"], "dst": ["*"], "ip": ["*"]},
        {"src": ["shared@example.com"], "dst": ["ds920"], "ip": ["tcp:28888"]}
    ]
}"""

_UPDATED_GRANT_ACL_RESPONSE = """{
    "groups": {},
    "tagOwners": {"tag:nas": ["autogroup:admin"]},
    "hosts": {"mbp": "100.71.214.58", "ds920": "100.75.120.75"},
    "ssh": [
        {
            "action": "accept",
            "src": ["autogroup:admin"],
            "dst": ["autogroup:self"],
            "users": ["autogroup:nonroot", "root"]
        },
        {
            "action": "accept",
            "src": ["shared@example.com"],
            "dst": ["tag:nas"],
            "users": ["autogroup:nonroot"]
        }
    ],
    "nodeAttrs": [
        {"target": ["autogroup:members"], "attr": ["funnel"]}
    ],
    "grants": [
        {"src": ["autogroup:admin"], "dst": ["*"], "ip": ["*"]},
        {"src": ["shared@example.com"], "dst": ["tag:nas"], "ip": ["tcp:22", "tcp:28888"]}
    ]
}"""


@patch("tailscale.tailscale.config", side_effect=_no_decouple)
async def test_read_modify_write_shared_user_grant(_mock: patch, aresponses: ResponsesMockServer) -> None:
    """Read ACL, mutate shared-user grant, write it back -- mirrors fix_nas_grant.py."""
    # GET returns the pre-fix policy
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/tailnet/frenck/acl",
        "GET",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=_MULTI_GRANT_ACL_RESPONSE,
        ),
    )
    # POST returns the post-fix policy
    aresponses.add(
        "api.tailscale.com",
        "/api/v2/tailnet/frenck/acl",
        "POST",
        aresponses.Response(
            status=200,
            headers={"Content-Type": "application/json"},
            text=_UPDATED_GRANT_ACL_RESPONSE,
        ),
    )
    async with aiohttp.ClientSession() as session:
        tailscale = Tailscale(tailnet="frenck", api_key="abc", session=session)
        policy = await tailscale.acl()

        # Pre-fix state: shared-user grant targets host alias with only resilio port
        shared_grant = policy.grants[1]
        assert shared_grant.src == ["shared@example.com"]
        assert shared_grant.dst == ["ds920"]
        assert shared_grant.ip == ["tcp:28888"]

        # Mutate to match SSH rule dst and add SSH port
        shared_grant.dst = ["tag:nas"]
        shared_grant.ip = ["tcp:22", "tcp:28888"]

        updated = await tailscale.set_acl(policy)

        # Post-fix state: grant dst aligned with SSH rule, both ports present
        result_grant = updated.grants[1]
        assert result_grant.dst == ["tag:nas"]
        assert result_grant.ip == ["tcp:22", "tcp:28888"]
        # Admin grant unchanged
        assert updated.grants[0].dst == ["*"]
        assert updated.grants[0].ip == ["*"]
