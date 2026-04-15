---
id: TASK-002
title: Add default None values to Optional model fields
status: Done
assignee: []
created_date: '2026-04-15 15:11'
updated_date: '2026-04-15 15:19'
labels:
  - bug
  - upstream-port
dependencies: []
references:
  - 'https://github.com/frenck/python-tailscale/pull/1267'
  - 'https://github.com/frenck/python-tailscale/issues/1262'
  - 'https://github.com/frenck/python-tailscale/pull/1265'
documentation:
  - 'https://api.tailscale.com/api/v2'
  - src/tailscale/models.py
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Port the defensive fix from upstream PR frenck/python-tailscale#1267. All `X | None` typed fields in mashumaro dataclass models (`ClientSupports`, `Device`) currently lack `= None` defaults. When the Tailscale API omits a field (documented behavior for `lastSeen`, `multipleConnections`, and potentially others), mashumaro deserialization crashes with `InvalidFieldValue` or missing key errors.

This task adds `= None` defaults to every nullable field across the models and reorders fields so non-default fields precede default fields (required by Python dataclasses).

Context:
- Upstream PR: https://github.com/frenck/python-tailscale/pull/1267
- Upstream issue: https://github.com/frenck/python-tailscale/issues/1262
- The Tailscale API docs confirm `lastSeen` is omitted when `connectedToControl` is true, and `multipleConnections` is omitted when only one connection exists.
- This fork uses mashumaro with orjson backend (`DataClassORJSONMixin`). Models are in `src/tailscale/models.py`.
- Do NOT remove `hair_pinning` from `ClientSupports` -- the API docs still list it. Default it to `None` instead.
- Tests in `tests/test_unit.py`, `tests/test_integration.py`, and `tests/test_hypothesis.py` reference `hair_pinning` and will need fixture/assertion updates if field ordering changes.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 All `X | None` fields in `ClientSupports` and `Device` have `= None` defaults
- [x] #2 Fields are reordered so required (non-default) fields precede optional (default) fields in each dataclass
- [x] #3 `hair_pinning` is retained on `ClientSupports` with `= None` default (not removed)
- [x] #4 Deserialization succeeds when `lastSeen`, `multipleConnections`, or `hairPinning` are absent from API JSON
- [x] #5 Existing tests pass after updating fixtures and assertions for field reordering
- [x] #6 No new ruff lint or mypy errors introduced
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
## Changes

### `src/tailscale/models.py`
- **ClientSupports**: Added `= None` defaults to all 6 `bool | None` fields. `hair_pinning` uses `field(default=None, metadata=...)`, others use plain `= None`.
- **Device**: Added `= None` defaults to `client_connectivity`, `created`, `expires`, and `last_seen`. Reordered fields so 14 required (non-default) fields come first, followed by 7 optional/defaulted fields (`advertised_routes`, `client_connectivity`, `created`, `enabled_routes`, `expires`, `last_seen`, `tags`).

### `tests/test_unit.py`
- Added `test_device_missing_optional_fields` -- verifies `Device.from_json` succeeds when `lastSeen`, `created`, `expires`, and `clientConnectivity` are absent from the JSON payload.
- Added `test_client_supports_missing_hair_pinning` -- verifies `ClientSupports.from_json` succeeds when `hairPinning` is absent.

### Verification
- 71 tests pass (69 existing + 2 new)
- No ruff lint or formatting issues
- mypy clean (0 errors)
<!-- SECTION:FINAL_SUMMARY:END -->
