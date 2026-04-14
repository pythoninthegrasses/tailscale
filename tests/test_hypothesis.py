"""Property-based tests for the Tailscale API client models."""

import copy
import dataclasses
from hypothesis import given, settings, strategies as st
from tailscale.exceptions import (
    TailscaleAuthenticationError,
    TailscaleConnectionError,
    TailscaleError,
)
from tailscale.models import ClientConnectivity, ClientSupports, Device, Devices

nullable_bool = st.one_of(st.none(), st.booleans())

client_supports_st = st.builds(
    ClientSupports,
    hair_pinning=nullable_bool,
    ipv6=nullable_bool,
    pcp=nullable_bool,
    pmp=nullable_bool,
    udp=nullable_bool,
    upnp=nullable_bool,
)

client_connectivity_st = st.builds(
    ClientConnectivity,
    client_supports=client_supports_st,
    endpoints=st.lists(st.text(min_size=1, max_size=50), max_size=5),
    mapping_varies_by_dest_ip=nullable_bool,
)

_datetime_st = st.one_of(st.none(), st.datetimes())
_nonempty_text = st.text(min_size=1, max_size=100)

device_st = st.builds(
    Device,
    addresses=st.lists(_nonempty_text, min_size=1, max_size=5),
    authorized=st.booleans(),
    blocks_incoming_connections=st.booleans(),
    client_connectivity=st.one_of(st.none(), client_connectivity_st),
    client_version=_nonempty_text,
    created=_datetime_st,
    device_id=_nonempty_text,
    expires=_datetime_st,
    hostname=_nonempty_text,
    is_external=st.booleans(),
    key_expiry_disabled=st.booleans(),
    last_seen=_datetime_st,
    machine_key=_nonempty_text,
    name=_nonempty_text,
    node_key=_nonempty_text,
    os=_nonempty_text,
    update_available=st.booleans(),
    user=_nonempty_text,
    advertised_routes=st.lists(_nonempty_text, max_size=5),
    enabled_routes=st.lists(_nonempty_text, max_size=5),
    tags=st.lists(_nonempty_text, max_size=5),
)


@given(supports=client_supports_st)
@settings(max_examples=50)
def test_client_supports_roundtrip(supports: ClientSupports) -> None:
    """ClientSupports survives a deepcopy."""
    assert copy.deepcopy(supports) == supports


@given(connectivity=client_connectivity_st)
@settings(max_examples=50)
def test_client_connectivity_roundtrip(connectivity: ClientConnectivity) -> None:
    """ClientConnectivity survives a deepcopy."""
    assert copy.deepcopy(connectivity) == connectivity


@given(device=device_st)
@settings(max_examples=20)
def test_device_roundtrip(device: Device) -> None:
    """Device survives a deepcopy."""
    assert copy.deepcopy(device) == device


@given(device=device_st)
@settings(max_examples=20)
def test_device_to_dict_preserves_fields(device: Device) -> None:
    """to_dict output contains a key for every dataclass field."""
    d = device.to_dict()
    field_names = {f.name for f in dataclasses.fields(device)}
    assert field_names == set(d.keys())


@given(msg=st.text(max_size=200))
@settings(max_examples=50)
def test_exceptions_preserve_message(msg: str) -> None:
    """All exception types preserve the original message."""
    for cls in (TailscaleError, TailscaleAuthenticationError, TailscaleConnectionError):
        exc = cls(msg)
        assert str(exc) == msg
