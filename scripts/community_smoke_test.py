#!/usr/bin/env python3
"""Run product-style community workflow smoke tests for agent-travel."""

from __future__ import annotations

import json
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


def usefulness_score(case: dict[str, object]) -> int:
    output = case["output"]
    suggestion = output["suggestions"][0]
    score = 0
    if output["advisory_only"] == "true" and output["thread_scope"] == "active_conversation_only":
        score += 1
    if output["visibility"] == "silent_until_relevant":
        score += 1
    if output["reuse_gate"] == "min_4_of_5_axes_and_ttl_valid":
        score += 1
    if len(suggestion["match_reasoning"]) >= 4:
        score += 1
    if len(suggestion["evidence"]) >= 2 and any(item.startswith("primary_") for item in suggestion["evidence"]):
        score += 1
    if suggestion["manual_check"] and suggestion["do_not_apply_when"] and suggestion["version_scope"]:
        score += 1
    return score


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

            suggestion_path = temp_dir / f"{case['id']}.suggestions.md"
            suggestion_path.write_text(render_case_markdown(case), encoding="utf-8")
            validator_returncode, validator_output, validator_crashed = run_command(
                [sys.executable, str(VALIDATOR), str(suggestion_path)]
            )

            expected = case["expected"]
            trigger_ok = (
                trigger_returncode == 0
                and not trigger_crashed
                and trigger_payload.get("should_run") == expected["should_run"]
                and trigger_payload.get("search_mode") == expected["search_mode"]
                and trigger_payload.get("error_code") == expected["error_code"]
            )
            validator_ok = validator_returncode == 0 and not validator_crashed
            with_skill_score = usefulness_score(case)
            without_skill_score = 0
            results.append(
                {
                    "id": case["id"],
                    "title": case["title"],
                    "host": case["host"],
                    "sources": case["sources"],
                    "trigger_ok": trigger_ok,
                    "validator_ok": validator_ok,
                    "trigger_output": trigger_output,
                    "validator_output": validator_output,
                    "with_skill_score": with_skill_score,
                    "without_skill_score": without_skill_score,
                    "score_delta": with_skill_score - without_skill_score,
                }
            )

    summary = {
        "total_cases": len(results),
        "smoke_passed": sum(1 for item in results if item["trigger_ok"] and item["validator_ok"]),
        "ablation_positive": sum(1 for item in results if item["score_delta"] > 0),
        "results": results,
    }
    REPORT_PATH.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if summary["smoke_passed"] == summary["total_cases"] and summary["ablation_positive"] == summary["total_cases"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
