"""Unit tests for the Tailscale API client.

Tests that require no network or mock server — pure logic only.
"""

# pylint: disable=protected-access

import pytest
from tailscale import Tailscale
from tailscale.exceptions import (
    TailscaleAuthenticationError,
    TailscaleConnectionError,
    TailscaleError,
)
from tailscale.models import (
    AclGrant,
    AclSshRule,
    ClientConnectivity,
    ClientSupports,
    Device,
    Devices,
    NodeAttr,
    PolicyFile,
)
from unittest.mock import patch
from yarl import URL


def test_base_exception_is_exception() -> None:
    """TailscaleError is a regular Exception."""
    assert issubclass(TailscaleError, Exception)


def test_authentication_error_inherits_base() -> None:
    """TailscaleAuthenticationError is a TailscaleError."""
    assert issubclass(TailscaleAuthenticationError, TailscaleError)


def test_connection_error_inherits_base() -> None:
    """TailscaleConnectionError is a TailscaleError."""
    assert issubclass(TailscaleConnectionError, TailscaleError)


def test_catch_all_catches_subtypes() -> None:
    """Catching TailscaleError catches all subtypes."""
    for exc_cls in (TailscaleAuthenticationError, TailscaleConnectionError):
        with pytest.raises(TailscaleError):
            raise exc_cls("test")


def test_default_request_timeout() -> None:
    """Default request_timeout is 8 seconds."""
    ts = Tailscale(tailnet="test", api_key="key")
    assert ts.request_timeout == 8


def test_default_session_is_none() -> None:
    """Session defaults to None before first request."""
    ts = Tailscale(tailnet="test", api_key="key")
    assert ts.session is None


def test_url_join() -> None:
    """Verify the URL join logic used in _request."""
    url = URL("https://api.tailscale.com/api/v2/").join(URL("tailnet/my-net/devices"))
    assert str(url) == "https://api.tailscale.com/api/v2/tailnet/my-net/devices"


_DEVICE_JSON = """{
    "addresses": ["100.64.0.1"],
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
    "clientVersion": "1.22.0",
    "created": "2023-01-01T00:00:00Z",
    "id": "device-1",
    "expires": "2024-01-01T00:00:00Z",
    "hostname": "myhost",
    "isExternal": false,
    "keyExpiryDisabled": false,
    "lastSeen": "2023-06-01T12:00:00Z",
    "machineKey": "mkey:abc",
    "name": "myhost.tail.ts.net",
    "nodeKey": "nodekey:def",
    "os": "linux",
    "updateAvailable": false,
    "user": "user@example.com",
    "tags": ["tag:server"]
}"""

_DEVICES_JSON = '{"devices": [' + _DEVICE_JSON + "]}"


def test_device_from_json() -> None:
    """Device round-trips through JSON deserialization."""
    device = Device.from_json(_DEVICE_JSON)
    assert device.device_id == "device-1"
    assert device.hostname == "myhost"
    assert device.addresses == ["100.64.0.1"]
    assert device.tags == ["tag:server"]


def test_device_client_connectivity() -> None:
    """ClientConnectivity and ClientSupports deserialize correctly."""
    device = Device.from_json(_DEVICE_JSON)
    assert isinstance(device.client_connectivity, ClientConnectivity)
    assert isinstance(device.client_connectivity.client_supports, ClientSupports)
    assert device.client_connectivity.client_supports.hair_pinning is True
    assert device.client_connectivity.endpoints == ["1.2.3.4:5678"]


def test_devices_from_json_keyed_by_id() -> None:
    """Devices.from_json produces a dict keyed by device id."""
    devices = Devices.from_json(_DEVICES_JSON)
    assert "device-1" in devices.devices
    assert devices.devices["device-1"].hostname == "myhost"


def test_device_empty_created_becomes_none() -> None:
    """An empty 'created' field is normalised to None by __pre_deserialize__."""
    patched = _DEVICE_JSON.replace('"2023-01-01T00:00:00Z"', '""').replace('"created": ""', '"created": ""')
    device = Device.from_json(patched)
    assert device.created is None


def test_device_default_lists() -> None:
    """advertisedRoutes and enabledRoutes default to empty lists."""
    device = Device.from_json(_DEVICE_JSON)
    assert device.advertised_routes == []
    assert device.enabled_routes == []


# -- decouple resolution tests ------------------------------------------------


@patch("tailscale.tailscale.config")
def test_decouple_provides_both_values(mock_config: patch) -> None:
    """When env/dotenv has both vars, constructor args are unnecessary."""
    mock_config.side_effect = lambda key, **kw: {
        "TAILSCALE_API_KEY": "env-key",
        "TAILSCALE_TAILNET": "env-tailnet",
    }[key]

    ts = Tailscale()
    assert ts.api_key == "env-key"
    assert ts.tailnet == "env-tailnet"


@patch("tailscale.tailscale.config")
def test_constructor_args_used_when_decouple_returns_nothing(mock_config: patch) -> None:
    """Constructor args are the fallback when decouple has no values."""
    mock_config.side_effect = lambda key, **kw: kw.get("default")

    ts = Tailscale(tailnet="ctor-tailnet", api_key="ctor-key")
    assert ts.tailnet == "ctor-tailnet"
    assert ts.api_key == "ctor-key"


@patch("tailscale.tailscale.config")
def test_decouple_wins_over_constructor(mock_config: patch) -> None:
    """Decouple values take precedence over constructor args."""
    mock_config.side_effect = lambda key, **kw: {
        "TAILSCALE_API_KEY": "env-key",
        "TAILSCALE_TAILNET": "env-tailnet",
    }[key]

    ts = Tailscale(tailnet="ctor-tailnet", api_key="ctor-key")
    assert ts.api_key == "env-key"
    assert ts.tailnet == "env-tailnet"


@patch("tailscale.tailscale.config")
def test_partial_decouple_partial_constructor(mock_config: patch) -> None:
    """One value from decouple, the other from constructor."""

    def fake_config(key: str, **kw: object) -> object:
        if key == "TAILSCALE_API_KEY":
            return "env-key"
        return kw.get("default")

    mock_config.side_effect = fake_config

    ts = Tailscale(tailnet="ctor-tailnet")
    assert ts.api_key == "env-key"
    assert ts.tailnet == "ctor-tailnet"


@patch("tailscale.tailscale.config")
def test_error_when_no_tailnet(mock_config: patch) -> None:
    """TailscaleError raised when tailnet is not resolvable."""
    mock_config.side_effect = lambda key, **kw: kw.get("default")

    with pytest.raises(TailscaleError, match="tailnet"):
        Tailscale(api_key="some-key")


@patch("tailscale.tailscale.config")
def test_error_when_no_api_key(mock_config: patch) -> None:
    """TailscaleError raised when api_key is not resolvable."""
    mock_config.side_effect = lambda key, **kw: kw.get("default")

    with pytest.raises(TailscaleError, match="api_key"):
        Tailscale(tailnet="some-tailnet")


@patch("tailscale.tailscale.config")
def test_error_when_nothing_provided(mock_config: patch) -> None:
    """TailscaleError raised when neither source provides any value."""
    mock_config.side_effect = lambda key, **kw: kw.get("default")

    with pytest.raises(TailscaleError):
        Tailscale()


# -- ACL policy model tests ----------------------------------------------------

_ACL_JSON = """{
    "acl": "{\\"groups\\": {}, \\"tagOwners\\": {\\"tag:nas\\": [\\"autogroup:admin\\"]}, \\"hosts\\": {\\"mbp\\": \\"100.71.214.58\\", \\"ds920\\": \\"100.75.120.75\\"}, \\"ssh\\": [{\\"action\\": \\"accept\\", \\"src\\": [\\"autogroup:admin\\"], \\"dst\\": [\\"autogroup:self\\"], \\"users\\": [\\"autogroup:nonroot\\", \\"root\\"]}], \\"nodeAttrs\\": [{\\"target\\": [\\"autogroup:members\\"], \\"attr\\": [\\"funnel\\"]}], \\"grants\\": [{\\"src\\": [\\"autogroup:admin\\"], \\"dst\\": [\\"*\\"], \\"ip\\": [\\"*\\"]}]}"
}"""

_POLICY_BODY = """{
    "groups": {},
    "tagOwners": {"tag:nas": ["autogroup:admin"]},
    "hosts": {"mbp": "100.71.214.58", "ds920": "100.75.120.75"},
    "ssh": [
        {
            "action": "accept",
            "src": ["autogroup:admin"],
            "dst": ["autogroup:self"],
            "users": ["autogroup:nonroot", "root"]
        }
    ],
    "nodeAttrs": [
        {
            "target": ["autogroup:members"],
            "attr": ["funnel"]
        }
    ],
    "grants": [
        {
            "src": ["autogroup:admin"],
            "dst": ["*"],
            "ip": ["*"]
        }
    ]
}"""


def test_policy_file_from_json() -> None:
    """PolicyFile deserializes from API JSON."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    assert policy.tag_owners == {"tag:nas": ["autogroup:admin"]}
    assert policy.hosts == {"mbp": "100.71.214.58", "ds920": "100.75.120.75"}


def test_policy_file_groups_default_empty() -> None:
    """PolicyFile.groups defaults to empty dict."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    assert policy.groups == {}


def test_policy_file_ssh_rules() -> None:
    """PolicyFile.ssh contains AclSshRule objects."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    assert len(policy.ssh) == 1
    rule = policy.ssh[0]
    assert isinstance(rule, AclSshRule)
    assert rule.action == "accept"
    assert rule.src == ["autogroup:admin"]
    assert rule.dst == ["autogroup:self"]
    assert rule.users == ["autogroup:nonroot", "root"]


def test_policy_file_grants() -> None:
    """PolicyFile.grants contains AclGrant objects."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    assert len(policy.grants) == 1
    grant = policy.grants[0]
    assert isinstance(grant, AclGrant)
    assert grant.src == ["autogroup:admin"]
    assert grant.dst == ["*"]
    assert grant.ip == ["*"]


def test_policy_file_node_attrs() -> None:
    """PolicyFile.node_attrs contains NodeAttr objects."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    assert len(policy.node_attrs) == 1
    attr = policy.node_attrs[0]
    assert isinstance(attr, NodeAttr)
    assert attr.target == ["autogroup:members"]
    assert attr.attr == ["funnel"]


def test_policy_file_roundtrip() -> None:
    """PolicyFile survives JSON serialize -> deserialize roundtrip."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    raw = policy.to_jsonb()
    restored = PolicyFile.from_json(raw)
    assert restored == policy


def test_policy_file_to_dict_keys() -> None:
    """to_dict produces camelCase keys matching the API."""
    policy = PolicyFile.from_json(_POLICY_BODY)
    d = policy.to_dict()
    assert "tagOwners" in d
    assert "nodeAttrs" in d


def test_ssh_rule_defaults() -> None:
    """AclSshRule fields default to empty lists."""
    rule = AclSshRule(action="accept")
    assert rule.src == []
    assert rule.dst == []
    assert rule.users == []


def test_grant_defaults() -> None:
    """AclGrant fields default to empty lists."""
    grant = AclGrant()
    assert grant.src == []
    assert grant.dst == []
    assert grant.ip == []


def test_policy_file_minimal() -> None:
    """PolicyFile can be constructed with all defaults (empty policy)."""
    policy = PolicyFile()
    assert policy.groups == {}
    assert policy.tag_owners == {}
    assert policy.hosts == {}
    assert policy.ssh == []
    assert policy.grants == []
    assert policy.node_attrs == []


def test_acl_url_join() -> None:
    """Verify the URL join logic for ACL endpoints."""
    url = URL("https://api.tailscale.com/api/v2/").join(URL("tailnet/my-net/acl"))
    assert str(url) == "https://api.tailscale.com/api/v2/tailnet/my-net/acl"


def test_device_url_join() -> None:
    """Verify the URL join logic for single device endpoint."""
    url = URL("https://api.tailscale.com/api/v2/").join(URL("device/12345"))
    assert str(url) == "https://api.tailscale.com/api/v2/device/12345"
