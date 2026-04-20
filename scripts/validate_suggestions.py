#!/usr/bin/env python3
"""Validate the canonical agent-travel suggestion block."""

from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path


START = "<!-- agent-travel:suggestions:start -->"
END = "<!-- agent-travel:suggestions:end -->"
TOP_LEVEL_REQUIRED = {
    "generated_at",
    "expires_at",
    "budget",
    "search_mode",
    "tool_preference",
    "source_scope",
    "thread_scope",
    "problem_fingerprint",
    "advisory_only",
}
ITEM_REQUIRED = {
    "title",
    "applies_when",
    "hint",
    "confidence",
    "manual_check",
    "solves_point",
    "new_idea",
    "fit_reason",
    "match_reasoning",
    "version_scope",
    "do_not_apply_when",
}
ALLOWED_LEVELS = {"low", "medium", "high"}
ALLOWED_TOOL_PREFERENCES = {"public-only", "all-available", "custom"}
ALLOWED_VISIBILITY = {"silent_until_relevant", "show_on_next_relevant_turn"}
ALLOWED_TRIGGER_REASONS = {
    "heartbeat",
    "scheduled",
    "task_end",
    "failure_recovery",
    "idle_fallback",
}
SUGGESTION_LIMITS = {"low": 1, "medium": 3, "high": 5}
MAX_TTL = timedelta(days=14)
MATCH_AXES = {
    "host",
    "version",
    "symptom",
    "constraint",
    "constraint_pattern",
    "desired_next_outcome",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to a markdown file containing suggestion markers")
    return parser.parse_args()


def fail(errors: list[str]) -> int:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    return 1


def parse_iso(value: str) -> datetime:
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


def normalize_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")


def tokenize_scope(value: str) -> set[str]:
    return {normalize_token(part) for part in re.split(r"[^A-Za-z0-9]+", value) if part.strip()}


def parse_block(path: Path) -> tuple[dict[str, str], list[dict[str, object]], list[str]]:
    text = path.read_text(encoding="utf-8")
    start = text.rfind(START)
    end = text.rfind(END)
    if start == -1 or end == -1 or end <= start:
        return {}, [], ["missing or invalid agent-travel markers"]

    block = text[start + len(START) : end].strip()
    lines = [line.rstrip() for line in block.splitlines()]
    errors: list[str] = []
    top_level: dict[str, str] = {}
    suggestions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    current_evidence: list[str] | None = None
    current_match_reasoning: list[str] | None = None

    key_pattern = re.compile(r"^([a-z_]+):\s*(.+)$")
    heading_pattern = re.compile(r"^##\s+suggestion-\d+\s*$")

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("# agent-travel suggestions"):
            continue
        if heading_pattern.match(line):
            current = {"evidence": [], "match_reasoning": []}
            suggestions.append(current)
            current_evidence = None
            current_match_reasoning = None
            continue
        if line == "evidence:":
            if current is None:
                errors.append("found evidence block before any suggestion heading")
                continue
            current_evidence = current["evidence"]  # type: ignore[assignment]
            current_match_reasoning = None
            continue
        if line == "match_reasoning:":
            if current is None:
                errors.append("found match_reasoning block before any suggestion heading")
                continue
            current_match_reasoning = current["match_reasoning"]  # type: ignore[assignment]
            current_evidence = None
            continue
        if line.startswith("- "):
            if current_evidence is not None:
                current_evidence.append(line[2:].strip())
                continue
            if current_match_reasoning is not None:
                current_match_reasoning.append(line[2:].strip())
                continue
            errors.append(f"unexpected list item outside block: {line}")
            continue

        match = key_pattern.match(line)
        if not match:
            errors.append(f"unrecognized line: {line}")
            current_evidence = None
            current_match_reasoning = None
            continue

        key, value = match.groups()
        current_evidence = None
        current_match_reasoning = None
        if current is None:
            top_level[key] = value
        else:
            current[key] = value

    return top_level, suggestions, errors


def suggestion_limit(top_level: dict[str, str]) -> int | None:
    values = []
    for key in ("budget", "search_mode"):
        value = top_level.get(key)
        if value in SUGGESTION_LIMITS:
            values.append(SUGGESTION_LIMITS[value])
    return min(values) if values else None


def validate_top_level(top_level: dict[str, str], suggestion_count: int) -> list[str]:
    errors: list[str] = []
    missing = sorted(TOP_LEVEL_REQUIRED - set(top_level))
    if missing:
        errors.append(f"missing top-level fields: {', '.join(missing)}")
        return errors

    if top_level.get("advisory_only", "").lower() != "true":
        errors.append("advisory_only must be true")
    if top_level.get("thread_scope") != "active_conversation_only":
        errors.append("thread_scope must be active_conversation_only")

    budget = top_level.get("budget", "")
    if budget not in ALLOWED_LEVELS:
        errors.append("budget must be one of: low, medium, high")
    search_mode = top_level.get("search_mode", "")
    if search_mode not in ALLOWED_LEVELS:
        errors.append("search_mode must be one of: low, medium, high")
    tool_preference = top_level.get("tool_preference", "")
    if tool_preference not in ALLOWED_TOOL_PREFERENCES:
        errors.append("tool_preference must be one of: all-available, custom, public-only")

    source_scope = tokenize_scope(top_level.get("source_scope", ""))
    if "primary" not in source_scope:
        errors.append("source_scope must include primary")

    visibility = top_level.get("visibility")
    if visibility and visibility not in ALLOWED_VISIBILITY:
        errors.append("visibility must be one of: show_on_next_relevant_turn, silent_until_relevant")

    trigger_reason = top_level.get("trigger_reason")
    if trigger_reason and trigger_reason not in ALLOWED_TRIGGER_REASONS:
        errors.append(
            "trigger_reason must be one of: failure_recovery, heartbeat, idle_fallback, scheduled, task_end"
        )

    reuse_gate = top_level.get("reuse_gate")
    if reuse_gate:
        lowered = reuse_gate.lower()
        if "min_4_of_5" not in lowered and "4" not in lowered:
            errors.append("reuse_gate must mention 4 or min_4_of_5")

    if not top_level.get("problem_fingerprint", "").strip():
        errors.append("problem_fingerprint must be non-empty")

    if {"generated_at", "expires_at"} <= set(top_level):
        try:
            generated = parse_iso(top_level["generated_at"])
            expires = parse_iso(top_level["expires_at"])
            if expires <= generated:
                errors.append("expires_at must be later than generated_at")
            if expires - generated > MAX_TTL:
                errors.append("expires_at must be within 14 days of generated_at")
        except ValueError as exc:
            errors.append(f"invalid ISO date: {exc}")

    limit = suggestion_limit(top_level)
    if limit is not None and suggestion_count > limit:
        errors.append(f"{budget or search_mode} allows at most {limit} suggestion(s)")

    return errors


def validate_suggestion(index: int, suggestion: dict[str, object]) -> list[str]:
    errors: list[str] = []
    missing = sorted(ITEM_REQUIRED - set(suggestion))
    if missing:
        errors.append(f"suggestion-{index} is missing fields: {', '.join(missing)}")
        return errors

    for field in ("title", "applies_when", "hint", "manual_check", "do_not_apply_when"):
        value = str(suggestion.get(field, "")).strip()
        if not value:
            errors.append(f"suggestion-{index} field {field} must be non-empty")

    confidence = str(suggestion.get("confidence", ""))
    if confidence not in ALLOWED_LEVELS:
        errors.append(f"suggestion-{index} confidence must be one of: low, medium, high")

    evidence = suggestion.get("evidence", [])
    if not isinstance(evidence, list) or len(evidence) < 2:
        errors.append(f"suggestion-{index} needs at least 2 evidence items")
    else:
        evidence_tiers = []
        for item in evidence:
            label = str(item).split(":", 1)[0]
            normalized = normalize_token(label)
            evidence_tiers.append(normalized.split("_", 1)[0] if normalized else "")
        if "primary" not in evidence_tiers:
            errors.append(f"suggestion-{index} needs at least 1 primary evidence item")

    match_reasoning = suggestion.get("match_reasoning", [])
    if not isinstance(match_reasoning, list) or len(match_reasoning) < 4:
        errors.append(f"suggestion-{index} needs at least 4 match_reasoning items")
    else:
        axes = set()
        for item in match_reasoning:
            if ":" not in str(item):
                errors.append(f"suggestion-{index} match_reasoning items must use axis: explanation format")
                break
            axis, explanation = str(item).split(":", 1)
            normalized_axis = normalize_token(axis)
            if normalized_axis not in MATCH_AXES:
                continue
            if not explanation.strip():
                errors.append(f"suggestion-{index} match_reasoning explanations must be non-empty")
                break
            axes.add(normalized_axis)
        if len(axes) < 4:
            errors.append(f"suggestion-{index} needs at least 4 distinct match_reasoning axes")

    return errors


def main() -> int:
    args = parse_args()
    path = Path(args.path)
    if not path.exists():
        return fail([f"file not found: {path}"])

    try:
        top_level, suggestions, errors = parse_block(path)
    except OSError as exc:
        return fail([f"failed to read {path}: {exc}"])

    errors.extend(validate_top_level(top_level, len(suggestions)))
    if not suggestions:
        errors.append("no suggestions found")

    for index, suggestion in enumerate(suggestions, start=1):
        errors.extend(validate_suggestion(index, suggestion))

    if errors:
        return fail(errors)

    print(f"OK: validated {len(suggestions)} suggestion(s) in {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
