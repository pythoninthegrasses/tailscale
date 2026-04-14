"""Asynchronous client for the Tailscale API."""

from .exceptions import (
    TailscaleAuthenticationError,
    TailscaleConnectionError,
    TailscaleError,
)
from .models import (
    AclGrant,
    AclSshRule,
    ClientConnectivity,
    ClientSupports,
    Device,
    Devices,
    NodeAttr,
    PolicyFile,
)
from .tailscale import Tailscale

__all__ = [
    "AclGrant",
    "AclSshRule",
    "ClientConnectivity",
    "ClientSupports",
    "Device",
    "Devices",
    "NodeAttr",
    "PolicyFile",
    "Tailscale",
    "TailscaleAuthenticationError",
    "TailscaleConnectionError",
    "TailscaleError",
]
