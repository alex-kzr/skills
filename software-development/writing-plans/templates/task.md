# {TASK-ID} - {Title}

Plan - [{YYYY-MM-DD-feature-name}.md](../{YYYY-MM-DD-feature-name}.md)

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

---

Field syntax, enums, defaults, and error messages: see
[writing-plans → Task Metadata](../SKILL.md#task-metadata-machine-readable), and the project's
own metadata contract when it defines one (in oxidium-forge:
`docs/agents/task-metadata-contract.md`).

Placeholders in angle brackets are mandatory decisions. Replace every one; write the literal
`none` where a field genuinely has no value. Delete this trailing note when using the template.
