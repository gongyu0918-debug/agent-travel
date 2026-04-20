#!/usr/bin/env python3
"""Run reliability tests for agent-travel validators and trigger logic."""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
VALIDATOR = ROOT / "scripts" / "validate_suggestions.py"
SHOULD_TRAVEL = ROOT / "scripts" / "should_travel.py"
CANONICAL = ROOT / "references" / "suggestion-contract.md"
REPORT_PATH = ROOT / "assets" / "reliability_report.json"
START = "<!-- agent-travel:suggestions:start -->"
END = "<!-- agent-travel:suggestions:end -->"


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        raise ValueError(f"missing expected text: {old}")
    return text.replace(old, new, 1)


def replace_line(text: str, key: str, value: str) -> str:
    pattern = re.compile(rf"^{re.escape(key)}:\s*.*$", re.MULTILINE)
    updated, count = pattern.subn(f"{key}: {value}", text, count=1)
    if count != 1:
        raise ValueError(f"missing line for {key}")
    return updated


def replace_block(text: str, start_marker: str, end_marker: str, replacement: str) -> str:
    start = text.index(start_marker)
    end = text.index(end_marker, start)
    return text[:start] + replacement + text[end:]


def extract_suggestion_block(text: str) -> str:
    start = text.index("## suggestion-1")
    end = text.index(END, start)
    return text[start:end].strip()


def append_suggestions(text: str, total: int) -> str:
    block = extract_suggestion_block(text)
    extras = []
    for index in range(2, total + 1):
        extra = block.replace("## suggestion-1", f"## suggestion-{index}", 1)
        extra = extra.replace(
            "title: Refresh the skill snapshot after edits",
            f"title: Refresh the skill snapshot after edits {index}",
            1,
        )
        extras.append(extra)
    insert_at = text.rindex(END)
    return text[:insert_at] + "\n\n" + "\n\n".join(extras) + "\n" + text[insert_at:]


def mutate_missing_markers(text: str) -> str:
    return text.replace(START, "").replace(END, "")


def mutate_invalid_dates(text: str) -> str:
    return replace_line(text, "expires_at", "2026-04-18T03:00:00+08:00")


def mutate_missing_source_scope(text: str) -> str:
    return replace_once(text, "source_scope: primary+secondary\n", "")


def mutate_missing_match_reasoning(text: str) -> str:
    return replace_block(text, "match_reasoning:\n", "version_scope:", "")


def mutate_no_primary_evidence(text: str) -> str:
    return (
        text.replace("primary_official_discussion:", "secondary_discussion:", 1)
        .replace("secondary_community:", "tertiary_community:", 1)
    )


def mutate_stray_list_item(text: str) -> str:
    needle = "problem_fingerprint: host|subsystem|symptom|version\n"
    return replace_once(text, needle, needle + "- stray item at top level\n")


def mutate_bad_match_axes(text: str) -> str:
    replacement = (
        "match_reasoning:\n"
        "- host: matched the same skill-host reload surface\n"
        "- host: matched the same host build family where scan timing matters\n"
        "- symptom: matched stale behavior after a local edit\n"
        "- symptom: matched a low-risk reload check before more edits\n"
    )
    return replace_block(text, "match_reasoning:\n", "version_scope:", replacement)


def mutate_low_budget_two_suggestions(text: str) -> str:
    return append_suggestions(text, 2)


def mutate_medium_budget_four_suggestions(text: str) -> str:
    text = replace_line(text, "budget", "medium")
    text = replace_line(text, "search_mode", "medium")
    return append_suggestions(text, 4)


def mutate_invalid_confidence(text: str) -> str:
    return replace_line(text, "confidence", "certain")


def mutate_ttl_too_long(text: str) -> str:
    return replace_line(text, "expires_at", "2026-05-10T03:00:00+08:00")


def mutate_invalid_visibility(text: str) -> str:
    return replace_line(text, "visibility", "always_show")


def mutate_invalid_trigger_reason(text: str) -> str:
    return replace_line(text, "trigger_reason", "manual_override")


def mutate_invalid_reuse_gate(text: str) -> str:
    return replace_line(text, "reuse_gate", "ttl_valid_only")


def mutate_valid_optional_fields(text: str) -> str:
    text = replace_line(text, "visibility", "show_on_next_relevant_turn")
    text = replace_line(text, "trigger_reason", "heartbeat")
    return replace_line(text, "reuse_gate", "min_4_of_5_axes_and_ttl_valid")


VALIDATOR_CASES = [
    ("canonical", lambda text: text, True),
    ("missing_markers", mutate_missing_markers, False),
    ("invalid_dates", mutate_invalid_dates, False),
    ("missing_source_scope", mutate_missing_source_scope, False),
    ("missing_match_reasoning", mutate_missing_match_reasoning, False),
    ("no_primary_evidence", mutate_no_primary_evidence, False),
    ("stray_list_item", mutate_stray_list_item, False),
    ("bad_match_axes", mutate_bad_match_axes, False),
    ("low_budget_two_suggestions", mutate_low_budget_two_suggestions, False),
    ("medium_budget_four_suggestions", mutate_medium_budget_four_suggestions, False),
    ("invalid_confidence", mutate_invalid_confidence, False),
    ("ttl_too_long", mutate_ttl_too_long, False),
    ("invalid_visibility", mutate_invalid_visibility, False),
    ("invalid_trigger_reason", mutate_invalid_trigger_reason, False),
    ("invalid_reuse_gate", mutate_invalid_reuse_gate, False),
    ("valid_optional_fields", mutate_valid_optional_fields, True),
]


TRIGGER_CASES = [
    (
        "should_travel_heartbeat_quiet_low",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 0,
            "user_corrections": 0,
            "unresolved_blocker_count": 0,
            "version_mismatch_seen": False,
            "user_explicit_search_request": False,
            "user_explicit_deep_research_request": False,
        },
        True,
        "low",
    ),
    (
        "should_travel_user_active",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T11:50:00+00:00",
            "last_user_action": "2026-04-20T11:50:00+00:00",
            "last_agent_action": "2026-04-20T11:40:00+00:00",
            "user_operation_in_progress": True,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
        },
        False,
        "low",
    ),
    (
        "should_travel_failure_recovery_medium",
        {
            "enabled": True,
            "event_kind": "failure_recovery",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "related_failures": 2,
            "user_corrections": 0,
            "unresolved_blocker_count": 1,
            "version_mismatch_seen": False,
            "user_explicit_search_request": False,
            "user_explicit_deep_research_request": False,
        },
        True,
        "medium",
    ),
    (
        "should_travel_explicit_deep_request_high",
        {
            "enabled": True,
            "event_kind": "heartbeat",
            "now": "2026-04-20T12:00:00+00:00",
            "last_thread_activity": "2026-04-20T10:00:00+00:00",
            "last_user_action": "2026-04-20T11:00:00+00:00",
            "last_agent_action": "2026-04-20T11:30:00+00:00",
            "user_operation_in_progress": False,
            "agent_response_in_progress": False,
            "tool_approval_pending": False,
            "thread_runs_today": 0,
            "user_runs_today": 0,
            "user_explicit_deep_research_request": True,
        },
        True,
        "high",
    ),
]


def run_validator_case(name: str, body: str, expected_pass: bool, temp_dir: Path) -> dict[str, object]:
    path = temp_dir / f"{name}.md"
    path.write_text(body, encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip()
    crashed = "Traceback" in output
    actual_pass = proc.returncode == 0
    return {
        "case": name,
        "kind": "validator",
        "expected_pass": expected_pass,
        "actual_pass": actual_pass,
        "ok": actual_pass == expected_pass and not crashed,
        "crashed": crashed,
        "output": output,
    }


def run_trigger_case(
    name: str,
    state: dict[str, object],
    expected_should_run: bool,
    expected_search_mode: str,
    temp_dir: Path,
) -> dict[str, object]:
    path = temp_dir / f"{name}.json"
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(SHOULD_TRAVEL), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    output = (proc.stdout + proc.stderr).strip()
    crashed = "Traceback" in output
    try:
        payload = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        payload = {}
        crashed = True
    actual_should_run = payload.get("should_run")
    actual_search_mode = payload.get("search_mode")
    ok = (
        actual_should_run == expected_should_run
        and actual_search_mode == expected_search_mode
        and proc.returncode == 0
        and not crashed
    )
    return {
        "case": name,
        "kind": "trigger",
        "expected_should_run": expected_should_run,
        "actual_should_run": actual_should_run,
        "expected_search_mode": expected_search_mode,
        "actual_search_mode": actual_search_mode,
        "ok": ok,
        "crashed": crashed,
        "output": output,
    }


def main() -> int:
    canonical = CANONICAL.read_text(encoding="utf-8")
    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="agent-travel-reliability-") as temp:
        temp_dir = Path(temp)
        for name, mutator, expected_pass in VALIDATOR_CASES:
            results.append(run_validator_case(name, mutator(canonical), expected_pass, temp_dir))
        for name, state, expected_should_run, expected_search_mode in TRIGGER_CASES:
            results.append(
                run_trigger_case(name, state, expected_should_run, expected_search_mode, temp_dir)
            )

    validator_results = [item for item in results if item["kind"] == "validator"]
    trigger_results = [item for item in results if item["kind"] == "trigger"]
    summary = {
        "total_cases": len(results),
        "passed_cases": sum(1 for item in results if item["ok"]),
        "crash_count": sum(1 for item in results if item["crashed"]),
        "validator_cases": len(validator_results),
        "validator_passed": sum(1 for item in validator_results if item["ok"]),
        "trigger_cases": len(trigger_results),
        "trigger_passed": sum(1 for item in trigger_results if item["ok"]),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["passed_cases"] == summary["total_cases"] and summary["crash_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
