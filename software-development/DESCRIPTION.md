---
description: Software development skills — systematic debugging, TDD, batch delegation, orchestration patterns, spike investigations, subagent-driven development, plan writing.
---

# Software Development

Skills for structured software development workflows and engineering best practices.

## Contents

| Type | Path | Description | When to open |
|---|---|---|---|
| Catalog | [backend-dev/](backend-dev/DESCRIPTION.md) | Backend development skills by language and framework — Rust, and more. | Open when working on server-side code, REST APIs, databases, or CLI tools. |
| Catalog | [frontend-dev/](frontend-dev/DESCRIPTION.md) | Frontend development skills — React, Tailwind CSS, and Vite. | Open when working on client-side code, UI components, or frontend build tooling. |
| Skill | [debugging/](debugging/SKILL.md) | Debugging methodology and tools: systematic root cause analysis, Python (pdb/debugpy), Node.js (inspect/CDP), and Hermes TUI debugging. | Open when debugging any codebase systematically. |
| Skill | [delegation-patterns/](delegation-patterns/SKILL.md) | Delegation patterns: batch parallel, sequential, conditional, and multi-stage orchestration workflows across Hermes, Codex, Claude Code, or equivalent subagent mechanisms. | Open when designing delegation or multi-stage orchestration flows. |
| Skill | [board-task-executor/](board-task-executor/SKILL.md) | Execute tasks from a task board in order, moving them through To Do, In Progress, and Done while preserving task status and validation. | Open when working through a task board one task at a time. |
| Skill | [plan/](plan/SKILL.md) | Plan mode: write markdown plan to .hermes/plans/, no exec. | Open when the task requires producing a written plan before any implementation. |
| Skill | [requesting-code-review/](requesting-code-review/SKILL.md) | Pre-commit review: security scan, quality gates, auto-fix. | Open when running a code review or quality gate before committing. |
| Skill | [spike/](spike/SKILL.md) | Throwaway experiments to validate an idea before build. | Open when a quick throwaway experiment is needed to de-risk a design decision. |
| Skill | [subagent-driven-development/](subagent-driven-development/SKILL.md) | Execute plans through subagent delegation with two-stage review. | Open when executing an implementation plan through subagent delegation. |
| Skill | [test-driven-development/](test-driven-development/SKILL.md) | TDD: enforce RED-GREEN-REFACTOR, tests before code. | Open when the task requires strict test-first development. |
| Skill | [writing-plans/](writing-plans/SKILL.md) | Write implementation plans: phases, tasks, kanban board, and individual task files in docs/. | Open when a structured written implementation plan is needed. |
