---
name: pipeline-runtime-recovery
description: Use when a pipeline worker quota or adapter failure occurs.
---

# Pipeline Runtime Recovery

## Procedure

1. Inspect the runner-owned failure artifact and distinguish quota/authentication failures from task-verifier findings, test failures, and task-contract rejections.
2. Keep the existing run immutable. Do not resume a run with a different adapter: runtime selection is part of its identity.
3. When the requested Claude model returns a concrete quota-limit response, use a fresh Codex fallback run with the user-requested model and effort, on the same scoped branch and contract. Read its durable runner result before deciding what follows.
4. If that fallback is rejected by the task's own strict runtime boundary, preserve both runs. Do not relax isolation, edit runner state, or manufacture a completion.
5. When strict-isolation capability is the blocker, run a bounded live probe only after the user authorizes a concrete runtime/model and consumption budget. Probe the exact executable and CLI surface with a harmless out-of-workspace sentinel; record a positive capability only on actual enforced denial. An escape or unavailable nested surface is negative evidence: keep the capability UNKNOWN and reject strict launch.
6. If a negative probe prevents the same strict adapter from launching its LLM verifier, apply a human-approved in-task amendment before changing scope. Preserve the probe and failure evidence, then add a runner-owned deterministic verifier that validates the evidence and fail-closed rejection without starting the untrusted adapter.
7. Only with explicit user authorization, use direct Codex as a scoped fallback: restrict writes to the task's allowed scope, retain the runner's board/task projection, run every declared verification command, and record exact exits.
8. Report direct fallback as self-validated only. Leave the task active and require a future fresh independent pipeline-verifier pass before calling it verified, closing its board card, or claiming PASS/PASS.

## Pitfalls

- Probe actual model capacity before dispatch; login status proves authentication, not usable quota.
- Treat a verifier's quota message as an external orchestration block, not as a failed acceptance criterion; its already-recorded test evidence remains evidence but cannot replace the missing independent verdict.
- Never weaken a strict adapter-isolation rejection to make a fallback run; that converts a required safety boundary into an untracked exception.
