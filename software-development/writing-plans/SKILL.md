---
name: writing-plans
description: "Write implementation plans: phases, tasks, kanban board, and individual task files. Use before implementing multi-step features, breaking down complex requirements, or delegating to subagents."
version: 2.2.0
author: Hermes Agent (adapted from obra/superpowers)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [planning, design, implementation, workflow, documentation]
    related_skills: [subagent-driven-development, test-driven-development, requesting-code-review]
---

# Writing Implementation Plans

## Overview

Write comprehensive implementation plans assuming the implementer has zero context for the codebase and questionable taste. Document everything they need: which files to touch, complete code, testing commands, docs to check, how to verify. Give them bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

**Core principle:** A good plan makes implementation obvious. If someone has to guess, the plan is incomplete.

## Language Requirement

**All documents created as part of implementation plans must be written in English.**

This ensures:
- Consistent, searchable documentation across the project
- Accessibility for all team members regardless of language background
- Maintainability over time as team composition changes

Apply this rule to:
- Plan files (`docs/plans/YYYY-MM-DD-*.md`)
- Kanban board (`docs/kanban.md`)
- Task files (`docs/plans/tasks/*.md`)
- Code comments in implementation
- Commit messages
- Task descriptions, requirements, and validation steps

## File Structure

Every plan produces three artifacts:

```
docs/plans/YYYY-MM-DD-feature-name.md   — feature description, phases, and task list
docs/kanban.md                           — kanban board with task statuses
docs/plans/tasks/{task-id}_{task-short-name}.md — detailed file per task
```

## Bite-Sized Task Granularity

**Each task = one atomic, independently executable unit of work.**

Tasks must be:
- Single responsibility — one clear goal
- Independently executable — no hidden dependencies within a phase
- Testable — has a clear done state

**Too big:** "Build authentication system"
**Right size:** "Create User model with email field", "Add password hash field", "Create password hashing utility"

## Phase & Task ID Rules

- **Phase ID** — abbreviation from first letters of phase name: `Hybrid Search` → `HS`, `Query Expansion` → `QE`
- **Task ID** — `{PHASE_ID}-{NN}`, e.g. `HS-01`, `HS-02`
- **Task filename** — `{task-id}_{task-short-name}.md`, e.g. `HS-01_embedding-model.md`

## Execution Mode Guidance

Every phase must tell the executing agent(s) **how** to run its tasks, not just what they are. Pick exactly one mode per phase (or override per task/group when a phase mixes modes):

| Mode | When to use | How to mark it |
|---|---|---|
| **Separate** | Tasks touch different files/areas, no shared context needed | Default — no tag needed, or `[separate]` |
| **Parallel** | Tasks are independent (no shared files, no ordering constraint) and can be dispatched to subagents at the same time | `[parallel: <IDs>]` |
| **Same session** | Tasks are tightly coupled (e.g. share a data model change) and splitting them risks an inconsistent intermediate state | `[same-session: <IDs>]` |
| **Whole phase same session** | The phase is small or so interdependent that splitting it into separate task executions adds overhead without benefit | `[whole-phase: same-session]` |

Decide this while designing phases (Step 3), not as an afterthought — it directly affects how [delegation-patterns](../delegation-patterns/SKILL.md) dispatches subagents at execution time.

### Task Leases for Parallel Work

When a phase is `parallel` (or multiple agents may otherwise work the same board concurrently), executors take a lightweight lease at `docs/.agents/locks/{task-id}.lock` before moving a task to "In Progress", and remove it on "Done" or when un-blocking back to "To Do". See [board-task-executor → Task Leases](../board-task-executor/SKILL.md#task-leases-parallel-safety) for the file format and rules. No plan-writing action is needed here beyond marking the phase `parallel` correctly — the lease mechanics are handled by the executor.

## Task Metadata (Machine-Readable)

Prose sections tell a human what to do. An `## Execution Metadata` block tells an orchestrator
the same thing without guessing: what kind of task this is, who runs it, what it may write, what
it depends on, and how it is checked. Add the block to every **new** task file.

```markdown
## Execution Metadata
- Type: <rust | backend | frontend | ui | plugin | docs | research | design | tooling | agent-config>
- Executor: <role name>
- Depends on: <TASK-ID, TASK-ID | none>
- Allowed scope: `<path glob>`, `<path glob>`
- Out of scope: `<path glob>` | none
- Required skills: `<exact path to a SKILL.md>` | none
- Maximum repair attempts: 2
- Documentation impact: `<doc path>` | none
- Verification commands:
  - `<cwd>` -> `<command>`
- Blocking conditions: <text> | none
```

Rules that hold in every project:

- The block sits between `## Status` and `## Purpose`, one `- Field: value` line per field.
- Lists are comma-separated; backticks around paths are optional and ignored.
- "Nothing" is always the literal `none`. An empty value is an error, never an implicit `none` —
  an author must not be able to skip a decision by leaving a blank.
- Paths are repository-relative and POSIX-separated. No absolute path, no `~`, no `..`.
- `Required skills` names **exact** `SKILL.md` paths. "the Rust skill" is not a path.
- `Verification commands` lists only commands the repository actually defines, one per entry,
  with no shell operators (`|`, `&&`, `;`, `>`), so each has its own exit code.

Pair it with a discrete criteria list so a verifier can tabulate evidence one row at a time:

```markdown
## Acceptance Criteria
- [ ] AC-1 — <independently checkable statement>
- [ ] AC-2 — <independently checkable statement>
```

`## Acceptance Criteria` replaces `## Definition of Done` in new task files — do not split
criteria across both. Task files that predate the block keep `## Definition of Done`, and an
orchestrator reads those checkboxes as `AC-1 … AC-n`.

**Do not retrofit old task files.** The block is additive; historical tasks stay executable
through documented defaults. Enrich an old file only when you are changing it anyway.

**Project overrides.** When the project defines its own metadata contract — in this repository,
`docs/agents/task-metadata-contract.md` — that document governs the exact field list, enums,
aliases, defaults, and error messages, and this section is the summary of it.

## Plan File Template

`docs/plans/YYYY-MM-DD-feature-name.md`

```markdown
# Feature: <Feature Name>

<Short description of the feature — 2-4 sentences covering goal, current state, and approach.>

## Phase 1: <Phase Name> (<First task ID> to <Last task ID>)
<Short description of phase 1 goal.>
**Execution:** <separate | parallel: <IDs> | same-session: <IDs> | whole-phase: same-session — one sentence why>

## Phase 2: <Phase Name> (<First task ID> to <Last task ID>)
<Short description of phase 2 goal.>
**Execution:** <separate | parallel: <IDs> | same-session: <IDs> | whole-phase: same-session — one sentence why>

---

## Phase 1 — <Phase Name>

**Execution:** <same tag as above, repeated here for the executor>

### <Task ID> <Task Name>
<One-sentence task description.>
→ [<task-id>_<task-short-name>.md](tasks/<task-id>_<task-short-name>.md)

### <Task ID> <Task Name>
<One-sentence task description.>
→ [<task-id>_<task-short-name>.md](tasks/<task-id>_<task-short-name>.md)

## Phase 2 — <Phase Name>

**Execution:** <same tag as above, repeated here for the executor>

### <Task ID> <Task Name>
<One-sentence task description.>
→ [<task-id>_<task-short-name>.md](tasks/<task-id>_<task-short-name>.md)
```

**Example:**

```markdown
# Feature: Conversation History Per User

This plan adds conversational memory to the AI chatbot. Currently the bot processes each message in isolation. The goal is to preserve per-user context between messages using in-memory storage keyed by Telegram user ID.

## Phase 1: Pseudo-memory (PM-01 to PM-03)
Introduce in-memory dialogue storage, refactor the LLM call to support history, and integrate into the message handler.
**Execution:** same-session: PM-01, PM-02 — the storage module and the LLM refactor share the same `history` shape and are easiest to get right together; PM-03 can follow separately once both land.

---

## Phase 1 — Pseudo-memory

**Execution:** same-session: PM-01, PM-02 (do together); PM-03 separate

### PM-01 Create history storage module
Create `src/history.py` with per-user in-memory history: `get_history()`, `append_message()`, `clear_history()`.
→ [PM-01_history-storage.md](tasks/PM-01_history-storage.md)

### PM-02 Refactor ask_llm() to support history
Update `src/llm.py` so `ask_llm()` accepts a `history` list and sends full context to Ollama.
→ [PM-02_llm-history-support.md](tasks/PM-02_llm-history-support.md)

### PM-03 Integrate history into message handler
Update `src/handlers.py` to load history before `ask_llm()` and save the response after.
→ [PM-03_handler-integration.md](tasks/PM-03_handler-integration.md)
```

## Kanban Board Template

`docs/kanban.md`

```markdown
# Kanban Board

## To Do
- [<Task ID>: <Task Name>](plans/tasks/<task-id>_<task-short-name>.md)
- [<Task ID>: <Task Name>](plans/tasks/<task-id>_<task-short-name>.md)

## In Progress
- (empty)

## Done
- (empty)
```

All tasks start in **To Do** in execution order. Every entry must be a relative link to the task file using the format `[<Task ID>: <Task Name>](plans/tasks/<task-id>_<task-short-name>.md)`.

## Task File Template

`docs/plans/tasks/{task-id}_{task-short-name}.md`
(also available as a copyable file: [templates/task.md](templates/task.md))

```markdown
# {task_id} - {title}

Plan — [YYYY-MM-DD-feature-name.md](../YYYY-MM-DD-feature-name.md)

## Status
- [ ] To Do
- [ ] In Progress
- [ ] Done

## Execution Metadata
- Type: <rust | backend | frontend | ui | plugin | docs | research | design | tooling | agent-config>
- Executor: <role name>
- Depends on: <TASK-ID, TASK-ID | none>
- Allowed scope: `<path glob>`
- Out of scope: `<path glob>` | none
- Required skills: `<exact path to a SKILL.md>` | none
- Maximum repair attempts: 2
- Documentation impact: `<doc path>` | none
- Verification commands:
  - `<cwd>` -> `<command>`
- Blocking conditions: <text> | none

## Purpose
Short description of why this task exists.

## Context
Background, links to related files, modules, or docs.

## Requirements
- Requirement 1
- Requirement 2

## Implementation Notes
- Suggested approach
- Constraints
- Important details

## Testing
- [ ] Unit tests
- [ ] Integration tests
- [ ] Manual testing

## Acceptance Criteria
- [ ] AC-1 — <independently checkable statement>
- [ ] AC-2 — <independently checkable statement>

## Affected Files / Components
- file1
- module/service

## Risks / Dependencies
- Dependency 1
- Risk 1

## Validation Steps
1. Step 1
2. Step 2
3. Expected result

## Follow-ups (optional)
- Additional tasks discovered during implementation
```

## Writing Process

### Step 1: Understand Requirements

Read the feature description and any existing docs in `docs/*` (skip `docs/cr/`). Extract: features, requirements, constraints, Jira ID if applicable.

### Step 2: Explore the Codebase

Understand project structure, existing patterns, similar features, and test layout before designing tasks.

### Step 3: Design Phases and Tasks

- Break the feature into 2–3 phases with clear goals
- Define atomic, independently executable tasks per phase
- Assign phase IDs and task IDs
- Decide the execution mode for each phase (see [Execution Mode Guidance](#execution-mode-guidance)): separate, parallel, same-session, or whole-phase-same-session

### Step 4: Write the Plan File

Create `docs/plans/YYYY-MM-DD-feature-name.md` with feature description, phases, and task list with links. Include an **Execution** line for every phase, in both the overview and the phase section.

### Step 5: Create Task Files

For each task, create `docs/plans/tasks/{task-id}_{task-short-name}.md` using the template above.

Include in each task file:
- **Exact file paths** (not "the config file" but `src/config/settings.py`)
- **Complete code examples** where relevant (copy-pasteable)
- **Exact commands** with expected output
- **Verification steps** proving the task is done
- An **`## Execution Metadata` block** and an **`## Acceptance Criteria`** list, per
  [Task Metadata](#task-metadata-machine-readable). Every field is a decision; write `none`
  rather than leaving one blank.

### Step 6: Create the Kanban Board

Create or update `docs/kanban.md` with all tasks in **To Do** in execution order.

### Step 7: Review

- [ ] Plan file has feature description, all phases with ID ranges, all tasks with links
- [ ] Every task has a file in `docs/plans/tasks/`
- [ ] All tasks are in `docs/kanban.md` under To Do
- [ ] Tasks are atomic, sequential, testable
- [ ] Every phase has an Execution mode tag (separate / parallel / same-session / whole-phase)
- [ ] Every new task file has a complete `## Execution Metadata` block — no blank values, `none` written explicitly
- [ ] `Depends on` names real task IDs and forms no cycle; the first task of a phase says `none`
- [ ] `Required skills` names exact `SKILL.md` paths that exist
- [ ] `Verification commands` uses only commands the repository defines, one per entry
- [ ] Every new task file has `## Acceptance Criteria` numbered `AC-1 … AC-n`, each independently checkable
- [ ] No historical task file was rewritten to add metadata
- [ ] No vague formulations, no tasks mixing responsibilities
- [ ] DRY, YAGNI, TDD principles applied

### Step 8: Commit

```bash
git add docs/plans/ docs/kanban.md docs/plans/tasks/
git commit -m "docs: add implementation plan for [feature]"
```

## Principles

### DRY — Don't Repeat Yourself
Extract shared logic; don't copy-paste validation or utilities across tasks.

### YAGNI — You Aren't Gonna Need It
Implement only what's needed now. No speculative flexibility.

### TDD — Test-Driven Development
Every task producing code should follow the full cycle in its Implementation Notes:
1. Write failing test
2. Run to verify failure
3. Write minimal code
4. Run to verify pass

See `test-driven-development` skill for details.

### Frequent Commits
Commit after every task: `git commit -m "type: description"`

## Execution Handoff

After saving the plan:

**"Plan complete and saved. Ready to execute using delegation-patterns (SDD) — I'll dispatch a fresh subagent per task with two-stage review (spec compliance then code quality). Shall I proceed?"**

Use the [delegation-patterns](../delegation-patterns/SKILL.md) skill (Subagent-Driven Development section): dispatch a fresh subagent per task using the current agent's mechanism (Hermes-specific `delegate_task`, Codex CLI, Claude Code CLI, or equivalent), then run spec compliance review and code quality review. Each subagent must open and execute its task file following the rules in [board-task-executor](../board-task-executor/SKILL.md). Proceed only when both review stages approve. Respect each phase's **Execution** tag: dispatch `parallel` tasks concurrently, keep `same-session`/`whole-phase` tasks in a single subagent turn instead of splitting them, and default to one subagent per task otherwise.
