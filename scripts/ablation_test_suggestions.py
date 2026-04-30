#!/usr/bin/env python3
"""Compare the current validator against the v0.1.0 baseline validator."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from _test_mutators import append_suggestions, ensure_legacy_budget, replace_line, replace_once


ROOT = SCRIPT_DIR.parent
CURRENT_VALIDATOR = ROOT / "scripts" / "validate_suggestions.py"
BASELINE_VALIDATOR = ROOT / "scripts" / "baselines" / "validate_suggestions_v0_1_0.py"
CANONICAL = ROOT / "references" / "suggestion-contract.md"
REPORT_PATH = ROOT / "assets" / "ablation_report.json"
TIMEOUT_SECONDS = 10


def mutate_valid_optional_fields(text: str) -> str:
    text = replace_line(text, "visibility", "show_on_next_relevant_turn")
    text = replace_line(text, "trigger_reason", "heartbeat")
    return replace_line(text, "reuse_gate", "min_4_of_5_axes_and_ttl_valid")


def mutate_medium_mode_over_budget(text: str) -> str:
    text = replace_line(text, "search_mode", "medium")
    return append_suggestions(text, 4)


def mutate_evidence_outside_source_scope(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- tertiary_community: https://example.com/community-thread",
    )


def mutate_no_independent_evidence(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- primary_official_discussion: https://example.com/maintainer-thread",
    )


def mutate_misplaced_top_level_visibility(text: str) -> str:
    needle = (
        "fit_reason: This fits when the user already edited the skill locally "
        "and needs a fast low-risk check before more changes.\n"
    )
    return replace_once(text, needle, needle + "visibility: silent_until_relevant\n")


def mutate_malformed_evidence_item(text: str) -> str:
    return replace_once(
        text,
        "- secondary_community: https://example.com/community-thread",
        "- secondary_community\n",
    )


MUTATORS = {
    "canonical": lambda text: text,
    "valid_optional_fields": mutate_valid_optional_fields,
    "low_mode_two_suggestions": lambda text: append_suggestions(text, 2),
    "medium_mode_four_suggestions": mutate_medium_mode_over_budget,
    "invalid_confidence": lambda text: replace_line(text, "confidence", "certain"),
    "ttl_too_long": lambda text: replace_line(text, "expires_at", "2026-05-10T03:00:00+08:00"),
    "invalid_visibility": lambda text: replace_line(text, "visibility", "always_show"),
    "invalid_trigger_reason": lambda text: replace_line(text, "trigger_reason", "manual_override"),
    "invalid_reuse_gate": lambda text: replace_line(text, "reuse_gate", "ttl_valid_only"),
    "invalid_source_scope_part": lambda text: replace_line(text, "source_scope", "primary+quaternary"),
    "evidence_outside_source_scope": mutate_evidence_outside_source_scope,
    "invalid_fingerprint_hash": lambda text: replace_line(text, "fingerprint_hash", "h64:xyz"),
    "short_problem_fingerprint": lambda text: replace_line(text, "problem_fingerprint", "host|symptom|version"),
    "invalid_dates": lambda text: replace_line(text, "expires_at", "2026-04-18T03:00:00+08:00"),
    "missing_timezone": lambda text: replace_line(text, "generated_at", "2026-04-20T03:00:00"),
    "no_independent_evidence": mutate_no_independent_evidence,
    "empty_fit_reason": lambda text: replace_line(text, "fit_reason", ""),
    "misplaced_top_level_visibility": mutate_misplaced_top_level_visibility,
    "malformed_evidence_item": mutate_malformed_evidence_item,
}


def mutate(text: str, case_id: str) -> str:
    mutator = MUTATORS.get(case_id)
    if mutator:
        return mutator(text)
    raise ValueError(f"unknown case: {case_id}")


CASES = [
    {"id": "canonical", "kind": "safe"},
    {"id": "valid_optional_fields", "kind": "safe"},
    {"id": "low_mode_two_suggestions", "kind": "guardrail"},
    {"id": "medium_mode_four_suggestions", "kind": "guardrail"},
    {"id": "invalid_confidence", "kind": "guardrail"},
    {"id": "ttl_too_long", "kind": "guardrail"},
    {"id": "invalid_visibility", "kind": "guardrail"},
    {"id": "invalid_trigger_reason", "kind": "guardrail"},
    {"id": "invalid_reuse_gate", "kind": "guardrail"},
    {"id": "invalid_source_scope_part", "kind": "guardrail"},
    {"id": "evidence_outside_source_scope", "kind": "guardrail"},
    {"id": "invalid_fingerprint_hash", "kind": "guardrail"},
    {"id": "short_problem_fingerprint", "kind": "guardrail"},
    {"id": "missing_timezone", "kind": "guardrail"},
    {"id": "no_independent_evidence", "kind": "guardrail"},
    {"id": "empty_fit_reason", "kind": "guardrail"},
    {"id": "misplaced_top_level_visibility", "kind": "guardrail"},
    {"id": "malformed_evidence_item", "kind": "guardrail"},
    {"id": "invalid_dates", "kind": "shared-invalid"},
]


def invoke(validator: Path, target: Path) -> dict[str, object]:
    try:
        proc = subprocess.run(
            [sys.executable, str(validator), str(target)],
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        passed = proc.returncode == 0
    except subprocess.TimeoutExpired:
        output = f"TIMEOUT after {TIMEOUT_SECONDS}s"
        crashed = True
        passed = False
    return {
        "passed": passed,
        "output": output,
        "crashed": crashed,
    }


def rate(items: list[dict[str, object]], predicate) -> float:
    if not items:
        return 0.0
    return sum(1 for item in items if predicate(item)) / len(items)


def run_case(case: dict[str, str], canonical: str, temp_dir: Path) -> dict[str, object]:
    target = temp_dir / f"{case['id']}.md"
    current_case = mutate(canonical, case["id"])
    target.write_text(current_case, encoding="utf-8")
    baseline_target = temp_dir / f"{case['id']}.baseline.md"
    baseline_target.write_text(ensure_legacy_budget(current_case), encoding="utf-8")
    baseline = invoke(BASELINE_VALIDATOR, baseline_target)
    current = invoke(CURRENT_VALIDATOR, target)
    return {
        "case": case["id"],
        "kind": case["kind"],
        "baseline_passed": baseline["passed"],
        "current_passed": current["passed"],
        "baseline_crashed": baseline["crashed"],
        "current_crashed": current["crashed"],
    }


def build_report(case_results: list[dict[str, object]]) -> dict[str, object]:
    guardrail_cases = [item for item in case_results if item["kind"] == "guardrail"]
    safe_cases = [item for item in case_results if item["kind"] == "safe"]
    shared_invalid_cases = [item for item in case_results if item["kind"] == "shared-invalid"]
    return {
        "baseline_ref": "v0.1.0-local-baseline",
        "current_ref": "agent-travel-current",
        "summary": {
            "baseline_guardrail_rejection_rate": rate(guardrail_cases, lambda item: not item["baseline_passed"]),
            "current_guardrail_rejection_rate": rate(guardrail_cases, lambda item: not item["current_passed"]),
            "baseline_safe_acceptance_rate": rate(safe_cases, lambda item: item["baseline_passed"]),
            "current_safe_acceptance_rate": rate(safe_cases, lambda item: item["current_passed"]),
            "baseline_shared_invalid_rejection_rate": rate(
                shared_invalid_cases,
                lambda item: not item["baseline_passed"],
            ),
            "current_shared_invalid_rejection_rate": rate(
                shared_invalid_cases,
                lambda item: not item["current_passed"],
            ),
        },
        "cases": case_results,
    }


def current_guardrails_pass(summary: dict[str, object]) -> bool:
    return (
        summary["current_guardrail_rejection_rate"] == 1.0
        and summary["current_safe_acceptance_rate"] == 1.0
        and summary["current_shared_invalid_rejection_rate"] == 1.0
    )


def main() -> int:
    canonical = CANONICAL.read_text(encoding="utf-8")
    case_results = []
    with tempfile.TemporaryDirectory(prefix="agent-travel-ablation-") as temp:
        temp_dir = Path(temp)
        for case in CASES:
            case_results.append(run_case(case, canonical, temp_dir))

    report = build_report(case_results)
    REPORT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if current_guardrails_pass(report["summary"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
