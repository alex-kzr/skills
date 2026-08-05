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
- Task type:
- Depends on:
- Allowed scope:
- Out of scope:
- Verification commands:
- Maximum repair attempts:

Rules:
- Read required skills first.
- Read the task file before editing.
- Write only inside Allowed scope; never inside Out of scope.
- Run every verification command from its declared working directory, one at a time.
- Report each command with its working directory and exit code. Never report a command you did not run.
- Do not verify your own work and do not tick acceptance-criteria checkboxes.
- Terminal state is `implemented`: stop after reporting. The orchestrator dispatches verification and moves the board.

Final report:
- Status: implemented | blocked
- Files changed:
- Validation:
- Acceptance criteria evidence:
- Out-of-scope discoveries:
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
- **Task type / Depends on / Allowed scope / Out of scope / Verification commands / Maximum
  repair attempts** — copied verbatim from the task file's `## Execution Metadata` block (see
  [writing-plans → Task Metadata](../writing-plans/SKILL.md#task-metadata-machine-readable)).
  Copy them rather than pointing at the file: a fresh subagent must not have to infer its own
  boundary. When the task file has no metadata block, fill `Allowed scope` from
  `## Affected Files / Components`, `Depends on` from board position, and say `none declared`
  for the rest — do not invent verification commands.
- **Allowed scope** — the boundary that turns an out-of-scope discovery into a report instead of
  a silent expansion of the task.
- **Verification ownership** — the subagent runs the commands as part of implementing; it does
  **not** decide whether the task passed. `implemented` is its terminal state, and an
  independent verifier with fresh context produces the verdict. This is why the envelope's rules
  forbid ticking acceptance-criteria checkboxes and moving the card to Done.
- **Acceptance criteria evidence** — one line per `AC-n` stating what in the diff or command
  output addresses it. Evidence, not a self-assessed pass.
- **Out-of-scope discoveries** — anything the subagent found that needed a change outside
  `Allowed scope`. Reported, never performed.
- **Role and report contracts** — in a project that publishes its own, those govern the dispatch
  and the shape of the Final report. In oxidium-forge they are
  `.agents/skills/project-skills/oxidium-forge/feature-pipeline/roles/README.md` and
  `.agents/skills/project-skills/oxidium-forge/feature-pipeline/reports/README.md`. This envelope
  stays the generic shape; it does not restate them.

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
- Task type: rust
- Depends on: TP-01
- Allowed scope: apps/oxidium-forge-core/crates/forge-store/src/queries.rs
- Out of scope: apps/oxidium-forge-ui/**, docs/**
- Verification commands:
  - apps/oxidium-forge-core -> cargo fmt --check
  - apps/oxidium-forge-core -> cargo clippy --all-targets --all-features -- -D warnings
  - apps/oxidium-forge-core -> cargo test --all
- Maximum repair attempts: 2

Rules:
- Read required skills first.
- Read the task file before editing.
- Write only inside Allowed scope; never inside Out of scope.
- Run every verification command from its declared working directory, one at a time.
- Report each command with its working directory and exit code. Never report a command you did not run.
- Do not verify your own work and do not tick acceptance-criteria checkboxes.
- Terminal state is `implemented`: stop after reporting. The orchestrator dispatches verification and moves the board.

Final report:
- Status: implemented | blocked
- Files changed:
- Validation:
- Acceptance criteria evidence:
- Out-of-scope discoveries:
- Blockers:
```
