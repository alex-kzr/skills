---
name: kanban
description: "Kanban orchestration + worker lifecycle: decompose tasks, route to specialists, execute as workers. Load for both orchestrator and worker roles."
version: 3.0.0
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [kanban, multi-agent, orchestration, routing, collaboration, workflow, pitfalls]
    related_skills: [delegation-patterns, subagent-driven-development]
---

# Kanban — Orchestrator & Worker Guide

> The **core worker lifecycle** (6 steps: orient → work → heartbeat → block/complete) is auto-injected into every kanban process via the `KANBAN_GUIDANCE` system-prompt block. This skill provides the deeper playbook for both orchestrator routing and worker execution.

---

## Section 1: Orchestrator Playbook

### When to use the board (vs. just doing the work)

Create Kanban tasks when any of these are true:

1. **Multiple specialists are needed.** Research + analysis + writing is three profiles.
2. **The work should survive a crash or restart.** Long-running, recurring, or important.
3. **The user might want to interject.** Human-in-the-loop at any step.
4. **Multiple subtasks can run in parallel.** Fan-out for speed.
5. **Review / iteration is expected.** A reviewer profile loops on drafter output.
6. **The audit trail matters.** Board rows persist in SQLite forever.

If *none* of those apply — it's a small one-shot reasoning task — use `delegate_task` instead or answer the user directly.

### The anti-temptation rules

- **Do not execute the work yourself.** Your restricted toolset usually doesn't even include terminal/file/code/web.
- **For any concrete task, create a Kanban task and assign it.** Every single time.
- **If no specialist fits, ask the user which profile to create.**
- **Decompose, route, and summarize — that's the whole job.**

### The standard specialist roster (convention)

| Profile | Does | Typical workspace |
|---|---|---|
| `researcher` | Reads sources, gathers facts, writes findings | `scratch` |
| `analyst` | Synthesizes, ranks, de-dupes | `scratch` |
| `writer` | Drafts prose in the user's voice | `scratch` or `dir:` into Obsidian vault |
| `reviewer` | Reads output, leaves findings, gates approval | `scratch` |
| `backend-eng` | Writes server-side code | `worktree` |
| `frontend-eng` | Writes client-side code | `worktree` |
| `ops` | Runs scripts, manages services, deployments | `dir:` into ops scripts repo |
| `pm` | Writes specs, acceptance criteria | `scratch` |

### Decomposition playbook

**Step 1 — Understand the goal.** Ask clarifying questions if ambiguous.

**Step 2 — Sketch the task graph** (in your response to the user, before creating anything):
```
T1  researcher        research: Postgres cost vs current
T2  researcher        research: Postgres performance vs current
T3  analyst           synthesize migration recommendation       parents: T1, T2
T4  writer            draft decision memo                       parents: T3
```

**Step 3 — Create tasks and link:**
```python
t1 = kanban_create(title="research: Postgres cost vs current", assignee="researcher", body="...", tenant=os.environ.get("HERMES_TENANT"))["task_id"]
t2 = kanban_create(title="research: Postgres performance vs current", assignee="researcher", body="...")["task_id"]
t3 = kanban_create(title="synthesize migration recommendation", assignee="analyst", body="...", parents=[t1, t2])["task_id"]
t4 = kanban_create(title="draft decision memo", assignee="writer", body="...", parents=[t3])["task_id"]
```

`parents=[...]` gates promotion — children stay in `todo` until every parent reaches `done`.

**Step 4 — Complete your own task** with `kanban_complete(summary=..., metadata={...})`.

**Step 5 — Report back to the user** in plain prose.

### Common patterns

- **Fan-out + fan-in:** N researchers → 1 analyst with all as parents.
- **Pipeline with gates:** pm → backend-eng → reviewer. Each stage's `parents=[previous_task]`.
- **Same-profile queue:** 50 tasks, all assigned to `translator`, serialized by dispatcher.
- **Human-in-the-loop:** Any task can `kanban_block()` to wait for input.

### Pitfalls

- **Reassignment vs. new task.** If reviewer blocks with "needs changes," create a NEW task — don't re-run the same one.
- **Argument order for links.** `kanban_link(parent_id=..., child_id=...)` — parent first.
- **Don't pre-create the whole graph if shape depends on intermediate findings.** Orchestrators can spawn orchestrators.
- **Tenant inheritance.** Pass `tenant=os.environ.get("HERMES_TENANT")` on every `kanban_create`.

### Recovering stuck workers

1. **Reclaim** (`hermes kanban reclaim <task_id>`) — abort and reset to `ready`.
2. **Reassign** (`hermes kanban reassign <task_id> <new-profile> --reclaim`) — switch profile.
3. **Change profile model** — edit profile config on disk, then Reclaim to retry.

---

## Section 2: Worker Guide

### Workspace handling

| Kind | What it is | How to work |
|---|---|---|
| `scratch` | Fresh tmp dir, yours alone | Read/write freely; GC'd when task archived. |
| `dir:<path>` | Shared persistent directory | Other runs will read what you write. |
| `worktree` | Git worktree at resolved path | If `.git` doesn't exist, run `git worktree add` first. Commit work here. |

### Tenant isolation

If `$HERMES_TENANT` is set, prefix memory entries with the tenant so context doesn't leak.

### Good summary + metadata shapes

**Coding task:**
```python
kanban_complete(summary="shipped rate limiter — token bucket, 14 tests pass",
    metadata={"changed_files": ["rate_limiter.py", "tests/test_rate_limiter.py"], "tests_passed": 14})
```

**Research task:**
```python
kanban_complete(summary="3 libraries reviewed; vLLM wins on throughput",
    metadata={"sources_read": 12, "recommendation": "vLLM"})
```

**Review task:**
```python
kanban_complete(summary="reviewed PR #123; 2 blocking issues",
    metadata={"pr_number": 123, "approved": False, "findings": [...]})
```

### Claiming cards you actually created

Only list ids captured from successful `kanban_create` return values. Never invent ids or claim cards another worker created. The kernel verifies each id; phantom ids block completion.

### Block reasons that get answered fast

Bad: `"stuck"`. Good: one sentence naming the specific decision. Leave longer context as a comment via `kanban_comment()`.

### Heartbeats worth sending

Good: `"epoch 12/50, loss 0.31"`, `"scanned 1.2M/2.4M rows"`. Bad: `"still working"`, empty notes. Every few minutes max; skip for tasks under ~2 minutes.

### Retry scenarios

If `kanban_show` returns `runs: [...]` with closed runs, you're a retry. Read prior outcomes:
- `timed_out` — chunk the work or shorten it.
- `crashed` — OOM or segfault. Reduce memory footprint.
- `spawn_failed` — profile config issue. Block for human help.
- `reclaimed` — operator archived task. Check status carefully.
- `blocked` — previous attempt blocked; unblock comment should be in thread.

### Do NOT

- Call `delegate_task` as substitute for `kanban_create`. `delegate_task` is for short reasoning subtasks; `kanban_create` is for cross-agent handoffs.
- Modify files outside `$HERMES_KANBAN_WORKSPACE` unless task body says to.
- Create follow-up tasks assigned to yourself — assign to the right specialist.
- Complete a task you didn't finish. Block instead.

### CLI fallback (for scripting)

Every tool has a CLI equivalent: `hermes kanban show|complete|block|create|...`. Use tools from inside agent; CLI for human at terminal.
