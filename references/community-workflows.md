# Community Workflows

These scenarios come from current official docs, public workflow discussions, and host-level background-automation patterns. They are used as product-oriented smoke cases for `agent-travel`.

## 1. Claude Code post-task guidance refresh

- Official source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- Community source: [Claude Code hooks workflow thread](https://www.reddit.com/r/ClaudeCode/comments/1qlzzzf/claude_codes_most_underrated_feature_hooks_wrote/)
- Workflow: after a multi-step coding task, the operator wants a quiet-window background pass that refreshes recent official guidance plus one community workflow note before the next similar turn.
- Why it matters: this is a realistic "research after task completion" workflow where silent inline interruption would be noise, while one later advisory hint is useful.

## 2. Claude Code failure-recovery contract check

- Official source: [Claude Code hooks reference](https://code.claude.com/docs/en/hooks)
- Community source: [Some hooks not working in Claude Code](https://www.reddit.com/r/ClaudeCode/comments/1rn8nxf/some_hooks_not_working_in_claude_code/)
- Workflow: repeated hook failures or silently ignored hook output trigger a recovery pass that checks the official event contract and one current community failure pattern.
- Why it matters: this models the "the hook is still broken and I need the next recovery attempt to aim at the real contract boundary" path.

## 3. OpenClaw heartbeat memory-safety advisory

- Official source: [OpenClaw Automation and Heartbeat docs](https://docs.openclaw.ai/automation)
- Community sources:
  - [Memory Master review on ClawHub](https://clawhub.ai/skills/memory-master)
  - [Mind Your HEARTBEAT!](https://arxiv.org/abs/2603.23064)
- Workflow: the operator uses heartbeat or similar background turns and wants lightweight research without turning that loop into silent memory pollution.
- Why it matters: this is the clearest real-world case for `advisory_only`, `thread_scope: active_conversation_only`, public-only search, and manual review gates.

## 4. OpenClaw idle fallback silence guardrail

- Official sources:
  - [Cron vs heartbeat](https://docs.openclaw.ai/cron-vs-heartbeat/)
  - [Heartbeat reference](https://docs.openclaw.ai/gateway/heartbeat)
- Workflow: the operator already has heartbeat enabled and wants idle fallback to stay off until they explicitly opt in.
- Why it matters: this tests the product-side promise that `agent-travel` stays quiet when the host already provides a stronger background trigger.

## 5. Hermes scheduled doc-drift scan

- Official sources:
  - [Hermes automation templates](https://hermes-agent.nousresearch.com/docs/guides/automation-templates)
  - [Hermes skills system docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- Community source: [Hermes ecosystem page](https://get-hermes.ai/community/)
- Workflow: the operator already uses skills and scheduled jobs, and wants a narrow recurring pass that checks documentation drift or workflow changes around one maintained skill flow.
- Why it matters: this models the low-budget scheduled maintenance path where one advisory hint is valuable and a broader research crawl would be waste.

## 6. Hermes repeated-fingerprint dedupe

- Official sources:
  - [Hermes automation templates](https://hermes-agent.nousresearch.com/docs/guides/automation-templates)
  - [Hermes skills system docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- Community source: [Hermes ecosystem page](https://get-hermes.ai/community/)
- Workflow: a recurring scheduled workflow hits the same fingerprint again while the last advisory note is still fresh.
- Why it matters: this tests whether the host can skip redundant travel and keep scheduled research cheap.

These cases are encoded in [community_workflow_cases.json](../assets/community_workflow_cases.json) and exercised by [community_smoke_test.py](../scripts/community_smoke_test.py).
