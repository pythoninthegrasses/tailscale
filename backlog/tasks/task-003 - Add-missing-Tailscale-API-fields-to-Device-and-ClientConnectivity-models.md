---
id: TASK-003
title: Add missing Tailscale API fields to Device and ClientConnectivity models
status: Done
assignee: []
created_date: '2026-04-15 15:11'
updated_date: '2026-04-15 15:29'
labels:
  - feature
  - upstream-port
dependencies:
  - TASK-002
references:
  - 'https://github.com/frenck/python-tailscale/pull/1268'
documentation:
  - 'https://api.tailscale.com/api/v2'
  - src/tailscale/models.py
priority: medium
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the feature additions from upstream PR frenck/python-tailscale#1268. The current models are missing several fields that the Tailscale API returns. This causes data loss -- callers cannot access useful device information like `nodeId` (the preferred device identifier), control server connectivity, latency data, or SSH/ephemeral status.

New models:
- `Latency` dataclass with `latency_ms: float` (alias `latencyMs`) and `preferred: bool | None = None`

New fields on `ClientConnectivity`:
- `latency: dict[str, Latency]` (default empty dict)

New fields on `Device`:
- `node_id: str` (alias `nodeId`) -- the preferred device identifier per API docs
- `connected_to_control: bool` (alias `connectedToControl`)
- `tailnet_lock_key: str` (alias `tailnetLockKey`) -- may be empty string
- `is_ephemeral: bool | None = None` (alias `isEphemeral`)
- `multiple_connections: bool | None = None` (alias `multipleConnections`) -- omitted when false per API docs
- `ssh_enabled: bool | None = None` (alias `sshEnabled`)
- `tailnet_lock_error: str | None = None` (alias `tailnetLockError`) -- empty string converted to None in `__pre_deserialize__`

Context:
- Upstream PR: https://github.com/frenck/python-tailscale/pull/1268
- All fields are confirmed present in the official Tailscale API schema.
- `postureIdentity` is intentionally excluded (Enterprise plans only).
- Models are in `src/tailscale/models.py`, serialization uses mashumaro `DataClassORJSONMixin`.
- This task depends on the "default None values" task being applied first, since that establishes the field ordering and default patterns.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 `Latency` dataclass is added with `latency_ms` and `preferred` fields
- [x] #2 `ClientConnectivity` gains a `latency: dict[str, Latency]` field defaulting to empty dict
- [x] #3 `Device` gains `node_id`, `connected_to_control`, `tailnet_lock_key` as required fields
- [x] #4 `Device` gains `is_ephemeral`, `multiple_connections`, `ssh_enabled`, `tailnet_lock_error` as optional fields with `None` defaults
- [x] #5 `__pre_deserialize__` converts empty `tailnetLockError` to `None`
- [x] #6 Unit tests cover deserialization of new fields including edge cases (missing optional fields, empty `tailnetLockError`)
- [x] #7 No new ruff lint or mypy errors introduced
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Changes\n\n### `src/tailscale/models.py`\n- **Latency**: New dataclass with `latency_ms: float` (alias `latencyMs`) and `preferred: bool | None = None`.\n- **ClientConnectivity**: Added `latency: dict[str, Latency]` field (default empty dict) for DERP region latency data.\n- **Device**: Added 3 required fields -- `connected_to_control: bool` (alias `connectedToControl`), `node_id: str` (alias `nodeId`), `tailnet_lock_key: str` (alias `tailnetLockKey`).\n- **Device**: Added 4 optional fields -- `is_ephemeral`, `multiple_connections`, `ssh_enabled` (all `bool | None = None`), `tailnet_lock_error: str | None = None`.\n- **Device.__pre_deserialize__**: Converts empty/missing `tailnetLockError` to `None`.\n\n### `src/tailscale/__init__.py`\n- Exported `Latency` in imports and `__all__`.\n\n### `tests/test_unit.py`\n- Updated `_DEVICE_JSON` fixture with all new fields (latency data in clientConnectivity, connectedToControl, nodeId, tailnetLockKey, isEphemeral, sshEnabled, tailnetLockError).\n- Updated `test_device_missing_optional_fields` minimal JSON to include new required fields and assert new optional fields are `None`.\n- Added 7 new tests: `test_latency_from_json`, `test_client_connectivity_latency`, `test_client_connectivity_empty_latency`, `test_device_new_required_fields`, `test_device_new_optional_fields`, `test_device_tailnet_lock_error_nonempty`, `test_device_tailnet_lock_error_missing`.\n\n### `tests/test_integration.py`\n- Updated `_SINGLE_DEVICE_RESPONSE` fixture with new required fields.\n\n### `tests/test_hypothesis.py`\n- Added `Latency` import and `latency_st` strategy.\n- Updated `client_connectivity_st` with latency dict strategy.\n- Updated `device_st` with all new Device fields.\n\n### Verification\n- 78 tests pass (71 existing + 7 new)\n- ruff lint and format clean\n- mypy clean (0 errors)\n- 100% coverage on models.py
<!-- SECTION:FINAL_SUMMARY:END -->
