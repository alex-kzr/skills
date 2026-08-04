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

1. **Find the next open task.** Open `docs/kanban.md` and the plan file (`docs/plans/YYYY-MM-DD-<plan-name>.md`). Pick the topmost task under "To Do" that belongs to this plan and has no unmet dependency (earlier tasks in its phase are already "Done").

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

3. **Carry the resolved task(s) into the Execution Workflow below.** For a multi-task session (same-session / whole-phase), repeat steps 4–9 of the workflow for each task in order, inside the same session, before moving to the next phase.

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
    * Purpose
    * Requirements
    * Definition of Done

7. Implement the task

8. Validate:

    * Follow all specs from task

9. Update:

    * Move task to "Done" in `docs/kanban.md`
    * Update status in `docs/plans/tasks/{task-id}_{task-short-name}.md`
    * Remove the task's lease at `docs/.agents/locks/{task-id}.lock`

10. Repeat to next task

---

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

---

## If Blocked

* Document the issue in the task file
* Remove the task's lease at `docs/.agents/locks/{task-id}.lock`
* Move task back to "To Do"
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
