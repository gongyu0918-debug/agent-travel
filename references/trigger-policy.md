# Trigger Policy

Use this file when `agent-travel` needs a host-side policy for quiet, low-noise background runs.

## Trigger Priority

1. `heartbeat`
2. `failure_recovery`
3. `task_end`
4. `scheduled`
5. `idle_fallback`

## Quiet Conditions

Run only when all of these are true:

- no user operation in progress
- no agent response in progress
- no tool approval pending
- active conversation within `24h`

## Default Cooldowns

- `active_conversation_window = 24h`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `repeat_fingerprint_cooldown = 12h`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`

## Escalation Rules

- `low`: normal heartbeat, scheduled, or idle micro-travel
- `medium`: 2 related failures, 2 user corrections, 1 unresolved blocker, or version mismatch
- `high`: explicit deep research request or repeated blocker after `medium`

`task_end` defaults to `medium` once the host decides the task just finished and the quiet window is open.

`idle_fallback` should run only when one of these is true:

- the host does not support heartbeat
- the operator explicitly enabled idle fallback
- the operator explicitly prefers inactivity-based travel

Repeated runs with the same fingerprint should stay quiet until `repeat_fingerprint_cooldown` elapses.

## Host Note

If the host cannot observe live typing or direct user activity, approximate quiet conditions with:

- `last_user_action`
- `last_agent_action`
- pending tool state
- whether the agent is actively responding

For `scheduled` triggers, distinguish manual prompts from host-generated prompts:

- manual scheduled prompts may preserve the operator's original wording
- host-generated scheduled prompts should stay neutral and workflow-derived
- generated scheduled prompts should be built from repo state, logs, backlog items, docs drift, or other task facts
