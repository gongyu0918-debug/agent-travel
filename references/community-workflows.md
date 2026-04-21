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
- Why it matters: this models the small-scope scheduled maintenance path where one advisory hint is valuable and a broader research crawl would be waste.

## 6. Hermes repeated-fingerprint dedupe

- Official sources:
  - [Hermes automation templates](https://hermes-agent.nousresearch.com/docs/guides/automation-templates)
  - [Hermes skills system docs](https://hermes-agent.nousresearch.com/docs/user-guide/features/skills)
- Community source: [Hermes ecosystem page](https://get-hermes.ai/community/)
- Workflow: a recurring scheduled workflow hits the same fingerprint again while the last advisory note is still fresh.
- Why it matters: this tests whether the host can skip redundant travel and keep scheduled research cheap.

## 7. Claude Code scheduled log collection

- Official source: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Community source: [Production error-log scheduled task thread](https://www.reddit.com/r/ClaudeAI/comments/1s32n1t/i_set_up_a_claude_code_scheduled_task_that/)
- Workflow: a scheduled task pulls production logs on a cadence and should return one reviewable hint for the next fix session instead of writing broad autonomous state.
- Why it matters: this covers scheduled data collection and shows how `agent-travel` should stay narrow even when the input is a high-volume operational feed.

## 8. Claude Code manual scheduled `CLAUDE.md` refresh

- Official source: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Community sources:
  - [Scheduled Claude Code workflows thread](https://www.reddit.com/r/claude/comments/1s4q0em/scheduled_claude_code/)
  - [My CLAUDE.md is always stale by the time I need it](https://www.reddit.com/r/ClaudeAI/comments/1rkya1a/my_claudemd_is_always_stale_by_the_time_i_need_it/)
- Workflow: the operator manually creates a recurring task that refreshes `CLAUDE.md` or codebase notes and wants that original task intent to survive scheduling.
- Why it matters: this is the cleanest contrast case for scheduled prompt handling: host-generated prompts stay neutral, while manually authored scheduled prompts can keep the operator's wording.

## 9. Claude Code generated scheduled prompt neutrality guard

- Official source: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Community source: [Loop and scheduled-task discussion](https://www.reddit.com/r/ClaudeCode/comments/1rn94wp/claude_code_just_shipped_loop_schedule_recurring/)
- Workflow: the host automatically materializes a scheduled prompt from workflow state and must not carry over the emotional tone of the original foreground thread.
- Why it matters: this is the key safety boundary for cron-like background runs that are derived from system facts instead of a fresh user prompt.

## 10. OpenClaw cron research digest

- Official sources:
  - [Automation & Tasks](https://docs.openclaw.ai/automation)
  - [Cron vs Heartbeat](https://docs.openclaw.ai/cron-vs-heartbeat/)
- Community source: [Crons don’t work on VPS](https://www.reddit.com/r/clawdbot/comments/1r21alk/crons_dont_work_on_vps/)
- Workflow: a daily cron job sends a research digest at an exact time and should keep that work isolated, reviewable, and separate from heartbeat context.
- Why it matters: this covers exact-time scheduled research, isolated execution, and the handoff from a cron digest into the next active thread.

## 11. OpenClaw daily summary collection

- Official sources:
  - [Automation & Tasks](https://docs.openclaw.ai/automation)
  - [Cron Jobs](https://docs.openclaw.ai/cron/)
- Community source: [How do you implement daily summarizations in claw?](https://www.reddit.com/r/openclaw/comments/1s291c6/how_do_you_implement_daily_sumarizations_in_claw/)
- Workflow: a recurring summary job collects recent conversations into a daily log and needs one bounded advisory hint about chunking, time windows, and append-only output.
- Why it matters: this is a real information-collection and digest workflow where data boundaries and time-window control matter more than code remediation.

## 12. Hermes nightly backlog triage digest

- Official source: [Hermes automation templates](https://hermes-agent.nousresearch.com/docs/guides/automation-templates)
- Community sources:
  - [Hermes Web UI overview](https://get-hermes.ai/)
  - [Hermes ecosystem page](https://get-hermes.ai/community/)
- Workflow: a nightly recurring job collects new issues or backlog items and wants one reviewable hint for the next maintenance thread.
- Why it matters: this covers scheduled backlog collection and shows how the skill should stay tied to one maintenance workflow instead of drifting into broad repo analysis.

## 13. Claude Code scheduled-job health audit

- Official source: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Community source: [I audited my always-on AI agent. 6 of 10 cron jobs had silently stopped running](https://www.reddit.com/r/ClaudeAI/comments/1srnkda/i_audited_my_alwayson_ai_agent_6_of_10_cron_jobs/)
- Workflow: a host-managed scheduled audit checks whether recurring jobs still produce timely output and leaves one receipt-first note for the next maintenance pass.
- Why it matters: this covers cron reliability, last-success markers, and the operational side of scheduled agents instead of only the "what should the prompt say" path.

## 14. Claude Code weekly reference-sheet refresh

- Official source: [Claude Code scheduled tasks](https://code.claude.com/docs/en/scheduled-tasks)
- Community source: [Printable Claude Code cheat sheet (auto-updated weekly)](https://www.reddit.com/r/ClaudeAI/comments/1rrm9ud/printable_claude_code_cheat_sheet_autoupdated/)
- Workflow: a weekly scheduled run refreshes a reference sheet or cheat sheet from current docs and workflow notes, then returns one bounded update note for the next review session.
- Why it matters: this covers recurring资料收集 and artifact refresh workflows where the right output is a small delta note instead of a full rewrite.

These cases are encoded in [community_workflow_cases.json](../assets/community_workflow_cases.json) and exercised by [community_smoke_test.py](../scripts/community_smoke_test.py).
