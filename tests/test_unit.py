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
from tailscale.models import ClientConnectivity, ClientSupports, Device, Devices
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
