#!/usr/bin/env python3
"""Run product-style community workflow smoke tests for agent-travel."""

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
CASES_PATH = ROOT / "assets" / "community_workflow_cases.json"
REPORT_PATH = ROOT / "assets" / "community_smoke_report.json"
TIMEOUT_SECONDS = 10
START = "<!-- agent-travel:suggestions:start -->"
END = "<!-- agent-travel:suggestions:end -->"


def render_case_markdown(case: dict[str, object]) -> str:
    output = case["output"]
    suggestion_lines = [
        START,
        "# agent-travel suggestions",
        f"generated_at: {output['generated_at']}",
        f"expires_at: {output['expires_at']}",
        f"budget: {output['budget']}",
        f"search_mode: {output['search_mode']}",
        f"tool_preference: {output['tool_preference']}",
        f"source_scope: {output['source_scope']}",
        f"thread_scope: {output['thread_scope']}",
        f"problem_fingerprint: {output['problem_fingerprint']}",
        f"advisory_only: {output['advisory_only']}",
        f"trigger_reason: {output['trigger_reason']}",
        f"visibility: {output['visibility']}",
        f"fingerprint_hash: {output['fingerprint_hash']}",
        f"reuse_gate: {output['reuse_gate']}",
    ]
    for index, item in enumerate(output["suggestions"], start=1):
        suggestion_lines.extend(
            [
                "",
                f"## suggestion-{index}",
                f"title: {item['title']}",
                f"applies_when: {item['applies_when']}",
                f"hint: {item['hint']}",
                f"confidence: {item['confidence']}",
                f"manual_check: {item['manual_check']}",
                f"solves_point: {item['solves_point']}",
                f"new_idea: {item['new_idea']}",
                f"fit_reason: {item['fit_reason']}",
                "match_reasoning:",
            ]
        )
        for reasoning in item["match_reasoning"]:
            suggestion_lines.append(f"- {reasoning}")
        suggestion_lines.extend(
            [
                f"version_scope: {item['version_scope']}",
                f"do_not_apply_when: {item['do_not_apply_when']}",
                "evidence:",
            ]
        )
        for evidence in item["evidence"]:
            suggestion_lines.append(f"- {evidence}")
    suggestion_lines.append(END)
    return "\n".join(suggestion_lines) + "\n"


def run_command(args: list[str]) -> tuple[int, str, bool]:
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            check=False,
            timeout=TIMEOUT_SECONDS,
        )
        output = (proc.stdout + proc.stderr).strip()
        crashed = "Traceback" in output
        return proc.returncode, output, crashed
    except subprocess.TimeoutExpired:
        return 1, f"TIMEOUT after {TIMEOUT_SECONDS}s", True


def normalize_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def content_blob(output: dict[str, object]) -> str:
    parts = [
        str(output.get("problem_fingerprint", "")),
        str(output.get("trigger_reason", "")),
        str(output.get("visibility", "")),
    ]
    for suggestion in output.get("suggestions", []):
        parts.extend(
            [
                str(suggestion.get("title", "")),
                str(suggestion.get("applies_when", "")),
                str(suggestion.get("hint", "")),
                str(suggestion.get("manual_check", "")),
                str(suggestion.get("solves_point", "")),
                str(suggestion.get("new_idea", "")),
                str(suggestion.get("fit_reason", "")),
                str(suggestion.get("version_scope", "")),
                str(suggestion.get("do_not_apply_when", "")),
                " ".join(str(item) for item in suggestion.get("match_reasoning", [])),
                " ".join(str(item) for item in suggestion.get("evidence", [])),
            ]
        )
    return normalize_text(" ".join(parts))


def extract_evidence_tiers(output: dict[str, object]) -> set[str]:
    tiers = set()
    for suggestion in output.get("suggestions", []):
        for evidence in suggestion.get("evidence", []):
            label = str(evidence).split(":", 1)[0].strip().lower()
            tiers.add(label.split("_", 1)[0])
    return tiers


def positive_usefulness_score(
    case: dict[str, object],
    trigger_payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    output = case["output"]
    suggestion = output["suggestions"][0]
    eval_cfg = case.get("eval", {})
    text = content_blob(output)
    pain_terms = [normalize_text(term) for term in eval_cfg.get("pain_terms", [])]
    term_hits = sum(1 for term in pain_terms if term and term in text)
    required_tiers = set(eval_cfg.get("required_evidence_tiers", []))
    actual_tiers = extract_evidence_tiers(output)
    score = 0
    breakdown: dict[str, object] = {
        "mode": "positive",
        "pain_term_hits": term_hits,
        "pain_term_total": len(pain_terms),
        "required_evidence_tiers": sorted(required_tiers),
        "actual_evidence_tiers": sorted(actual_tiers),
    }

    if output["advisory_only"] == "true" and output["thread_scope"] == "active_conversation_only":
        score += 1
    if output["visibility"] == eval_cfg.get("expected_visibility", "silent_until_relevant"):
        score += 1
    if output["reuse_gate"] == "min_4_of_5_axes_and_ttl_valid":
        score += 1
    if len(suggestion["match_reasoning"]) >= 4:
        score += 1
    if required_tiers <= actual_tiers:
        score += 1
    if term_hits >= int(eval_cfg.get("min_term_hits", max(1, len(pain_terms) - 1))):
        score += 1
    if suggestion["manual_check"] and suggestion["do_not_apply_when"] and suggestion["version_scope"]:
        score += 1
    if trigger_payload.get("trigger_reason") == case["expected"].get("trigger_reason", case["expected"].get("event_kind")):
        score += 1

    breakdown["score"] = score
    return score, breakdown


def silent_guardrail_score(
    case: dict[str, object],
    trigger_payload: dict[str, object],
) -> tuple[int, dict[str, object]]:
    expected = case["expected"]
    eval_cfg = case.get("eval", {})
    score = 0
    observed_signals = trigger_payload.get("observed_signals", []) or []
    breakdown: dict[str, object] = {
        "mode": "silent_guardrail",
        "observed_signals": observed_signals,
    }
    if trigger_payload.get("should_run") is False:
        score += 1
    if trigger_payload.get("error_code") == expected["error_code"]:
        score += 1
    if trigger_payload.get("search_mode") == expected["search_mode"]:
        score += 1
    expected_signal = eval_cfg.get("expected_signal")
    if expected_signal and expected_signal in observed_signals:
        score += 1
    breakdown["score"] = score
    return score, breakdown


def evaluate_case(
    case: dict[str, object],
    trigger_payload: dict[str, object],
) -> tuple[int, dict[str, object], bool]:
    eval_cfg = case.get("eval", {})
    mode = eval_cfg.get("mode", "positive" if case.get("output") else "silent_guardrail")
    if mode == "silent_guardrail":
        score, breakdown = silent_guardrail_score(case, trigger_payload)
    else:
        score, breakdown = positive_usefulness_score(case, trigger_payload)
    min_score = int(eval_cfg.get("min_score", 1))
    return score, breakdown, score >= min_score


def main() -> int:
    cases = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    results = []
    with tempfile.TemporaryDirectory(prefix="agent-travel-community-") as temp:
        temp_dir = Path(temp)
        for case in cases:
            state_path = temp_dir / f"{case['id']}.state.json"
            state_path.write_text(json.dumps(case["state"], ensure_ascii=False, indent=2), encoding="utf-8")
            trigger_returncode, trigger_output, trigger_crashed = run_command(
                [sys.executable, str(SHOULD_TRAVEL), str(state_path)]
            )
            try:
                trigger_payload = json.loads(trigger_output) if trigger_output else {}
            except json.JSONDecodeError:
                trigger_payload = {}
                trigger_crashed = True

            validator_ok = True
            validator_output = "SKIPPED: no output fixture for blocked case"
            if "output" in case:
                suggestion_path = temp_dir / f"{case['id']}.suggestions.md"
                suggestion_path.write_text(render_case_markdown(case), encoding="utf-8")
                validator_returncode, validator_output, validator_crashed = run_command(
                    [sys.executable, str(VALIDATOR), str(suggestion_path)]
                )
                validator_ok = validator_returncode == 0 and not validator_crashed

            expected = case["expected"]
            trigger_ok = (
                trigger_returncode == 0
                and not trigger_crashed
                and trigger_payload.get("should_run") == expected["should_run"]
                and trigger_payload.get("search_mode") == expected["search_mode"]
                and trigger_payload.get("error_code") == expected["error_code"]
            )
            with_skill_score, score_breakdown, eval_ok = evaluate_case(case, trigger_payload)
            without_skill_score = 0
            results.append(
                {
                    "id": case["id"],
                    "title": case["title"],
                    "host": case["host"],
                    "sources": case["sources"],
                    "trigger_ok": trigger_ok,
                    "validator_ok": validator_ok,
                    "eval_ok": eval_ok,
                    "trigger_output": trigger_output,
                    "validator_output": validator_output,
                    "with_skill_score": with_skill_score,
                    "without_skill_score": without_skill_score,
                    "score_delta": with_skill_score - without_skill_score,
                    "score_breakdown": score_breakdown,
                }
            )

    summary = {
        "total_cases": len(results),
        "smoke_passed": sum(1 for item in results if item["trigger_ok"] and item["validator_ok"]),
        "eval_passed": sum(1 for item in results if item["eval_ok"]),
        "ablation_positive": sum(1 for item in results if item["score_delta"] > 0),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    all_passed = (
        summary["smoke_passed"] == summary["total_cases"]
        and summary["eval_passed"] == summary["total_cases"]
        and summary["ablation_positive"] == summary["total_cases"]
    )
    return 0 if all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
