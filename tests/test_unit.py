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
    Latency,
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
        "latency": {
            "Dallas": {"latencyMs": 60.46384, "preferred": true},
            "New York City": {"latencyMs": 31.323}
        },
        "mappingVariesByDestIP": false
    },
    "clientVersion": "1.22.0",
    "connectedToControl": true,
    "created": "2023-01-01T00:00:00Z",
    "id": "device-1",
    "expires": "2024-01-01T00:00:00Z",
    "hostname": "myhost",
    "isEphemeral": false,
    "isExternal": false,
    "keyExpiryDisabled": false,
    "lastSeen": "2023-06-01T12:00:00Z",
    "machineKey": "mkey:abc",
    "name": "myhost.tail.ts.net",
    "nodeId": "n1234567CNTRL",
    "nodeKey": "nodekey:def",
    "os": "linux",
    "sshEnabled": true,
    "tailnetLockError": "",
    "tailnetLockKey": "tlpub:abc123",
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


def test_device_missing_optional_fields() -> None:
    """Device deserializes when optional fields are absent."""
    minimal = """{
        "addresses": ["100.64.0.1"],
        "authorized": true,
        "blocksIncomingConnections": false,
        "clientVersion": "1.22.0",
        "connectedToControl": false,
        "id": "device-1",
        "hostname": "myhost",
        "isExternal": false,
        "keyExpiryDisabled": false,
        "machineKey": "mkey:abc",
        "name": "myhost.tail.ts.net",
        "nodeId": "n999",
        "nodeKey": "nodekey:def",
        "os": "linux",
        "tailnetLockKey": "",
        "updateAvailable": false,
        "user": "user@example.com"
    }"""
    device = Device.from_json(minimal)
    assert device.device_id == "device-1"
    assert device.last_seen is None
    assert device.created is None
    assert device.expires is None
    assert device.client_connectivity is None
    assert device.is_ephemeral is None
    assert device.multiple_connections is None
    assert device.ssh_enabled is None
    assert device.tailnet_lock_error is None


def test_client_supports_missing_hair_pinning() -> None:
    """ClientSupports deserializes when hairPinning is absent."""
    minimal = '{"ipv6": true, "pcp": false, "pmp": false, "udp": true, "upnp": false}'
    supports = ClientSupports.from_json(minimal)
    assert supports.hair_pinning is None
    assert supports.ipv6 is True


def test_latency_from_json() -> None:
    """Latency dataclass deserializes latencyMs alias and optional preferred."""
    full = '{"latencyMs": 60.46, "preferred": true}'
    lat = Latency.from_json(full)
    assert lat.latency_ms == pytest.approx(60.46)
    assert lat.preferred is True

    minimal = '{"latencyMs": 31.3}'
    lat2 = Latency.from_json(minimal)
    assert lat2.latency_ms == pytest.approx(31.3)
    assert lat2.preferred is None


def test_client_connectivity_latency() -> None:
    """ClientConnectivity.latency deserializes nested Latency dict."""
    device = Device.from_json(_DEVICE_JSON)
    cc = device.client_connectivity
    assert cc is not None
    assert "Dallas" in cc.latency
    assert cc.latency["Dallas"].latency_ms == pytest.approx(60.46384)
    assert cc.latency["Dallas"].preferred is True
    assert "New York City" in cc.latency
    assert cc.latency["New York City"].preferred is None


def test_client_connectivity_empty_latency() -> None:
    """ClientConnectivity.latency defaults to empty dict when absent."""
    raw = '{"clientSupports": {"ipv6": true, "pcp": false, "pmp": false, "udp": true, "upnp": false}}'
    cc = ClientConnectivity.from_json(raw)
    assert cc.latency == {}


def test_device_new_required_fields() -> None:
    """Device gains node_id, connected_to_control, tailnet_lock_key."""
    device = Device.from_json(_DEVICE_JSON)
    assert device.node_id == "n1234567CNTRL"
    assert device.connected_to_control is True
    assert device.tailnet_lock_key == "tlpub:abc123"


def test_device_new_optional_fields() -> None:
    """Device gains is_ephemeral, ssh_enabled, multiple_connections, tailnet_lock_error."""
    device = Device.from_json(_DEVICE_JSON)
    assert device.is_ephemeral is False
    assert device.ssh_enabled is True
    # multipleConnections absent from fixture -> None (API omits when false)
    assert device.multiple_connections is None
    # tailnetLockError is empty string -> converted to None by __pre_deserialize__
    assert device.tailnet_lock_error is None


def test_device_tailnet_lock_error_nonempty() -> None:
    """Non-empty tailnetLockError is preserved as-is."""
    patched = _DEVICE_JSON.replace('"tailnetLockError": ""', '"tailnetLockError": "key not signed"')
    device = Device.from_json(patched)
    assert device.tailnet_lock_error == "key not signed"


def test_device_tailnet_lock_error_missing() -> None:
    """Missing tailnetLockError is converted to None by __pre_deserialize__."""
    import json

    data = json.loads(_DEVICE_JSON)
    del data["tailnetLockError"]
    device = Device.from_json(json.dumps(data))
    assert device.tailnet_lock_error is None


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


# -- Multi-rule / multi-grant policy tests (mirrors fix_nas_grant.py) ----------

_MULTI_GRANT_POLICY = """{
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


def test_multi_grant_policy_ssh_rules() -> None:
    """Policy with two SSH rules deserializes both."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    assert len(policy.ssh) == 2
    assert policy.ssh[0].src == ["autogroup:admin"]
    assert policy.ssh[1].src == ["shared@example.com"]
    assert policy.ssh[1].dst == ["tag:nas"]
    assert policy.ssh[1].users == ["autogroup:nonroot"]


def test_multi_grant_policy_grants() -> None:
    """Policy with two grants deserializes both."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    assert len(policy.grants) == 2
    admin = policy.grants[0]
    shared = policy.grants[1]
    assert admin.src == ["autogroup:admin"]
    assert admin.dst == ["*"]
    assert shared.src == ["shared@example.com"]
    assert shared.dst == ["ds920"]
    assert shared.ip == ["tcp:28888"]


def test_multi_grant_policy_roundtrip() -> None:
    """Multi-rule policy survives JSON roundtrip."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    restored = PolicyFile.from_json(policy.to_jsonb())
    assert restored == policy


def test_grant_mutation_updates_fields() -> None:
    """Mutating grant dst/ip in-place is reflected in the policy."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    target = policy.grants[1]
    target.dst = ["tag:nas"]
    target.ip = ["tcp:22", "tcp:28888"]
    assert policy.grants[1].dst == ["tag:nas"]
    assert policy.grants[1].ip == ["tcp:22", "tcp:28888"]


def test_grant_mutation_roundtrip() -> None:
    """Mutated grant survives JSON roundtrip."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    policy.grants[1].dst = ["tag:nas"]
    policy.grants[1].ip = ["tcp:22", "tcp:28888"]
    restored = PolicyFile.from_json(policy.to_jsonb())
    assert restored.grants[1].dst == ["tag:nas"]
    assert restored.grants[1].ip == ["tcp:22", "tcp:28888"]


def test_grant_dst_mismatch_between_ssh_and_grant() -> None:
    """Demonstrate that SSH rule dst and grant dst can diverge (the bug this task fixes)."""
    policy = PolicyFile.from_json(_MULTI_GRANT_POLICY)
    ssh_dst = policy.ssh[1].dst
    grant_dst = policy.grants[1].dst
    # Before fix: SSH targets tag:nas but grant targets host alias ds920
    assert ssh_dst == ["tag:nas"]
    assert grant_dst == ["ds920"]
    assert ssh_dst != grant_dst


# -- _redact helper tests ------------------------------------------------------
# Duplicated here because examples/ is not an importable package.


def _redact(email: str) -> str:
    """Replace the local part of an email with '***'."""
    _local, _, domain = email.partition("@")
    if not domain:
        return "***"
    return f"***@{domain}"


def test_redact_email() -> None:
    """_redact replaces the local part of an email."""
    assert _redact("user@example.com") == "***@example.com"


def test_redact_no_domain() -> None:
    """_redact returns '***' when there is no @ sign."""
    assert _redact("noemailatall") == "***"


def test_redact_empty_string() -> None:
    """_redact handles empty string."""
    assert _redact("") == "***"
