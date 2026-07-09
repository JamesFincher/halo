#!/usr/bin/env python3
"""Legal phase / status transition graph. Deterministic gates."""

from __future__ import annotations

from typing import Any

# Allowed directed edges: from_phase -> set of to_phases
PHASE_EDGES: dict[str, set[str]] = {
    "bootstrap": {"intake", "bootstrap"},
    "intake": {"intake", "spec_pack", "spec_review"},
    "spec_pack": {"spec_pack", "spec_review", "intake"},
    "spec_review": {"spec_review", "readiness", "intake", "spec_pack"},
    "readiness": {"readiness", "scaffold", "spec_review"},
    "scaffold": {"scaffold", "build", "readiness"},
    "build": {"build", "complete", "scaffold", "spec_review", "readiness"},
    "complete": {"complete", "build", "spec_review"},  # reopen only deliberate
    # control overlays stored in status, not phase — but allow these names if mis-set
    "paused": {"intake", "spec_review", "readiness", "scaffold", "build"},
    "blocked": {"readiness", "scaffold", "build", "intake"},
}

STATUS_VALUES = frozenset({"ACTIVE", "PAUSED", "BLOCKED", "ESCALATED", "COMPLETE"})

# Spec status machine
SPEC_EDGES: dict[str, set[str]] = {
    "none": {"none", "drafting", "ready_for_review", "locked"},
    "drafting": {"drafting", "ready_for_review", "locked", "none"},
    "ready_for_review": {"ready_for_review", "drafting", "locked"},
    "locked": {"locked", "drafting"},  # unlock -> drafting
}


def validate_phase_transition(old: str | None, new: str | None, force: bool = False) -> str | None:
    """Return error message or None if ok."""
    if new is None:
        return None
    if force:
        return None
    if old is None or old == new:
        return None
    old_n = old.lower()
    new_n = new.lower()
    allowed = PHASE_EDGES.get(old_n)
    if allowed is None:
        # unknown old phase — allow forward to known
        if new_n in PHASE_EDGES or new_n in {p for s in PHASE_EDGES.values() for p in s}:
            return None
        return f"unknown phase {new!r}"
    if new_n not in allowed:
        return (
            f"illegal phase transition {old!r} -> {new!r}; "
            f"allowed from {old}: {sorted(allowed)}. use --force to override"
        )
    return None


def validate_spec_transition(old: str | None, new: str | None, force: bool = False) -> str | None:
    if new is None or force:
        return None
    if old is None or old == new:
        return None
    allowed = SPEC_EDGES.get(old, set(SPEC_EDGES.keys()))
    if new not in allowed:
        return f"illegal spec_status {old!r} -> {new!r}; allowed: {sorted(allowed)}"
    return None


def validate_status(status: str | None) -> str | None:
    if status is None:
        return None
    if status not in STATUS_VALUES:
        return f"illegal status {status!r}; want one of {sorted(STATUS_VALUES)}"
    return None


def assert_can_set(data: dict[str, Any], *, phase: str | None = None, spec_status: str | None = None, status: str | None = None, force: bool = False) -> None:
    err = validate_phase_transition(data.get("phase"), phase, force=force)
    if err:
        raise SystemExit(f"PHASE_GATE: {err}")
    err = validate_spec_transition(data.get("spec_status"), spec_status, force=force)
    if err:
        raise SystemExit(f"SPEC_GATE: {err}")
    err = validate_status(status)
    if err:
        raise SystemExit(f"STATUS_GATE: {err}")
