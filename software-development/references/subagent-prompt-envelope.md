# Subagent Prompt Envelope

A standard prompt shape for dispatching task-board work to a subagent, regardless of which
agent implementation runs it (Codex, Claude, Hermes `delegate_task`, or a plain CLI invocation).
Fresh subagents have no memory of the orchestrating session — the envelope exists so nothing
required to execute the task is left implicit.

Fill in every field. Omit a field only if the task genuinely has none (e.g. no `Plan file` for
ad-hoc work) — do not delete the label, leave the value blank instead.

## Envelope

```text
Context:
- Project root:
- Agents root:
- Required skills:
- Plan file:
- Task file:
- Kanban file:

Execution mode:
- separate | parallel | same-session | whole-phase

Task:
- Task ID:
- Task title:
- Expected scope:

Rules:
- Read required skills first.
- Read the task file before editing.
- Update task status and kanban status.
- Validate before moving to Done.
- Report changed files and validation commands.

Final report:
- Status:
- Files changed:
- Validation:
- Blockers:
```

## Field Notes

- **Project root** — the working directory the subagent should treat as project root (not the
  agents repo root).
- **Agents root** — where `.agents/` resolves to, so the subagent can load skills by relative
  path (see agent profiles under `agents/` for discovery details per agent).
- **Required skills** — explicit paths, e.g. `.agents/skills/software-development/board-task-executor/SKILL.md`.
  Do not assume the subagent will discover skills on its own.
- **Plan file / Task file / Kanban file** — explicit paths, following the canonical structure
  from [writing-plans](../writing-plans/SKILL.md#file-structure).
- **Execution mode** — one value from [board-task-executor's execution tags](../board-task-executor/SKILL.md#resolving-tasks-when-only-a-plan-is-given):
  `separate` (this task only), `parallel` (this task runs alongside sibling tasks in their own
  sessions), `same-session` (pull in the listed IDs and run sequentially), or `whole-phase`
  (pull in every task of the phase).
- **Expected scope** — a short boundary statement (files/modules expected to change) so the
  subagent can flag out-of-scope discoveries instead of silently expanding the task.

## Why a Fixed Envelope

- Removes ambiguity about which files a fresh subagent needs to open before writing code.
- Makes batch/parallel dispatch consistent — every task in a batch is filled from the same
  template, so aggregation of the Final report block is mechanical.
- Is agent-agnostic: it names no specific tool call or API. Hermes maps it onto
  `delegate_task(goal=..., context=...)`; a CLI-based agent maps it onto a prompt string passed
  on invocation. See [delegation-patterns](../delegation-patterns/SKILL.md) for both.

## Minimal Example

```text
Context:
- Project root: C:\Users\admin\projects\oxidium-forge
- Agents root: C:\Users\admin\projects\oxidium-forge\.agents
- Required skills: .agents/skills/software-development/board-task-executor/SKILL.md
- Plan file: docs/plans/2026-07-29-tenant-support.md
- Task file: docs/plans/tasks/TP-02_scope-tenant-queries.md
- Kanban file: docs/kanban.md

Execution mode:
- separate

Task:
- Task ID: TP-02
- Task title: Scope tenant queries
- Expected scope: src/db/queries.rs only

Rules:
- Read required skills first.
- Read the task file before editing.
- Update task status and kanban status.
- Validate before moving to Done.
- Report changed files and validation commands.

Final report:
- Status:
- Files changed:
- Validation:
- Blockers:
```
