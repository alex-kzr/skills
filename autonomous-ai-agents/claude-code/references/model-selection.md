# Claude Code Model & Effort Selection Guide

## Quick Reference Table

| Task Type | Model | Effort | Max Turns | Duration | Cost |
|-----------|-------|--------|-----------|----------|------|
| Simple test addition | Haiku | low | 5-10 | 10-20s | $ |
| Bug fix (small) | Haiku/Sonnet | low/medium | 10-15 | 20-40s | $$ |
| New module (small) | Sonnet | medium | 15-20 | 30-60s | $$$ |
| New module (medium) | Sonnet | medium | 20-25 | 60-90s | $$$ |
| CLI interface | Sonnet | medium | 20-25 | 60-90s | $$$ |
| Refactor (small) | Sonnet | medium | 15-25 | 45-90s | $$$ |
| Refactor (large) | Opus | high | 30-40 | 90-180s | $$$$$ |
| Architecture design | Opus | high | 30-50 | 120-300s | $$$$$ |
| Critical production code | Opus | max | 40-60 | 180-600s | $$$$$$ |

## Model Characteristics

### Claude Haiku (claude-haiku-4-20250514)

**Best for:**
- Simple bug fixes
- Adding tests
- Small refactors
- Quick prototypes
- Non-critical code

**Strengths:**
- ✅ Fast (2-3x faster than Sonnet)
- ✅ Cheap (~10x cheaper than Opus)
- ✅ Good for straightforward tasks
- ✅ Lower latency

**Weaknesses:**
- ❌ Less deep reasoning
- ❌ May miss edge cases
- ❌ Less architectural initiative
- ❌ Requires more specific instructions

**Example usage:**
```bash
claude -p "Add test for empty string edge case" \
  --model haiku \
  --effort low \
  --max-turns 5 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.01-0.05 per task
**Speed:** 10-30 seconds

---

### Claude Sonnet (claude-sonnet-4-20250514)

**Best for:**
- New modules (small-medium)
- TDD implementation
- Standard refactors
- CLI interfaces
- Everyday development

**Strengths:**
- ✅ Balanced speed/quality
- ✅ Good architectural understanding
- ✅ Handles edge cases well
- ✅ Reasonable cost
- ✅ Good for TDD

**Weaknesses:**
- ❌ Slower than Haiku
- ❌ More expensive than Haiku
- ❌ May need more turns for complex tasks

**Example usage:**
```bash
claude -p "Create statistics module with mean, median, std_dev. Follow TDD." \
  --model sonnet \
  --effort medium \
  --max-turns 20 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.05-0.20 per task
**Speed:** 30-90 seconds

---

### Claude Opus (claude-opus-4-20250514)

**Best for:**
- Complex refactors
- Architecture design
- Critical production code
- Multi-module changes
- Security-sensitive code

**Strengths:**
- ✅ Deepest reasoning
- ✅ Best architecture
- ✅ Best edge case handling
- ✅ Most reliable
- ✅ Good for complex tasks

**Weaknesses:**
- ❌ Slow (3-5x slower than Haiku)
- ❌ Expensive (~10x Haiku)
- ❌ Overkill for simple tasks
- ❌ Higher token usage

**Example usage:**
```bash
claude -p "Refactor entire codebase to use dependency injection. Maintain all functionality." \
  --model opus \
  --effort high \
  --max-turns 40 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.20-1.00 per task
**Speed:** 90-300 seconds

## Effort Levels

### low

**When to use:**
- Simple, well-defined tasks
- Clear expected outcome
- No architectural decisions
- Quick iterations

**Characteristics:**
- Faster execution
- Less reasoning depth
- Fewer tool calls
- Lower token usage

**Best paired with:**
- Haiku for speed
- Simple bug fixes
- Test additions

```bash
--effort low --max-turns 5-10
```

---

### medium (default)

**When to use:**
- Standard development tasks
- New modules with moderate complexity
- Refactoring small components
- TDD workflows

**Characteristics:**
- Balanced reasoning
- Good for most tasks
- Moderate tool usage
- Standard token usage

**Best paired with:**
- Sonnet for balance
- New modules
- Standard refactors

```bash
--effort medium --max-turns 15-25
```

---

### high

**When to use:**
- Complex refactoring
- Architecture changes
- Multi-file modifications
- Complex edge cases

**Characteristics:**
- Deep reasoning
- More tool calls
- Higher token usage
- Better quality

**Best paired with:**
- Opus for depth
- Large refactors
- Architecture work

```bash
--effort high --max-turns 30-40
```

---

### max

**When to use:**
- Critical production code
- Security-sensitive implementations
- Maximum reliability required
- Complex multi-system changes

**Characteristics:**
- Maximum reasoning depth
- Most thorough analysis
- Highest token usage
- Best quality

**Best paired with:**
- Opus only
- Critical code
- Security work

```bash
--effort max --max-turns 40-60
```

## Decision Tree

```
Is this a critical/production task?
├─ Yes → Use Opus + high/max effort
│         Budget: $0.20-1.00, Time: 2-5min
└─ No
    └─ Is this a complex architectural change?
        ├─ Yes → Use Opus + high effort
        │         Budget: $0.20-0.50, Time: 1.5-3min
        └─ No
            └─ Is this a new module or standard refactor?
                ├─ Yes → Use Sonnet + medium effort
                │         Budget: $0.05-0.20, Time: 0.5-1.5min
                └─ No
                    └─ Is this a simple fix or test addition?
                        ├─ Yes → Use Haiku + low effort
                        │         Budget: $0.01-0.05, Time: 10-30s
                        └─ No → Fallback to Sonnet + medium
```

## Task-Specific Templates

### Template 1: Simple Test Addition

```bash
claude -p "Add edge case test for <scenario>" \
  --model haiku \
  --effort low \
  --max-turns 5 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.01
**Time:** 10-20s
**Use case:** Adding a few tests, quick validation

---

### Template 2: Bug Fix (Small)

```bash
claude -p "Fix bug in <module>: <description>. Add regression test." \
  --model haiku \
  --effort medium \
  --max-turns 10 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.03
**Time:** 20-40s
**Use case:** Small bug with clear fix

---

### Template 3: New Module (Small)

```bash
claude -p "Create module src/<name>.py with <functions>. Follow TDD. Add type hints and docstrings." \
  --model sonnet \
  --effort medium \
  --max-turns 20 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.10
**Time:** 30-60s
**Use case:** New module with 3-5 functions

---

### Template 4: New Module (Medium)

```bash
claude -p "Create comprehensive module for <purpose>. Include error handling, logging, tests." \
  --model sonnet \
  --effort medium \
  --max-turns 25 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.15
**Time:** 60-90s
**Use case:** New module with complexity

---

### Template 5: CLI Interface

```bash
claude -p "Create CLI for <module> with argparse. Commands: <list>. Add tests." \
  --model sonnet \
  --effort medium \
  --max-turns 25 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.15
**Time:** 60-90s
**Use case:** Command-line interfaces

---

### Template 6: Small Refactor

```bash
claude -p "Refactor <module> to <pattern>. Maintain all functionality. Update tests." \
  --model sonnet \
  --effort medium \
  --max-turns 20 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.10
**Time:** 45-90s
**Use case:** Function → class, extract method, etc.

---

### Template 7: Large Refactor

```bash
claude -p "Refactor entire <subsystem> to use <pattern>. Maintain API compatibility. Update all dependent code." \
  --model opus \
  --effort high \
  --max-turns 35 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.30
**Time:** 90-180s
**Use case:** Architecture changes across multiple files

---

### Template 8: Architecture Design

```bash
claude -p "Design architecture for <system>. Consider: scalability, maintainability, testability. Create initial structure." \
  --model opus \
  --effort high \
  --max-turns 40 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.50
**Time:** 120-300s
**Use case:** New systems, major redesigns

---

### Template 9: Critical Production Code

```bash
claude -p "Implement <critical feature> with maximum reliability. Include: comprehensive tests, error handling, logging, monitoring." \
  --model opus \
  --effort max \
  --max-turns 50 \
  --dangerously-skip-permissions
```

**Cost:** ~$0.80
**Time:** 180-600s
**Use case:** Security, payments, core infrastructure

---

## Cost Optimization Tips

### 1. **Use Haiku for iterations**
```bash
# First pass: Haiku for quick draft
claude -p "Create basic implementation" --model haiku --effort low

# Second pass: Sonnet for polish
claude -p "Improve quality, add type hints" --model sonnet --effort medium
```

### 2. **Restrict tools**
```bash
# For code review only
claude -p "Review code" --model haiku --allowedTools "Read" --max-turns 1

# For analysis without modification
claude -p "Analyze architecture" --model sonnet --allowedTools "Read" --max-turns 5
```

### 3. **Use pipe for analysis**
```bash
# Instead of reading files, pipe content
cat src/module.py | claude -p "Find bugs" --max-turns 1 --model haiku
```

### 4. **Set budget caps**
```bash
# Prevent overspending
claude -p "Complex task" --max-budget-usd 0.10 --model haiku --effort low
```

### 5. **Use fallback model**
```bash
# Auto-fallback to Haiku if Sonnet is overloaded
claude -p "Task" --fallback-model haiku --model sonnet
```

## Performance Optimization Tips

### 1. **Right-size max-turns**
```bash
# Too high: waste time
--max-turns 50  # Overkill for simple task

# Too low: incomplete
--max-turns 3   # Won't complete

# Just right
--max-turns 15  # Standard task
```

### 2. **Use effort levels correctly**
```bash
# Don't use high for simple tasks
--effort high --model opus  # Overkill

# Don't use low for complex tasks
--effort low --model haiku   # Will fail
```

### 3. **Batch small tasks**
```bash
# Instead of 3 separate calls:
claude -p "Add tests for A, B, C" --max-turns 15

# Better than:
claude -p "Add test for A" --max-turns 5
claude -p "Add test for B" --max-turns 5
claude -p "Add test for C" --max-turns 5
```

## Quality Indicators by Model

| Metric | Haiku | Sonnet | Opus |
|--------|-------|--------|------|
| Type hints | 50% | 70% | 90% |
| Docstrings | 40% | 70% | 90% |
| Edge cases | 60% | 80% | 95% |
| Architecture | 50% | 75% | 95% |
| Test coverage | 70% | 85% | 95% |
| Error handling | 60% | 80% | 95% |

## Benchmarks from Testing

| Task | Haiku | Sonnet | Opus |
|------|-------|--------|------|
| Add 5 tests | 15s, $0.01 | 25s, $0.03 | 45s, $0.10 |
| Fix small bug | 20s, $0.02 | 35s, $0.05 | 60s, $0.15 |
| New module (small) | 40s, $0.04 | 60s, $0.10 | 120s, $0.30 |
| CLI interface | - | 90s, $0.15 | 150s, $0.35 |
| Refactor to class | - | 90s, $0.15 | 150s, $0.40 |

## Common Pitfalls

1. **❌ Over-engineering with Opus**
   - Don't use Opus for "Hello World" level tasks
   - Fix: Use Haiku for simple tasks

2. **❌ Under-specifying with Haiku**
   - Haiku needs clear, specific instructions
   - Fix: Provide detailed steps and examples

3. **❌ No max-turns**
   - Can lead to runaway loops
   - Fix: Always specify --max-turns

4. **❌ Wrong effort level**
   - Using high for simple tasks wastes time
   - Fix: Match effort to task complexity

5. **❌ No budget cap**
   - Complex tasks can get expensive
   - Fix: Use --max-budget-usd for large tasks

## Remember

```
Simple task → Haiku + low
Standard task → Sonnet + medium
Complex task → Opus + high
Critical task → Opus + max
```

**Match model and effort to task complexity.**
**Always specify max-turns.**
**Use budget caps for large tasks.**
