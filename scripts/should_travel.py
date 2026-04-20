#!/usr/bin/env python3
"""Decide whether agent-travel should run for a given host state."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path


DEFAULTS = {
    "active_conversation_window": "24h",
    "quiet_after_user_action": "20m",
    "quiet_after_agent_action": "5m",
    "max_runs_per_thread_per_day": 1,
    "max_runs_per_user_per_day": 3,
}
EVENTS = {"heartbeat", "scheduled", "task_end", "failure_recovery", "idle_fallback"}


@dataclass
class Decision:
    should_run: bool
    search_mode: str
    trigger_reason: str
    reason: str


class InputError(ValueError):
    """Raised when a readable state file has malformed fields."""


def emit(decision: Decision) -> None:
    print(
        json.dumps(
            {
                "should_run": decision.should_run,
                "search_mode": decision.search_mode,
                "trigger_reason": decision.trigger_reason,
                "reason": decision.reason,
            },
            ensure_ascii=False,
        )
    )


def parse_duration(value: str) -> timedelta:
    stripped = value.strip().lower()
    if len(stripped) < 2:
        raise InputError(f"invalid duration: {value}")
    amount = int(stripped[:-1])
    unit = stripped[-1]
    if unit == "m":
        return timedelta(minutes=amount)
    if unit == "h":
        return timedelta(hours=amount)
    if unit == "d":
        return timedelta(days=amount)
    raise InputError(f"invalid duration unit: {value}")


def parse_timestamp(name: str, value: str) -> datetime:
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise InputError(f"invalid {name}: {exc}") from exc


def as_bool(value: object, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    raise InputError(f"invalid boolean value: {value}")


def as_int(value: object, default: int) -> int:
    if value is None:
        return default
    if isinstance(value, bool):
        raise InputError(f"invalid integer value: {value}")
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise InputError(f"invalid integer value: {value}") from exc


def get_duration(state: dict[str, object], key: str) -> timedelta:
    raw = state.get(key, DEFAULTS[key])
    if isinstance(raw, str):
        return parse_duration(raw)
    raise InputError(f"invalid duration value for {key}: {raw}")


def get_event_kind(state: dict[str, object]) -> str:
    raw = str(state.get("event_kind", "")).strip().lower()
    if raw == "idle":
        raw = "idle_fallback"
    return raw


def infer_search_mode(state: dict[str, object]) -> str:
    if as_bool(state.get("user_explicit_deep_research_request"), False):
        return "high"
    medium_signals = [
        as_int(state.get("related_failures"), 0) >= 2,
        as_int(state.get("user_corrections"), 0) >= 2,
        as_int(state.get("unresolved_blocker_count"), 0) >= 1,
        as_bool(state.get("version_mismatch_seen"), False),
        as_bool(state.get("user_explicit_search_request"), False),
    ]
    if any(medium_signals):
        return "medium"
    return "low"


def decide(state: dict[str, object]) -> Decision:
    event_kind = get_event_kind(state)
    if event_kind not in EVENTS:
        return Decision(False, "low", event_kind or "unknown", "unsupported event_kind")

    if not as_bool(state.get("enabled"), True):
        return Decision(False, "low", event_kind, "travel is disabled")

    try:
        now = parse_timestamp("now", str(state["now"]))
        last_thread_activity = parse_timestamp("last_thread_activity", str(state["last_thread_activity"]))
        last_user_action = parse_timestamp(
            "last_user_action",
            str(state.get("last_user_action", state["last_thread_activity"])),
        )
        last_agent_action = parse_timestamp(
            "last_agent_action",
            str(state.get("last_agent_action", state["last_thread_activity"])),
        )
    except KeyError as exc:
        return Decision(False, "low", event_kind, f"missing required field: {exc.args[0]}")

    active_window = get_duration(state, "active_conversation_window")
    quiet_after_user = get_duration(state, "quiet_after_user_action")
    quiet_after_agent = get_duration(state, "quiet_after_agent_action")
    max_runs_per_thread = as_int(
        state.get("max_runs_per_thread_per_day"),
        int(DEFAULTS["max_runs_per_thread_per_day"]),
    )
    max_runs_per_user = as_int(
        state.get("max_runs_per_user_per_day"),
        int(DEFAULTS["max_runs_per_user_per_day"]),
    )

    if as_bool(state.get("user_operation_in_progress"), False):
        return Decision(False, "low", event_kind, "user operation in progress")
    if as_bool(state.get("agent_response_in_progress"), False):
        return Decision(False, "low", event_kind, "agent response in progress")
    if as_bool(state.get("tool_approval_pending"), False):
        return Decision(False, "low", event_kind, "tool approval pending")
    if now - last_thread_activity > active_window:
        return Decision(False, "low", event_kind, "active conversation window expired")
    if now - last_user_action < quiet_after_user:
        return Decision(False, "low", event_kind, "quiet window after user action has not elapsed")
    if now - last_agent_action < quiet_after_agent:
        return Decision(False, "low", event_kind, "quiet window after agent action has not elapsed")
    if as_int(state.get("thread_runs_today"), 0) >= max_runs_per_thread:
        return Decision(False, "low", event_kind, "thread run budget exhausted")
    if as_int(state.get("user_runs_today"), 0) >= max_runs_per_user:
        return Decision(False, "low", event_kind, "user run budget exhausted")

    related_failures = as_int(state.get("related_failures"), 0)
    user_corrections = as_int(state.get("user_corrections"), 0)
    unresolved_blocker_count = as_int(state.get("unresolved_blocker_count"), 0)
    version_mismatch_seen = as_bool(state.get("version_mismatch_seen"), False)
    user_explicit_search_request = as_bool(state.get("user_explicit_search_request"), False)
    user_explicit_deep_research_request = as_bool(
        state.get("user_explicit_deep_research_request"),
        False,
    )
    user_configured_periodic_travel = as_bool(state.get("user_configured_periodic_travel"), False)

    if event_kind == "failure_recovery":
        has_recovery_signal = any(
            [
                related_failures >= 1,
                user_corrections >= 1,
                unresolved_blocker_count >= 1,
                version_mismatch_seen,
                user_explicit_search_request,
                user_explicit_deep_research_request,
            ]
        )
        if not has_recovery_signal:
            return Decision(False, "low", event_kind, "failure recovery needs a failure or blocker signal")

    if event_kind == "scheduled" and not user_configured_periodic_travel:
        return Decision(False, "low", event_kind, "scheduled travel requires host scheduling or explicit opt-in")

    search_mode = infer_search_mode(state)
    return Decision(True, search_mode, event_kind, "active conversation, quiet window, within cooldown")


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: python scripts/should_travel.py state.json", file=sys.stderr)
        return 2

    path = Path(sys.argv[1])
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        emit(Decision(False, "low", "error", f"unable to read state file: {exc}"))
        return 1

    try:
        state = json.loads(raw)
    except json.JSONDecodeError as exc:
        emit(Decision(False, "low", "error", f"invalid JSON: {exc.msg}"))
        return 1

    if not isinstance(state, dict):
        emit(Decision(False, "low", "error", "state must be a JSON object"))
        return 0

    try:
        decision = decide(state)
    except InputError as exc:
        emit(Decision(False, "low", get_event_kind(state), str(exc)))
        return 0
    except Exception as exc:  # pragma: no cover - defensive fallback
        emit(Decision(False, "low", get_event_kind(state), f"unexpected error: {exc}"))
        return 0

    emit(decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
