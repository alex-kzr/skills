---
name: board-task-executor
description: Cycle through tasks from a task board, executing them as they are ready, and moving them through the board as they are completed, ensuring requirements and definition of done are met.
---

# SKILL: board-task-executor

## Description

This skill defines how an autonomous coding agent executes tasks from a task board, ensuring consistent progress, validation, and system stability.

---

## Behavior

You are an autonomous coding agent.

---

## Resolving Task(s) When Only a Plan Is Given

If the user specifies which plan to execute but does not specify a phase or task, resolve what to work on before starting the Execution Workflow:

1. **Find the next open task.** Open `docs/kanban.md` and the plan file (`docs/plans/YYYY-MM-DD-<plan-name>.md`). Pick the topmost task under "To Do" that belongs to this plan and has no unmet dependency.

    A task's dependencies are whatever its `## Execution Metadata` → `Depends on` field names (see [Task Metadata and Scope](#task-metadata-and-scope)). When a task file has no such block, fall back to position: earlier tasks in its phase must already be "Done". Never treat a dependency as met because it *looks* finished — it must be "Done" on the board.

2. **Check the phase's Execution tag** in the plan file (see [writing-plans → Execution Mode Guidance](../writing-plans/SKILL.md#execution-mode-guidance)) to decide the scope of this session:

    | Execution tag | What to do |
    |---|---|
    | **separate** (default, no tag) | Work on that ONE task only in this session. |
    | **parallel: `<IDs>`** | The task belongs to a parallel group. Dispatch each task in the group to its own subagent/session at the same time (same starting context), then continue once they land. |
    | **same-session: `<IDs>`** | The task is coupled to the other listed IDs. Pull ALL of them into this session and execute sequentially, one after another, without stopping in between. |
    | **whole-phase: same-session** | Pull EVERY task of that phase into this session and execute sequentially. |

    When dispatching to a separate subagent/session (`parallel`, or delegation via
    [delegation-patterns](../delegation-patterns/SKILL.md)), build its prompt from the
    [Standard Subagent Prompt Envelope](../references/subagent-prompt-envelope.md) so it
    receives explicit context, execution mode, and reporting rules.

3. **Carry the resolved task(s) into the Execution Workflow below.** For a multi-task session (same-session / whole-phase), repeat steps 4–9 of the workflow for each task in order, applying step 9 only when this session is the human-directed board runner rather than an orchestrated executor.

---

## Execution Workflow

Repeat the following loop:

1. **Analyze input data** — read `docs/*`

2. Open `docs/kanban.md`

3. Select the task(s) to work on — the TOP task from "To Do", or the set resolved via [Resolving Task(s) When Only a Plan Is Given](#resolving-tasks-when-only-a-plan-is-given) if only a plan was specified

4. Before moving it to "In Progress", create its lease at `docs/.agents/locks/{task-id}.lock` (see [Task Leases](#task-leases-parallel-safety)). Then move it to "In Progress" and update status in `docs/plans/tasks/{task-id}_{task-short-name}.md`

5. Open corresponding task file in `docs/plans/tasks/{task-id}_{task-short-name}.md`

6. Read and understand:

    * Plan
    * Execution Metadata — type, executor, dependencies, allowed scope, out of scope, required skills, verification commands
    * Purpose
    * Requirements
    * Acceptance Criteria (or Definition of Done in older task files)

    Load every skill listed under `Required skills` before writing anything.

7. Implement the task — writing only inside `Allowed scope`

8. Validate:

    * Run every entry under `Verification commands` from its declared working directory, one at a time, and record the exact command and its exit code
    * Follow all specs from task

9. Update:

    * If you are running the board directly for a human, with no orchestrator and no independent verifier:
      move task to "Done" in `docs/kanban.md`, update status in `docs/plans/tasks/{task-id}_{task-short-name}.md`, and remove the lease at `docs/.agents/locks/{task-id}.lock`
    * If you are running under an orchestrator or pipeline runner:
      leave the board and `## Status` unchanged, keep or hand off the lease according to the orchestrator's policy, and stop at the terminal state `implemented`

10. Repeat to next task

---

## Task Metadata and Scope

Newer task files carry an `## Execution Metadata` block between `## Status` and `## Purpose`
(format: [writing-plans → Task Metadata](../writing-plans/SKILL.md#task-metadata-machine-readable);
in a project that publishes its own contract, that document governs — in oxidium-forge it is
`docs/agents/task-metadata-contract.md`).

Treat it as binding, not advisory:

| Field | What it obliges you to do |
|---|---|
| `Type`, `Executor` | Confirm you are the right executor. If the task names an executor you are not, stop and say so instead of proceeding. |
| `Depends on` | Do not start until every listed task is "Done". `none` means no dependency. |
| `Allowed scope` | Write only inside these paths. A needed change outside them is an out-of-scope discovery, not a licence to expand. |
| `Out of scope` | Never write here, even if `Allowed scope` looks like it might overlap. |
| `Required skills` | Read every listed `SKILL.md` before implementing. |
| `Maximum repair attempts` | After this many failed verification rounds the task is blocked, not retried again. |
| `Documentation impact` | The documents this task is expected to change. `none` means the task is documentation-neutral. |
| `Verification commands` | Run each one from its declared working directory, sequentially, and report the exact command plus its exit code. Never report a command you did not run. |
| `Blocking conditions` | Preconditions outside the repository. If one is unmet, the task is blocked — see [If Blocked](#if-blocked). |

A task file with no metadata block is a historical task: fall back to `## Affected Files /
Components` for scope, board position for dependencies, and `## Definition of Done` for
criteria. **Do not add a metadata block to an old task file just to make it uniform.**

## Verification Ownership and the `implemented` Handoff

**You never verify your own work.** Running the task's verification commands is part of
implementing; it is not verification. Verification is a separate, independent judgement made by
someone with fresh context comparing the diff against the acceptance criteria.

- Leave every `AC-n` checkbox unticked. Ticking one records a verifier's finding, and you are
  not the verifier.
- Report evidence, not conclusions: the commands you ran, their working directories, their exit
  codes, and the files you changed. Do not claim a check passed without showing the command that
  proves it.
- When you are running under an orchestrator (dispatched as a subagent, or driven by a pipeline
  runner), your terminal state is **`implemented`**, not "Done": implement, validate, report, and
  stop. The orchestrator dispatches verification and only then moves the card. Do not edit the
  board or the `## Status` checkboxes to "Done" yourself in that mode, and do not write to run
  state — you have no write path to it.
- When you are running the board directly for a human, with no orchestrator and no independent
  verifier, step 9 below is yours to perform — say plainly in your report that the task was
  self-validated and received no independent verdict.

## Task Leases (Parallel Safety)

When multiple agents/sessions may pull from the same `docs/kanban.md` (e.g. `parallel` execution mode, or several agents working the same board), use a lightweight lease file to avoid two agents picking up the same task.

Lease path:

```text
docs/.agents/locks/{task-id}.lock
```

Lease contents:

```markdown
# {TASK_ID} Lease

- Agent:
- Session:
- Started:
- Plan:
- Task:
```

Rules:

* Before moving a task to "In Progress", create its lease file.
* If a fresh lease already exists for another active agent/session, do NOT take that task — pick the next eligible one instead.
* Remove the lease when the task moves to "Done".
* If blocked (see [If Blocked](#if-blocked)), document the blocker in the task file and remove the lease before moving the task back to "To Do".

This is guidance, not a locking system — it does not require a lock server, retries, or expiry logic. Treat a stale-looking lease from a dead session as a judgment call: confirm with the user before taking it over.

---

## Rules

* Only ONE task can be "In Progress" at a time per session, EXCEPT when the resolved Execution mode is `parallel` (separate sessions, one task each), `same-session`, or `whole-phase: same-session` — in those cases the resolved group's tasks move to "In Progress" together and are worked through as described above
* Do NOT skip tasks
* Do NOT reorder tasks unless explicitly instructed
* Do NOT modify task scope
* Do NOT write outside the task's `Allowed scope`, and never inside its `Out of scope`
* Do NOT mark your own work verified — see [Verification Ownership](#verification-ownership-and-the-implemented-handoff)
* Do NOT add or rewrite metadata in historical task files

---

## If Blocked

* Document the issue in the task file under a `## Blockers` section — what was attempted, what failed, the exact command and exit code if any, and what would unblock it
* Remove the task's lease at `docs/.agents/locks/{task-id}.lock`
* Move task back to "To Do"
* Do NOT start a task that lists the blocked task under `Depends on` — a blocked dependency blocks its dependents too
* Optionally create a new task describing the blocker

---

## If New Work Is Discovered

* DO NOT extend current task
* Create a NEW task using skill [writing-plans](../writing-plans/SKILL.md)


---

## Stability Requirement

After EACH task:

* Project must remain runnable
* No broken functionality allowed
