# Claude Code Subagent Orchestration — delegate_task Templates

Effective patterns for delegating coding tasks to Claude Code via `delegate_task`.

## When to Use

Use these templates when:
- You need to execute coding tasks via Claude Code
- Tasks require TDD, refactoring, or multi-step implementation
- You want predictable, structured output from subagents
- Tasks benefit from environment validation and progress tracking

## Core Pattern

### Standard delegate_task for Claude Code

```python
delegate_task(
    goal="<brief task description>",
    context=f"""
    TASK: <detailed task description>
    
    ENVIRONMENT CHECK:
    1. Check tools: pytest --version, python3 --version
    2. If missing, install: pip install pytest -q
    3. Verify project: ls -la src/ tests/
    
    STRICT PROCESS:
    Step 1: <action>
      - Expected: <outcome>
    
    Step 2: <action>
      - Run: <command>
      - Expected: <outcome>
    
    [Continue for all steps]
    
    PROGRESS REPORTING:
    After EACH step, report:
    - Step completed: YES/NO
    - Command output (if any)
    - Any errors or issues
    
    MAX TURNS: <number>
    If incomplete after MAX TURNS:
    - Stop work
    - Report partial progress
    - List remaining steps
    
    FINAL REPORT FORMAT:
    ## Summary
    - Task completed: YES/NO
    - Files created/modified: [list]
    - Tests passing: [count]/[total]
    - Issues: [list]
    - Remaining work: [list if incomplete]
    """,
    toolsets=['terminal', 'file']
)
```

## Task Templates

### Template 1: TDD Feature Addition

```python
delegate_task(
    goal="Add <feature> to <module> following strict TDD",
    context=f"""
    TASK: Add <feature> to <module>
    
    ENVIRONMENT CHECK:
    1. pytest --version (install if missing)
    2. Verify project structure
    
    STRICT TDD PROCESS:
    Step 1: Write tests for <feature> in tests/test_<module>.py
      - Test basic functionality
      - Test edge cases
      - Test error handling
      - Expected: pytest will FAIL
    
    Step 2: Run: pytest tests/test_<module>.py -v
      - Verify: new tests FAIL
      - Report: which tests fail
    
    Step 3: Implement <feature> in src/<module>.py
      - Add type hints
      - Add Google-style docstring
      - Handle edge cases
      - Expected: code compiles
    
    Step 4: Run: pytest tests/test_<module>.py -v
      - Verify: all new tests PASS
      - Report: test results
    
    Step 5: Run: pytest tests/ -q
      - Verify: no regressions (old tests still pass)
      - Report: full suite results
    
    PROGRESS REPORTING:
    After EACH step: Report completion + pytest output
    
    MAX TURNS: 20
    
    FINAL REPORT FORMAT:
    ## Summary
    - Feature implemented: YES/NO
    - Tests created: YES/NO
    - New tests passing: [count]/[total]
    - Old tests still passing: YES/NO
    - Files modified: [list]
    - Issues: [list]
    """,
    toolsets=['terminal', 'file']
)
```

### Template 2: Bug Fix with TDD

```python
delegate_task(
    goal="Fix bug in <module>: <bug description>",
    context=f"""
    TASK: Fix bug in <module>
    
    BUG: <description>
    FILE: <file path>
    LINE: <if known>
    
    ENVIRONMENT CHECK:
    1. pytest --version (install if missing)
    2. Run: pytest tests/ -v (capture current state)
    
    BUG FIX PROCESS:
    Step 1: Add failing test that reproduces bug
      - File: tests/test_<module>.py
      - Expected: pytest FAIL
    
    Step 2: Run: pytest tests/test_<module>.py -v
      - Verify: new test FAILS (reproduces bug)
    
    Step 3: Fix bug in src/<module>.py
      - Minimal change only
      - Don't refactor unless necessary
      - Add regression test comment
    
    Step 4: Run: pytest tests/ -v
      - Verify: all tests PASS
      - Report: which tests pass
    
    Step 5: Run: pytest tests/ -q
      - Verify: no regressions
      - Report: full count
    
    PROGRESS REPORTING:
    After EACH step: Report completion + pytest output
    
    MAX TURNS: 15
    
    FINAL REPORT FORMAT:
    ## Summary
    - Bug fixed: YES/NO
    - Reproduction test added: YES/NO
    - All tests passing: YES/NO
    - Files modified: [list]
    - Changes summary: <brief description>
    - Issues: [list]
    """,
    toolsets=['terminal', 'file']
)
```

### Template 3: Refactoring

```python
delegate_task(
    goal="Refactor <module> to <pattern>",
    context=f"""
    TASK: Refactor <module> to <pattern>
    
    CURRENT: <current architecture/implementation>
    TARGET: <desired pattern/architecture>
    
    ENVIRONMENT CHECK:
    1. pytest --version (install if missing)
    2. Run: pytest tests/ -v (baseline)
    3. Record: <test count> tests passing
    
    REFACTORING PROCESS:
    Step 1: Read current implementation
      - File: src/<module>.py
      - Understand existing structure
    
    Step 2: Design refactor approach
      - Plan: changes needed
      - Risk: what might break
    
    Step 3: Apply refactor in small steps
      - Change 1: <description>
      - Run: pytest tests/ -v
      - Change 2: <description>
      - Run: pytest tests/ -v
      - [Continue as needed]
    
    Step 4: Update tests if necessary
      - File: tests/test_<module>.py
      - Update imports if API changed
      - Add new tests if needed
    
    Step 5: Final verification
      - Run: pytest tests/ -v
      - Verify: all tests PASS
      - Verify: same test count as baseline
    
    PROGRESS REPORTING:
    After EACH refactor step: Report change + pytest output
    
    MAX TURNS: 30
    
    FINAL REPORT FORMAT:
    ## Summary
    - Refactor completed: YES/NO
    - Tests still passing: YES/NO
    - Test count: <final> / <baseline>
    - Files modified: [list]
    - Refactor changes: <summary>
    - Issues: [list]
    """,
    toolsets=['terminal', 'file']
)
```

### Template 4: New Module with Tests

```python
delegate_task(
    goal="Create new module <name> with <functions>",
    context=f"""
    TASK: Create new module src/<name>.py
    
    REQUIREMENTS:
    - Functions: <list of functions>
    - Type hints: required
    - Docstrings: Google style
    - Tests: comprehensive coverage
    - Error handling: edge cases
    
    ENVIRONMENT CHECK:
    1. pytest --version (install if missing)
    2. Verify project structure
    
    MODULE CREATION PROCESS:
    Step 1: Create test file tests/test_<name>.py
      - Test each function
      - Test edge cases
      - Test error handling
      - Expected: pytest FAIL
    
    Step 2: Run: pytest tests/test_<name>.py -v
      - Verify: all tests FAIL
    
    Step 3: Create module src/<name>.py
      - Implement all functions
      - Add type hints
      - Add Google-style docstrings
      - Handle edge cases
    
    Step 4: Run: pytest tests/test_<name>.py -v
      - Verify: all tests PASS
    
    Step 5: Run: pytest tests/ -q
      - Verify: no regressions
    
    PROGRESS REPORTING:
    After EACH step: Report completion + pytest output
    
    MAX TURNS: 25
    
    FINAL REPORT FORMAT:
    ## Summary
    - Module created: YES/NO
    - Functions implemented: <count> / <required>
    - Tests created: <count>
    - All tests passing: YES/NO
    - Files created: [list]
    - Issues: [list]
    """,
    toolsets=['terminal', 'file']
)
```

## Quality Gates

Always include these checks in context:

```python
context += """
QUALITY GATES (must pass before completing):
- All tests passing: pytest tests/ -v
- No lint errors: ruff check src/ (if ruff available)
- Type check: mypy src/ (if mypy configured)
- No regressions: compare test count to baseline
"""
```

## Environment Validation Pattern

```python
context += """
ENVIRONMENT VALIDATION:
1. Check Python: python3 --version
2. Check pytest: pytest --version
3. Check project structure: ls -la
4. If any missing: install or report issue

DEPENDENCY INSTALLATION:
- pytest: pip install pytest -q
- Other deps: pip install <name> -q
- Update requirements.txt: pip freeze > requirements.txt
"""
```

## Error Handling in Context

```python
context += """
ERROR HANDLING:
If pytest fails with import error:
  - Check __init__.py exists in packages
  - Fix imports
  - Try again (max 3 attempts)

If test fails after implementation:
  - Read error message
  - Fix implementation
  - Re-run test (max 3 attempts)

If still failing after 3 attempts:
  - Stop work
  - Report error with full traceback
  - List attempted fixes
"""
```

## Progress Tracking Pattern

```python
context += """
PROGRESS TRACKING:
After EVERY major step, report:
- Step number and name
- Completed: YES/NO
- Output from tools (pytest, git, etc.)
- Any warnings or errors
- Next step planned

Example:
=== Step 2 Complete ===
- Run: pytest tests/ -v
- Output: 10 tests passed, 2 failed
- Issues: test_power_negative_exponent failed
- Next step: Fix implementation
"""
```

## Max Turns Guidance

| Task Type | Recommended Max Turns |
|-----------|----------------------|
| Simple bug fix | 10-15 |
| TDD feature addition | 15-20 |
| Small refactor | 20-25 |
| New module with tests | 20-30 |
| Large refactor | 30-40 |

Always include:
```python
context += f"""
MAX TURNS: {recommended}
If incomplete after {recommended} turns:
- Stop work
- Report partial progress
- List completed steps
- List remaining steps
"""
```

## Structured Output for Parsing

For automation, use structured reports:

```python
context += """
FINAL REPORT FORMAT (structured):
## Summary
- Task completed: YES/NO
- Files created: [list]
- Files modified: [list]
- Files deleted: [list]
- Tests created: <count>
- Tests passing: <count> / <total>
- Regressions: <count>
- Issues: [list]
- Remaining work: [list if incomplete]

## Details
[Additional details if needed]

This format is parseable for automation.
"""
```

## Common Pitfalls

1. **❌ Skipping environment check**
   - Fix: Always check pytest version first

2. **❌ No progress reporting**
   - Fix: Require report after EACH step

3. **❌ Unclear turn limits**
   - Fix: Always specify MAX TURNS

4. **❌ Vague instructions**
   - Fix: Be specific: "Run: pytest tests/ -v" not "run tests"

5. **❌ Missing final report format**
   - Fix: Always specify FINAL REPORT FORMAT

6. **❌ No error handling instructions**
   - Fix: Specify what to do on failures

7. **❌ Skipping regression checks**
   - Fix: Always run full test suite after changes

8. **❌ No quality gates**
   - Fix: Specify what must pass before completion

## Integration with subagent-driven-development

These templates complement `subagent-driven-development`:

1. **Use these templates** for creating delegate_task contexts
2. **Use subagent-driven-development** for two-stage reviews
3. **Combine** for full workflow:
   ```python
   # Step 1: Implement via Claude Code (these templates)
   delegate_task(goal="...", context=..., toolsets=['terminal', 'file'])
   
   # Step 2: Spec review (subagent-driven-development)
   delegate_task(goal="Review spec compliance", context=..., toolsets=['file'])
   
   # Step 3: Quality review (subagent-driven-development)
   delegate_task(goal="Review code quality", context=..., toolsets=['file'])
   ```

## Remember

```
Environment check first
Step-by-step instructions
Progress after each step
Structured final report
Explicit turn limits
Quality gates before completion
```

**Consistency beats cleverness.** Same pattern every time → predictable results.
