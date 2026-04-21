# Search Playbook

Use this file when `agent-travel` needs to turn local context into a safe search plan.

Default behavior:

- `search_mode = low`
- `tool_preference = public-only`
- `thread_scope = active_conversation_only`
- `active_conversation_window = 24h`
- `quiet_after_user_action = 20m`
- `quiet_after_agent_action = 5m`
- `repeat_fingerprint_cooldown = 12h`
- `max_runs_per_thread_per_day = 1`
- `max_runs_per_user_per_day = 3`
- `visibility = silent_until_relevant`

Use public search surfaces by default. Expand to private or internal search surfaces only when the user explicitly asks for that scope.

## Problem Fingerprint

Build the smallest fingerprint that still distinguishes the issue:

- `system`: host agent and relevant subsystem
- `version`: product, library, or runtime version
- `symptom`: what is failing
- `error_fragment`: 5-20 words from the most stable error text
- `attempted_fixes`: short list of what already failed
- `constraints`: platform, policy, budget, or safety limits
- `goal`: what would count as a useful hint on the next task

Do not include secrets, full file contents, customer data, private repo names when not public, long private paths, or raw tokens.

If the current fingerprint hash matches the last stored fingerprint hash and the previous run is still inside `repeat_fingerprint_cooldown`, skip the trip and reuse the existing advisory note until the cooldown or TTL expires.

## Micro-Travel Query Policy

- `low`: 1 query, `primary` first, keep at most 1 suggestion
- `medium`: up to 3 queries, `primary + 2 secondary` surfaces, keep at most 3 suggestions
- `high`: up to 5 queries, `primary + secondary + limited tertiary`, keep at most 5 suggestions

Use version labels whenever the toolchain moves quickly.

## Do Not Include In Search Query

- secrets
- private repo names when not public
- private file paths
- customer names
- full code blocks
- auth tokens
- internal URLs

## Search Coverage Matrix

- `primary`: official docs, release notes, official discussions
- `secondary`: search engines, GitHub issues, Stack Overflow
- `tertiary`: forums, blogs, social media

- `low`: `primary` only, or `primary + 1 secondary` when the problem is ambiguous
- `medium`: `primary + any 2 secondary surfaces`, add `tertiary` only when secondary recall is weak
- `high`: `primary + any 2 secondary surfaces + up to 2 tertiary surfaces`

## Source Order

1. `primary`: official documentation
2. `primary`: official release notes or changelogs
3. `primary`: official issue trackers or discussions
4. `secondary`: search engines for broader discovery
5. `secondary`: GitHub issues, Stack Overflow, or maintained Q&A posts with version details
6. `tertiary`: forum threads, blog posts, social summaries, and chat-community workaround signals

For every kept suggestion, at least 1 evidence item from `primary` is mandatory.

## Distillation Frame

Every kept suggestion must define:

- `solves_point`
- `new_idea`
- `fit_reason`
- `match_reasoning`
- `version_scope`
- `do_not_apply_when`
