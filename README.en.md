# agent-travel

The second law of thermodynamics says a closed system drifts toward entropy. Agents do too. An agent that stays trapped inside the same tools, the same context window, and the same stale assumptions will slowly confuse repetition with truth. `agent-travel` gives it a low-noise micro-travel loop: step out only during heartbeat, task wrap-up, failure recovery, scheduled windows, or idle fallback, then bring back what is still useful for the current problem.

It is not a noisy background crawler and it does not make decisions for the user. It compresses outside practice into advisory-only hints, stores them in an isolated channel, and surfaces them only when the next relevant task appears.

## Why It Is Lightweight

- No daemon. Scheduling stays with the host agent through heartbeat, cron, task-end, or failure hooks.
- No database. State stays in a lightweight `state.json`, and hints stay in an isolated `suggestions.md`.
- Public search surfaces are the default. Internal docs, private connectors, and private repos require explicit user opt-in.
- Every script uses Python stdlib only.
- Search is executed by the host tools. This repository defines triggers, contracts, validation, and host adapters.
- The suggestion channel stays isolated. It does not write into the core system prompt, persona, long-term memory, or core AGENT.md/agent.md instructions.

## Recommended Default

The recommended default is low-frequency, low-budget, and silent by design.

- `active_conversation_window = 24h`
- `default_search_mode = low`
- `tool_preference = public-only`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`
- `visibility = silent_until_relevant`

`medium` and `high` are escalation modes, not the everyday background default.

## Key Points

- Search uses three tiers: `primary` for official docs, release notes, and official discussions; `secondary` for search engines, GitHub issues, and Stack Overflow; `tertiary` for forums, blogs, and social media.
- Every suggestion is cross-validated. At least 1 `primary` evidence item is mandatory.
- Every kept suggestion must include `match_reasoning`, with axis-by-axis notes explaining why it matched at least 4 of the 5 axes.
- Output is always advisory-only and scoped to `active_conversation_only`.
- The host should invoke it only inside a quiet window: no user operation, no agent output in progress, and no pending tool approval.

## Do Not Use This For

- Autonomous command execution from web pages.
- Private-data search without explicit user opt-in.
- Permanent memory, persona, or core-instruction mutation.
- Replacing user decisions.

## Companion Skill

`agent-travel` is the single-node background research layer today. It pairs with the same author's [agent-compute-mesh](https://github.com/gongyu0918-debug/agent-compute-mesh): this skill compresses outside practice into structured hints, while the mesh skill turns similar `exploration job` units into stricter execution leases.

## Files

- [SKILL.md](SKILL.md)
- [SKILL.en.md](SKILL.en.md)
- [agents/openai.yaml](agents/openai.yaml)
- [agents/openclaw.yaml](agents/openclaw.yaml)
- [agents/hermes.yaml](agents/hermes.yaml)
- [references/search-playbook.md](references/search-playbook.md)
- [references/suggestion-contract.md](references/suggestion-contract.md)
- [references/trigger-policy.md](references/trigger-policy.md)
- [references/threat-model.md](references/threat-model.md)
- [references/host-adapters.md](references/host-adapters.md)
- [scripts/validate_suggestions.py](scripts/validate_suggestions.py)
- [scripts/should_travel.py](scripts/should_travel.py)
- [scripts/reliability_test_suggestions.py](scripts/reliability_test_suggestions.py)
- [scripts/ablation_test_suggestions.py](scripts/ablation_test_suggestions.py)
- [assets/reliability_report.json](assets/reliability_report.json)
- [assets/ablation_report.json](assets/ablation_report.json)
