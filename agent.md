# agent-travel Project Notes

Use this file as the project-level handoff guide for future agents working in this repository.

## Product Boundary

`agent-travel` is a lightweight skill protocol package. It lets a host agent use quiet windows to create a redacted, public-first research plan and later store only cross-validated advisory hints for the active conversation.

Keep these boundaries intact:

- stdlib-only Python scripts
- no daemon, database, crawler, scheduler, or background service
- host-managed scheduling only
- default `search_mode = low`
- default `tool_preference = public-only`
- output remains `advisory_only: true`
- output remains `thread_scope: active_conversation_only`
- never write travel hints into system prompts, persona files, permanent memory, or core agent instructions

Do not merge this skill with `agent-compute-mesh`. `agent-travel` is the single-node background research layer; compute mesh is a separate distributed execution concept.

## Workflow

Think in this order:

1. Trigger: `scripts/should_travel.py`
2. Redaction and dry-run planning: `scripts/plan_travel.py`
3. Suggestion contract: `references/suggestion-contract.md`
4. Contract validation: `scripts/validate_suggestions.py`
5. Reliability, ablation, and workflow smoke tests

Actual web or community search is performed by the host agent. This repo should not grow a real search engine or scraper.

## Public Documentation

Keep public surfaces English-first:

- `SKILL.md`
- `README.md`
- `agents/*.yaml`

Keep Chinese content separated in `README.zh.md` or a clearly separated Chinese section. Do not alternate Chinese and English paragraph by paragraph on ClawHub-facing surfaces.

`SKILL.md` is the primary ClawHub display surface. `README.md` is the GitHub landing page.

## Test Gate

Before publishing or claiming a fix, run:

```powershell
python -m py_compile scripts\should_travel.py scripts\plan_travel.py scripts\validate_suggestions.py scripts\reliability_test_suggestions.py scripts\ablation_test_suggestions.py scripts\community_smoke_test.py scripts\_report_utils.py scripts\_test_mutators.py
python scripts\should_travel.py examples\states\heartbeat-ready.json
python scripts\plan_travel.py examples\states\heartbeat-ready.json --context examples\thread-contexts\openclaw-cron-drift.txt
python scripts\validate_suggestions.py references\suggestion-contract.md
python scripts\reliability_test_suggestions.py
python scripts\ablation_test_suggestions.py
python scripts\community_smoke_test.py
git diff --check
```

Expected current shape:

- reliability: all cases pass, crash count is 0
- ablation: current guardrail rejection rate is 1.0 and safe acceptance is 1.0
- community smoke: all workflow cases pass

## Release Discipline

Before a GitHub or ClawHub publish, verify the working tree, run the full test gate, inspect ClawHub after publish, and confirm static scan/verdict state. Be careful when editing `references/threat-model.md`; defensive payload labels can affect static scanners.
