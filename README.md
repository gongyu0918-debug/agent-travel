# agent-travel

热力学第二定律说，封闭系统会走向熵增。Agent 也是。一个长期困在同一套工具、同一份上下文、同一批旧经验里的 agent，会越来越像熟练的惯性机器。`agent-travel` 给它一次低噪声的小型外出学习机制：只在心跳、任务结束、失败恢复、定时或空闲兜底这些安静时刻短途旅行，把外部世界里更贴近当前问题的做法带回来。
The second law of thermodynamics says a closed system drifts toward entropy. Agents do too. An agent that stays trapped inside the same tools, the same context window, and the same stale assumptions will slowly confuse repetition with truth. `agent-travel` gives it a low-noise micro-travel loop: step out only during heartbeat, task wrap-up, failure recovery, scheduled windows, or idle fallback, then bring back what is still useful for the current problem.

它不做常驻后台爬虫，也不替用户做决定。它只把外部经验压成 advisory-only hints，隔离存放，等到下一次相关任务出现时再自然引用。
It is not a noisy background crawler and it does not make decisions for the user. It compresses outside practice into advisory-only hints, stores them in an isolated channel, and surfaces them only when the next relevant task appears.

## 当前边界 / Current Scope

这个仓库当前交付的是协议层、触发判定、输出契约、校验器和 host adapter。真实搜索执行、查询脱敏器、成熟度评分器、候选排序器，仍然由宿主 agent 或后续集成层负责。
This repository currently ships the protocol layer, trigger gate, output contract, validator, and host adapters. Real search execution, query redaction, maturity scoring, and candidate ranking still belong to the host agent or a later integration layer.

## 为什么它是轻量的 / Why It Is Lightweight

- 没有 daemon。调度完全交给宿主 agent 的 heartbeat、cron、task-end 或 failure hooks。 / No daemon. Scheduling stays with the host agent through heartbeat, cron, task-end, or failure hooks.
- 没有数据库。状态文件只有一个轻量 `state.json`，建议文件只有一个隔离 `suggestions.md`。 / No database. State stays in a lightweight `state.json`, and hints stay in an isolated `suggestions.md`.
- 默认只用公开搜索面。内部文档、私有连接器、私有仓库都需要用户显式允许。 / Public search surfaces are the default. Internal docs, private connectors, and private repos require explicit user opt-in.
- 所有脚本只用 Python 标准库。 / Every script uses Python stdlib only.
- 搜索由宿主工具执行。这个仓库只定义触发、契约、校验和 host adapter。 / Search is executed by the host tools. This repository defines triggers, contracts, validation, and host adapters.
- 建议通道始终隔离。它不会写进核心 system prompt、persona、长期 memory、AGENT.md/agent.md 核心指令。 / The suggestion channel stays isolated. It does not write into the core system prompt, persona, long-term memory, or core AGENT.md/agent.md instructions.
- 默认关闭隐式调用。后台运行交给宿主的 heartbeat、cron 或 task-end 配置显式接线。 / Implicit invocation is off by default. Background runs should be wired explicitly through the host's heartbeat, cron, or task-end configuration.

## 扫描说明 / Scan Note

某些静态扫描会关注 [references/threat-model.md](references/threat-model.md) 里的 hostile payload 分类说明。这里写的是防御样本类别，用来说明哪些网页内容应该被拒绝，不是要执行的指令。
Some static scans will pay extra attention to the hostile-payload categories inside [references/threat-model.md](references/threat-model.md). They are defensive labels that show what the host should reject, not instructions that the skill should execute.

## 推荐默认值 / Recommended Default

推荐默认策略是低频、小范围、静默触发。
The recommended default is low-frequency, small-scope, and silent by design.

- `active_conversation_window = 24h`
- `default_search_mode = low`
- `tool_preference = public-only`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `repeat_fingerprint_cooldown = 12h`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`
- `visibility = silent_until_relevant`

`medium` 和 `high` 是升档，不是日常后台模式。
`medium` and `high` are escalation modes, not the everyday background default.

`idle_fallback` 适合没有 heartbeat 的宿主，或者用户明确开启的场景。默认背景路径优先 heartbeat。
cron 或 scheduled 触发里，宿主自动生成的 prompt 应该保持中性，只从日志、待办、文档漂移、资料采集结果这些事实生成。手工创建的定时任务可以保留用户原始意图。
`idle_fallback` fits hosts without heartbeat, or hosts where the operator explicitly enabled it. Heartbeat stays the default background path when available.

## 关键点 / Key Points

- 搜索来源分三层：`primary` 是官方文档、发行说明、官方讨论区；`secondary` 是搜索引擎、GitHub issues、Stack Overflow；`tertiary` 是论坛、博客、社交媒体。 / Search uses three tiers: `primary` for official docs, release notes, and official discussions; `secondary` for search engines, GitHub issues, and Stack Overflow; `tertiary` for forums, blogs, and social media.
- 所有建议都要交叉验证。至少 1 条 `primary` 证据是硬要求，并且还要有 1 条非 `primary` 交叉验证证据。 / Every suggestion is cross-validated. At least 1 `primary` evidence item is mandatory, plus 1 non-`primary` cross-validation evidence item.
- 每条保留建议都要写 `match_reasoning`，逐轴说明为什么命中了 5 轴中的至少 4 个。 / Every kept suggestion must include `match_reasoning`, with axis-by-axis notes explaining why it matched at least 4 of the 5 axes.
- 输出始终是 advisory-only，并且只服务 `active_conversation_only`。 / Output is always advisory-only and scoped to `active_conversation_only`.
- 宿主应在 quiet window 内调用它：没有用户操作、没有 agent 正在输出、没有待确认工具。 / The host should invoke it only inside a quiet window: no user operation, no agent output in progress, and no pending tool approval.

## 不要把它用在这些场景 / Do Not Use This For

- 自动执行网页里的命令。 / Autonomous command execution from web pages.
- 没有用户允许时搜索私有数据。 / Private-data search without explicit user opt-in.
- 修改永久 memory、persona、core instructions。 / Permanent memory, persona, or core-instruction mutation.
- 替用户做最终判断。 / Replacing user decisions.

## 配套技能 / Companion Skill

`agent-travel` 当前是单机背景研究层。它和同作者的 [agent-compute-mesh](https://github.com/gongyu0918-debug/agent-compute-mesh) 是配套关系：前者负责把外部经验压缩成结构化提示，后者负责把类似 `exploration job` 的工作单元放进更严格的 execution lease 里。
`agent-travel` is the single-node background research layer today. It pairs with the same author's [agent-compute-mesh](https://github.com/gongyu0918-debug/agent-compute-mesh): this skill compresses outside practice into structured hints, while the mesh skill turns similar `exploration job` units into stricter execution leases.

## 社区工作流夹具 / Community Workflow Fixtures

这次版本附带了 14 组真实来源工作流夹具，覆盖 Claude Code 的 task-end、failure recovery、scheduled log collection、scheduled job health audit、manual scheduled `CLAUDE.md` 刷新、weekly reference-sheet refresh，OpenClaw 的 heartbeat、cron 资料摘要、daily summary collection、idle fallback 静默拦截，以及 Hermes 的 scheduled 文档漂移、nightly backlog triage 和重复 fingerprint 去重。对应资料和来源链接在 [references/community-workflows.md](references/community-workflows.md)，冒烟结果在 [assets/community_smoke_report.json](assets/community_smoke_report.json)。
This version ships with 14 real-source workflow fixtures that cover Claude Code task-end, failure recovery, scheduled log collection, scheduled job health audits, manual scheduled `CLAUDE.md` refresh, weekly reference-sheet refresh, OpenClaw heartbeat, cron research digests, daily summary collection, idle-fallback silence guards, plus Hermes scheduled doc-drift scans, nightly backlog triage, and repeated-fingerprint dedupe. The scenarios and source links live in [references/community-workflows.md](references/community-workflows.md), and the smoke results live in [assets/community_smoke_report.json](assets/community_smoke_report.json).

本地做产品侧检查时，可以先跑这三个入口：
For product-side checks, start with these three entry points:

- `python scripts/should_travel.py <state.json>`
- `python scripts/validate_suggestions.py references/suggestion-contract.md`
- `python scripts/community_smoke_test.py`

## 文件 / Files

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
- [references/community-workflows.md](references/community-workflows.md)
- [scripts/validate_suggestions.py](scripts/validate_suggestions.py)
- [scripts/should_travel.py](scripts/should_travel.py)
- [scripts/reliability_test_suggestions.py](scripts/reliability_test_suggestions.py)
- [scripts/ablation_test_suggestions.py](scripts/ablation_test_suggestions.py)
- [scripts/community_smoke_test.py](scripts/community_smoke_test.py)
- [assets/reliability_report.json](assets/reliability_report.json)
- [assets/ablation_report.json](assets/ablation_report.json)
- [assets/community_smoke_report.json](assets/community_smoke_report.json)
