---
name: delegation-patterns
description: "Abstract delegation/orchestration decisions (batch, sequential, conditional, multi-stage) plus agent-specific mechanisms: Hermes delegate_task, and CLI-based delegation through Codex or Claude Code. Includes subagent-driven development (2-stage review)."
version: 1.1.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [delegation, parallel, batch, orchestration, multi-stage, conditional, integration, performance]
    related_skills: [subagent-driven-development, claude-code-subagent]
    absorbed_from: [batch-delegation, orchestration-patterns]
---

# Delegation Patterns — Batch, Sequential, Conditional & Multi-Stage Orchestration

Complete guide to delegating work: from simple parallel batches to complex multi-stage
pipelines with conditional branching, error handling, and performance tuning.

This skill has two layers:

1. **Abstract orchestration decisions** (below) — apply regardless of which agent
   implementation actually runs the subagent: when to batch, when to run sequentially,
   how to gate on results, how to structure multi-stage pipelines.
2. **Agent-specific mechanisms** — the concrete API or CLI syntax used to carry out
   those decisions. Pick the one that matches your runtime:

| Mechanism | Use when | Reference |
|---|---|---|
| Hermes `delegate_task` | Running inside Hermes Agent, spawning in-process subagents | [Hermes-Specific: `delegate_task`](#hermes-specific-delegate_task-api) below, [hermes-agent/SKILL.md](../../autonomous-ai-agents/hermes-agent/SKILL.md) |
| Codex CLI | Delegating to OpenAI Codex as an external process (worktrees, `codex exec`) | [../../autonomous-ai-agents/codex/SKILL.md](../../autonomous-ai-agents/codex/SKILL.md) |
| Claude Code CLI | Delegating to Claude Code as an external process (`claude -p`, tmux) | [../../autonomous-ai-agents/claude-code/SKILL.md](../../autonomous-ai-agents/claude-code/SKILL.md) |

A non-Hermes agent (Codex, Claude Code, or any other orchestrator) should read the
**abstract orchestration decisions** section to decide *what* to do, then follow its own
CLI-based delegation mechanism (see [CLI-Based Delegation](#cli-based-delegation-codex--claude-code)) to decide *how*.

When dispatching task-board work to a subagent (any agent implementation), fill the prompt
using the [Standard Subagent Prompt Envelope](../references/subagent-prompt-envelope.md) so
required context (project root, agents root, skills, plan/task/kanban paths, execution mode)
is never left implicit.

---

## Abstract Orchestration Decisions

These decisions are implementation-agnostic — they apply whether the actual subagent is
spawned via Hermes `delegate_task`, a Codex/Claude Code CLI process, or any other mechanism.

### When to Use What

| Pattern | Shape | Use When | Speedup |
|---------|-----|----------|---------|
| **Batch** | Fan out N independent subagents | 2+ independent tasks, different files/modules | ~2.5–3× |
| **Sequential** | One subagent at a time, in order | Tasks depend on each other's output, strict order required | 1× (baseline) |
| **Conditional** | `if result OK → dispatch next` | Next step depends on prior result | Varies |
| **Multi-Stage** | Combine all of the above | Complex workflows with infrastructure → features → testing | 2–3× (batch stages) |

### Decision Rules

```
Independent tasks, different files  → Batch mode (fan out)
Dependent tasks, same files        → Sequential mode (one at a time)
Runtime conditions                 → Conditional branching
Complex workflow with phases       → Multi-stage orchestration
```

**Don't use batch when:**
- Tasks depend on each other's output
- Strict order is required
- One task is critical and must pass first
- Tasks touch the same files (conflict risk)
- Memory is constrained

---

## CLI-Based Delegation (Codex / Claude Code)

For agents that don't have an in-process `delegate_task` tool, the same abstract patterns
map onto external CLI processes:

| Abstract pattern | Codex CLI | Claude Code CLI |
|---|---|---|
| Batch | Multiple `codex --yolo exec` processes, one per git worktree, run with `background=true` | Multiple `claude -p` invocations in parallel tmux sessions or worktrees |
| Sequential | One `codex exec` (or interactive session), wait for completion, then the next | One `claude -p` print-mode call, check its result, then the next |
| Conditional | Check the prior process's exit/output before launching the next `codex exec` | Check the prior `claude -p --output-format json` result's `subtype` before launching the next |
| Multi-Stage | Combine worktree batches with sequential gating steps between stages | Combine parallel `claude -p` batches with sequential gating steps between stages |

See the full syntax, flags, and pitfalls in:
- [../../autonomous-ai-agents/codex/SKILL.md](../../autonomous-ai-agents/codex/SKILL.md)
- [../../autonomous-ai-agents/claude-code/SKILL.md](../../autonomous-ai-agents/claude-code/SKILL.md)

Both CLIs are external processes — there is no `max_concurrent_children` config or shared
process state to manage; concurrency is bounded by however many processes/worktrees you
choose to launch at once.

---

## Hermes-Specific: `delegate_task` API

Everything below this point is Hermes Agent's in-process `delegate_task` tool. If you are
not running inside Hermes, skip to [CLI-Based Delegation](#cli-based-delegation-codex--claude-code) above.

## 1. Batch Delegation — Parallel Tasks

### Quick Example

```python
delegate_task(
    tasks=[
        {
            "goal": "Add logging to calculator.py",
            "context": "Add debug/info/error logging to all methods...",
            "toolsets": ["terminal", "file"]
        },
        {
            "goal": "Create config loader module",
            "context": "Create src/config_loader.py with JSON/YAML/TOML support...",
            "toolsets": ["terminal", "file"]
        },
        {
            "goal": "Setup mypy type checking",
            "context": "Install mypy, create config, add type hints...",
            "toolsets": ["terminal", "file"]
        }
    ]
)
```

### How Batch Works

```
Input: 5 tasks, max_concurrent_children=3

Wave 1: [Task1, Task2, Task3] → Parallel
  ↓ (first completes)
Wave 2: [Task4] → Starts
  ↓ (second completes)
Wave 3: [Task5] → Starts

Total: ~3× parallelism → ~2.9× speedup
```

### Common Batch Patterns

#### Independent Infrastructure Tasks

```python
delegate_task(
    tasks=[
        {
            "goal": "Setup logging framework",
            "context": """
            TASK: Create src/logger.py with get_logger(name), console + file handlers.

            FINAL REPORT:
            - Created: YES/NO
            - Tests: [count]/[total]
            """,
            "toolsets": ["terminal", "file"]
        },
        {
            "goal": "Setup configuration system",
            "context": """
            TASK: Create src/config.py with Config class, get/get_int/get_bool methods.

            FINAL REPORT:
            - Created: YES/NO
            - Tests: [count]/[total]
            """,
            "toolsets": ["terminal", "file"]
        },
        {
            "goal": "Setup pytest",
            "context": """
            TASK: Create tests/conftest.py with fixtures, pytest.ini.

            FINAL REPORT:
            - Created: YES/NO
            - Fixtures: [count]
            """,
            "toolsets": ["terminal", "file"]
        }
    ]
)
```

#### Module Creation (Different Modules)

```python
delegate_task(
    tasks=[
        {"goal": "Create src/string_utils.py (reverse, capitalize, count_vowels, is_palindrome)", "context": "...FINAL REPORT: Module created YES/NO, Tests [count]/[total]", "toolsets": ["terminal", "file"]},
        {"goal": "Create src/math_utils.py (gcd, lcm, fibonacci, factorial)", "context": "...FINAL REPORT: Module created YES/NO, Tests [count]/[total]", "toolsets": ["terminal", "file"]},
        {"goal": "Create src/validation.py (validate_email, validate_phone, validate_url)", "context": "...FINAL REPORT: Module created YES/NO, Tests [count]/[total]", "toolsets": ["terminal", "file"]}
    ]
)
```

#### Test Addition (Different Test Files)

```python
delegate_task(
    tasks=[
        {"goal": "Add edge case tests for calculator", "context": "...FINAL REPORT: Tests added [count], All passing YES/NO", "toolsets": ["file"]},
        {"goal": "Add integration tests for config", "context": "...FINAL REPORT: Tests added [count], All passing YES/NO", "toolsets": ["file"]},
        {"goal": "Add performance tests", "context": "...FINAL REPORT: Tests added [count], All passing YES/NO", "toolsets": ["file"]}
    ]
)
```

#### Refactoring (Different Modules)

```python
delegate_task(
    tasks=[
        {"goal": "Refactor calculator to use type hints", "context": "...FINAL REPORT: Type hints [count], mypy clean/errors", "toolsets": ["terminal", "file"]},
        {"goal": "Refactor string utils to use type hints", "context": "...FINAL REPORT: Type hints [count], mypy clean/errors", "toolsets": ["terminal", "file"]},
        {"goal": "Refactor config loader to use type hints", "context": "...FINAL REPORT: Type hints [count], mypy clean/errors", "toolsets": ["terminal", "file"]}
    ]
)
```

---

## 2. Sequential Delegation — Dependent Tasks

Use `delegate_task(goal=...)` for one task at a time when order matters.

```python
# Create base module first
base_result = delegate_task(
    goal="Create module A",
    context="...",
    toolsets=["terminal", "file"]
)

if base_result['status'] != 'completed':
    raise Exception("Module A creation failed")

# Then create module that depends on A
delegate_task(
    goal="Create module B that imports A",
    context="Uses src.module_a...",
    toolsets=["terminal", "file"]
)
```

### When Sequential is Required

- Module B imports Module A (dependency)
- Multiple tasks modify the same file (conflict avoidance)
- One task is critical and must pass before others start
- Output of task 1 is needed as input to task 2

---

## 3. Multi-Stage Orchestration

Combine batch, sequential, and conditional into a structured pipeline.

### The 4-Stage Model

```
Stage 1: [Task1, Task2, Task3]  → Parallel Batch (Infrastructure)
           ↓ (all complete ✓)
Stage 2:  Task4 → Task5         → Sequential (Dependent Features)
           ↓ (check results)
Stage 3:  if Task4 OK → Task6   → Conditional (Enhancements)
          if Task5 OK → Task7
           ↓ (all stages complete)
Stage 4:  Integration Test      → Verify all components together
```

### Stage 1: Batch Infrastructure

```python
stage1_results = delegate_task(
    tasks=[
        {"goal": "Setup logging", "context": "Create src/logger.py...", "toolsets": ["terminal", "file"]},
        {"goal": "Setup config", "context": "Create src/config.py...", "toolsets": ["terminal", "file"]},
        {"goal": "Setup tests", "context": "Create tests/conftest.py...", "toolsets": ["terminal", "file"]},
    ]
)

# Gate: validate all Stage 1 tasks succeeded
if not all(r['status'] == 'completed' for r in stage1_results):
    raise Exception("Stage 1 failed — cannot proceed")
```

**Characteristics:** 3 tasks run in parallel, ~2–3× faster than sequential, all must succeed for Stage 2.

### Stage 2: Sequential Features

```python
api_result = delegate_task(
    goal="Create API endpoint",
    context="""
    DEPENDENCIES (from Stage 1):
    - Use src.logger.get_logger for logging
    - Use src.config.Config for configuration

    REQUIREMENTS: handle_request(path, method, data)
    FINAL REPORT: Created YES/NO, Uses logger YES/NO, Tests [count]/[total]
    """,
    toolsets=["terminal", "file"]
)

if api_result['status'] != 'completed':
    raise Exception("API creation failed")

db_result = delegate_task(
    goal="Create database layer",
    context="""
    DEPENDENCIES (from Stage 1):
    - Use src.logger.get_logger for logging
    - Use src.config.Config for configuration

    REQUIREMENTS: Database class with connect/query/execute/close
    FINAL REPORT: Created YES/NO, Tests [count]/[total]
    """,
    toolsets=["terminal", "file"]
)
```

**Characteristics:** Tasks run one at a time, explicit dependencies on Stage 1, validates before proceeding.

### Stage 3: Conditional Enhancements

```python
stage3_tasks = []

if api_result['status'] == 'completed':
    stage3_tasks.append({
        "goal": "Add rate limiting to API",
        "context": "PRECONDITION: src/api.py exists. Decorator @rate_limit(max, window)...",
        "toolsets": ["terminal", "file"]
    })

if db_result['status'] == 'completed':
    stage3_tasks.append({
        "goal": "Create migrations for DB",
        "context": "PRECONDITION: src/database.py exists. Migration class with up/down...",
        "toolsets": ["terminal", "file"]
    })

# Run qualifying Stage 3 tasks in parallel (batch optimization)
if stage3_tasks:
    stage3_results = delegate_task(tasks=stage3_tasks)
```

**Conditional Patterns:**

```python
# Simple if/else
if task_a_succeeded:
    delegate_task(goal="Enhancement A", ...)
else:
    delegate_task(goal="Fallback A", ...)

# Multiple conditions
if task_a_succeeded and task_b_succeeded:
    delegate_task(goal="Integration", ...)

# Nested conditions
if task_a_succeeded:
    if quality >= 8:
        delegate_task(goal="Advanced feature", ...)
    else:
        delegate_task(goal="Basic feature", ...)
```

### Stage 4: Integration Testing

```python
integration_result = delegate_task(
    goal="Run full integration tests",
    context="""
    VERIFICATION:
    - Stage 1: logger + config work
    - Stage 2: API uses logger + config; DB uses logger + config
    - Stage 3: Rate limiting + migrations work
    - Cross-stage: All components integrate correctly

    Create tests/test_integration.py
    FINAL REPORT: Tests [count]/[total], All stages integrated YES/NO
    """,
    toolsets=["terminal", "file"]
)

if integration_result['status'] != 'completed':
    raise Exception("Integration tests failed")
```

### Full Workflow Template

```python
def run_multi_stage_orchestration():
    """Complete multi-stage orchestration workflow."""

    # === Stage 1: Batch Infrastructure ===
    print("🚀 Stage 1: Batch infrastructure setup...")
    stage1_results = delegate_task(tasks=[
        {"goal": "Setup logging", "context": "...", "toolsets": ["terminal", "file"]},
        {"goal": "Setup config", "context": "...", "toolsets": ["terminal", "file"]},
        {"goal": "Setup tests", "context": "...", "toolsets": ["terminal", "file"]},
    ])

    if not all(r['status'] == 'completed' for r in stage1_results):
        raise Exception("❌ Stage 1 failed")
    print("✅ Stage 1 completed")

    # === Stage 2: Sequential Features ===
    print("🚀 Stage 2: Sequential feature development...")
    api_result = delegate_task(goal="Create API...", context="...", toolsets=["terminal", "file"])
    if api_result['status'] != 'completed':
        raise Exception("❌ API creation failed")

    db_result = delegate_task(goal="Create DB...", context="...", toolsets=["terminal", "file"])
    if db_result['status'] != 'completed':
        raise Exception("❌ Database creation failed")
    print("✅ Stage 2 completed")

    # === Stage 3: Conditional Enhancements (parallel) ===
    print("🚀 Stage 3: Conditional enhancements...")
    stage3_tasks = []
    if api_result['status'] == 'completed':
        stage3_tasks.append({"goal": "Add rate limiting", ...})
    if db_result['status'] == 'completed':
        stage3_tasks.append({"goal": "Create migrations", ...})
    if stage3_tasks:
        stage3_results = delegate_task(tasks=stage3_tasks)
    print("✅ Stage 3 completed")

    # === Stage 4: Integration Testing ===
    print("🚀 Stage 4: Integration testing...")
    integration_result = delegate_task(goal="Run full integration tests", context="...", toolsets=["terminal", "file"])
    if integration_result['status'] != 'completed':
        raise Exception("❌ Integration tests failed")
    print("🎉 All stages completed successfully!")

    return {
        "stage1": stage1_results,
        "stage2": {"api": api_result, "db": db_result},
        "stage3": stage3_results,
        "stage4": integration_result
    }
```

---

## 4. Configuration — max_concurrent_children

### Default: 3 parallel tasks

Edit `config.yaml`:
```yaml
delegation:
  max_concurrent_children: 3  # Default (balanced)
  # Increase for I/O-bound tasks:
  # max_concurrent_children: 5
  # Decrease for CPU-bound tasks:
  # max_concurrent_children: 2
```

### Tuning Guidelines

| Workload Type | Recommended | Why |
|---------------|-------------|-----|
| CPU-bound (refactors, analysis) | 2 | Less resource contention |
| Mixed (default) | 3 | Balanced throughput |
| I/O-bound (downloads, file ops) | 5 | Tasks wait on I/O, slots free faster |

---

## 5. Structured Output Patterns

### Per-Task Structured Report

```python
context = """
TASK: <description>

FINAL REPORT FORMAT:
{
  "task_completed": true/false,
  "files_created": ["file1.py", "file2.py"],
  "files_modified": ["file3.py"],
  "tests_passing": 10,
  "tests_total": 10,
  "duration_seconds": 45,
  "issues": []
}

This format is parseable for aggregation.
"""
```

### Aggregating Batch Results

```python
results = delegate_task(tasks=[...])

all_completed = all(r['status'] == 'completed' for r in results)
total_files = sum(len(r.get('files_created', [])) for r in results)
total_tests = sum(r.get('tests_passing', 0) for r in results)

print(f"All tasks completed: {all_completed}")
print(f"Total files created: {total_files}")
print(f"Total tests passing: {total_tests}")
```

---

## 6. Error Handling Patterns

### Pattern 1: Retry Failed Tasks

```python
results = delegate_task(tasks=[...])

failed_tasks = [(i, r) for i, r in enumerate(results) if r['status'] != 'completed']

if failed_tasks:
    print(f"Failed: {len(failed_tasks)}/{len(results)}")
    for idx, result in failed_tasks:
        delegate_task(
            goal=tasks[idx]['goal'],
            context=tasks[idx]['context']
        )
```

### Pattern 2: Stage-Level Retry

```python
def run_stage_with_retry(stage_name, task_or_tasks, max_retries=3):
    for attempt in range(max_retries):
        try:
            if isinstance(task_or_tasks, list):
                results = delegate_task(tasks=task_or_tasks)
            else:
                results = [delegate_task(**task_or_tasks)]

            if all(r['status'] == 'completed' for r in results):
                return results

            print(f"⚠️ {stage_name} attempt {attempt + 1} failed")
        except Exception as e:
            print(f"❌ {stage_name} error: {e}")

    raise Exception(f"❌ {stage_name} failed after {max_retries} attempts")
```

### Pattern 3: Rollback on Failure

```python
def run_with_rollback(stages):
    completed = []

    try:
        for stage in stages:
            results = run_stage(stage)
            completed.append((stage, results))
    except Exception as e:
        print(f"❌ Failed: {e}")
        for stage, results in reversed(completed):
            print(f"🔄 Rolling back {stage['name']}...")
            rollback_stage(stage, results)
        raise
```

### Pattern 4: Partial Continuation

```python
def run_orchestration_with_continuation(stages):
    results = {}
    failed_stages = []

    for stage in stages:
        try:
            results[stage['name']] = run_stage(stage)
        except Exception as e:
            failed_stages.append(stage['name'])
            # Continue only if remaining stages don't depend on the failed one
            remaining = stages[stages.index(stage)+1:]
            if any(s.get('depends_on') == stage['name'] for s in remaining):
                break
            else:
                print(f"⚠️ Continuing with non-dependent stages...")
                continue

    return {"results": results, "failed": failed_stages}
```

### Pattern 5: Timeout Handling

```python
context = """
TASK: <description>

TIMEOUT: 120 seconds
If timeout exceeded:
- Stop work immediately
- Report progress so far
- List remaining steps
"""
```

---

## 7. Performance Optimization

### Parallel Stage 3 (Conditional → Batch)

When multiple conditional branches are independent, collect qualifying tasks and batch them:

```python
stage3_tasks = []
if api_result['status'] == 'completed':
    stage3_tasks.append({"goal": "Rate limiting", ...})
if db_result['status'] == 'completed':
    stage3_tasks.append({"goal": "Migrations", ...})

if stage3_tasks:
    stage3_results = delegate_task(tasks=stage3_tasks)  # Parallel!
```

### Early Termination

```python
def run_with_early_termination(stages):
    for stage in stages:
        results = run_stage(stage)
        if stage['critical'] and not all_succeeded(results):
            print(f"❌ Critical stage {stage['name']} failed — terminating")
            return {"status": "failed", "failed_stage": stage['name']}
    return {"status": "completed"}
```

### Wave Splitting for Large Batches

```python
# Split 10 tasks into 2 waves of 5
delegate_task(tasks=tasks[:5])
delegate_task(tasks=tasks[5:])
```

### Benchmarks

| Scenario | Tasks | Sequential | Batch (3 slots) | Speedup |
|----------|-------|------------|-----------------|---------|
| Infrastructure setup | 5 | 627s | 216s | 2.9× |
| Module creation | 3 | 270s | 90s | 3.0× |
| Test addition | 4 | 120s | 45s | 2.7× |
| Refactoring | 3 | 240s | 90s | 2.7× |

**Factors affecting speedup:**

| Factor | Impact | Notes |
|--------|--------|-------|
| Task count variance | High | Uneven durations improve speedup |
| Task independence | Critical | Dependencies kill parallelism |
| Resource contention | Medium | CPU-bound benefits less from >3 slots |
| max_concurrent_children | Direct | 3 → ~2.5×, 5 → ~4× |

---

## 8. Monitoring & Reporting

```python
def track_orchestration(stages):
    report = {
        "start_time": time.time(),
        "stages": {},
        "completed_tasks": 0,
        "failed_tasks": 0
    }

    for stage in stages:
        stage_start = time.time()
        try:
            results = run_stage(stage)
            report["stages"][stage['name']] = {
                "status": "completed",
                "duration": time.time() - stage_start
            }
            report["completed_tasks"] += 1
        except Exception as e:
            report["stages"][stage['name']] = {
                "status": "failed",
                "duration": time.time() - stage_start,
                "error": str(e)
            }
            report["failed_tasks"] += 1

    report["total_time"] = time.time() - report["start_time"]
    return report
```

---

## 9. Common Pitfalls

### ❌ 1. Dependent Tasks in Batch

**Problem:**
```python
delegate_task(tasks=[
    {"goal": "Create module A"},
    {"goal": "Create module B that imports A"},  # May fail
])
```
**Fix:** Use sequential for dependent tasks, or batch independent groups separately.

### ❌ 2. Same-File Access Conflicts

**Problem:**
```python
delegate_task(tasks=[
    {"goal": "Modify calculator.py (add logging)"},
    {"goal": "Modify calculator.py (add type hints)"},  # Conflict!
])
```
**Fix:** Combine into one task, or run sequentially.

### ❌ 3. No Stage Validation (Ignoring Failures)

**Problem:**
```python
stage1_results = delegate_task(tasks=[...])
# Don't check, proceed to Stage 2 anyway
```
**Fix:** Always gate: check `r['status'] == 'completed'` before proceeding.

### ❌ 4. No Structured Output

**Problem:** Freeform output is hard to parse and aggregate.
**Fix:** Use the structured FINAL REPORT format in every task context.

### ❌ 5. Too Many Concurrent Tasks Without Tuning

**Problem:** 10 tasks with `max_concurrent_children=3` means 4 waves.
**Fix:** Increase limit for I/O-bound tasks, or split into explicit waves.

### ❌ 6. No Integration Testing

**Problem:** All stages pass individually but break together.
**Fix:** Always run Stage 4 integration tests after all other stages.

---

## 10. Integration with Other Skills

### With subagent-driven-development

```python
# Batch for independent tasks, then two-stage review
results = delegate_task(tasks=[...])
for result in results:
    if result['status'] == 'completed':
        delegate_task(goal="Review spec compliance", ...)
        delegate_task(goal="Review code quality", ...)
```

### With claude-code-subagent

```python
tasks = [
    {"goal": "Add feature via TDD", "context": get_claude_code_context("TDD Feature"), "toolsets": ["terminal", "file"]},
    {"goal": "Fix bug via TDD", "context": get_claude_code_context("Bug Fix with TDD"), "toolsets": ["terminal", "file"]}
]
delegate_task(tasks=tasks)
```

---

## Quick Reference (Hermes-Specific)

```
Independent tasks, different files  → delegate_task(tasks=[...])
Dependent tasks / same files        → delegate_task(goal=...)
Runtime conditions                  → if result OK → delegate_task(...)
Complex phased workflow             → 4-stage orchestration

Stage gating: always check status before proceeding
Structured output: essential for batch aggregation
Failure handling: always handle, never ignore
File conflicts: never batch tasks touching the same files
max_concurrent_children: 3 (default), 5 (I/O), 2 (CPU)
```

---

## Subagent-Driven Development (SDD)

Execute implementation plans by dispatching fresh subagents per task with systematic two-stage review.
This workflow is agent-agnostic — the Dispatch Template below shows Hermes `delegate_task` syntax,
but a Codex or Claude Code orchestrator should follow the same Stage 1–3 structure using its own
CLI-based delegation mechanism (see [CLI-Based Delegation](#cli-based-delegation-codex--claude-code)).

### Core Principle
Fresh subagent per task + two-stage review (spec then quality) = high quality, fast iteration.

### When to Use SDD
- You have an implementation plan (from writing-plans skill or user requirements).
- Tasks are mostly independent.
- Quality and spec compliance are important.

### SDD Workflow

**Stage 1: Plan Decomposition**
Break the plan into independent tasks, each with clear acceptance criteria. Tasks live in `docs/plans/tasks/`, board state in `docs/kanban.md`.

**Stage 2: Dispatch + Review Loop**
For each task:
1. Dispatch a fresh subagent with the task spec + relevant context. The subagent must open and execute the task file following [board-task-executor](../board-task-executor/SKILL.md) rules: read the task file, implement, validate against Definition of Done, update kanban and task status.
2. **Review Stage A (Spec)**: Did the subagent implement what was asked? Check against acceptance criteria.
3. **Review Stage B (Quality)**: Is the code well-structured, tested, no obvious bugs?
4. If either review fails: dispatch a new subagent with the review feedback + the original spec.

**Stage 3: Integration**
After all tasks pass review, run the full test suite and verify integration.

### Dispatch Template (Hermes-Specific)

Build `context` from the [Standard Subagent Prompt Envelope](../references/subagent-prompt-envelope.md)
so the fresh subagent has explicit paths and rules instead of a freeform description:

```
delegate_task(
  goal="Implement task X: <description>",
  context="<envelope filled in — see subagent-prompt-envelope.md>",
  toolsets=["terminal", "file"]
)
```

### Key Pitfalls
- Each subagent has NO memory of prior conversations — pass all context explicitly.
- Don't reuse subagents across tasks — fresh context prevents contamination.
- Review subagent results before telling the user — subagent summaries are self-reports.
- For external side-effects (HTTP POST, file writes), verify independently.

