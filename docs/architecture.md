# Architecture

Async Python client library for the Tailscale API.

## Project layout

```txt
src/tailscale/
    __init__.py          # public API re-exports
    py.typed             # PEP 561 marker (do not remove -- enables type checking for consumers)
    tailscale.py         # Tailscale client (aiohttp-based, async context manager)
    models.py            # dataclass models using mashumaro + orjson for JSON serde
    exceptions.py        # TailscaleError hierarchy
typings/
    decouple.pyi         # mypy stubs for python-decouple (mypy_path set in pyproject.toml)
tests/
    test_unit.py         # pure-logic tests, no network
    test_integration.py  # HTTP tests with aresponses mock server
    test_hypothesis.py   # property-based tests (model roundtrips, exception messages)
    test_e2e.py          # real API tests, skipped without env vars
```

## Configuration resolution

The `Tailscale` client resolves `tailnet` and `api_key` via python-decouple with constructor fallback:

1. **Environment variable** (`TAILSCALE_TAILNET` / `TAILSCALE_API_KEY`)
2. **`.env` file** (via python-decouple's `AutoConfig`)
3. **Constructor arguments** (fallback)

If neither source provides a value, `TailscaleError` is raised at construction time.

```python
# Zero-arg -- relies on env vars or .env
async with Tailscale() as client: ...

# Explicit -- constructor args used only if env/dotenv is absent
async with Tailscale(tailnet="my-net", api_key="tskey-...") as client: ...
```

## API endpoints

| Method                       | HTTP          | Endpoint                              |
| ---------------------------- | ------------- | ------------------------------------- |
| `Tailscale.devices()`        | GET           | `/tailnet/{tailnet}/devices?fields=all`|
| `Tailscale.device(device_id)`| GET           | `/device/{deviceId}?fields=all`       |
| `Tailscale.acl()`            | GET           | `/tailnet/{tailnet}/acl`              |
| `Tailscale.set_acl(policy)`  | POST          | `/tailnet/{tailnet}/acl`              |

## Models

Models use `mashumaro` `field_options(alias=...)` to map camelCase API fields to snake_case.
`__pre_deserialize__` classmethod on models handles API inconsistencies (e.g. empty string -> None).
Serialization uses orjson for performance.

### Device models

- `Device` -- single Tailscale device with addresses, tags, connectivity info
- `Devices` -- wrapper that deserializes the API list into a dict keyed by device ID
- `ClientConnectivity`, `ClientSupports` -- nested device connectivity details

### ACL policy models

- `PolicyFile` -- top-level ACL policy file containing groups, tagOwners, hosts, ssh, grants, nodeAttrs
- `AclSshRule` -- a single SSH access rule (action, src, dst, users)
- `AclGrant` -- a single network-level grant (src, dst, ip)
- `NodeAttr` -- a node attribute rule (target, attr)

`PolicyFile` uses `serialize_by_alias = True` so `to_dict()` / `to_jsonb()` produce camelCase keys matching the API format.
