---
name: debugging
description: "Debugging methodology and tools: systematic root cause analysis, Python (pdb/debugpy), Node.js (inspect/CDP), and Hermes TUI debugging."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [debugging, troubleshooting, root-cause, python, pdb, debugpy, nodejs, inspect, cdp, hermes, tui]
    related_skills: [test-driven-development, writing-plans, subagent-driven-development]
    absorbed_from: [systematic-debugging, python-debugpy, node-inspect-debugger, debugging-hermes-tui-commands]
---

# Debugging

Umbrella skill covering debugging methodology, Python debugging, Node.js debugging, and Hermes TUI slash-command debugging.

---

## Methodology: Systematic Root Cause Debugging

**Core principle:** ALWAYS find root cause before attempting fixes. Symptom fixes are failure.

### The Iron Law

```
NO FIXES WITHOUT ROOT CAUSE INVESTIGATION FIRST
```

### The Four Phases (complete each before the next)

**Phase 1 — Root Cause Investigation:**
1. **Read error messages carefully** — they often contain the exact solution. Read stack traces completely; note line numbers, file paths, error codes.
2. **Reproduce consistently** — if not reproducible, gather more data, don't guess.
   ```bash
   pytest tests/test_module.py::test_name -v --tb=long
   ```
3. **Check recent changes** — git diff, recent commits, new deps.
   ```bash
   git log --oneline -10
   git diff
   git log -p --follow src/problematic_file.py | head -100
   ```
4. **Gather evidence in multi-component systems** — log data at each component boundary, verify config propagation, check state at each layer.
5. **Trace data flow** — where does the bad value originate? Trace upstream to the source.

Phase 1 checklist: errors read, issue reproduced, recent changes reviewed, evidence gathered, problem isolated, root cause hypothesis formed.

**Phase 2 — Pattern Analysis:**
Find working examples, compare against references, identify every difference, understand dependencies.

**Phase 3 — Hypothesis and Testing:**
Form a single hypothesis, test with the smallest possible change, one variable at a time. If it doesn't work, form a NEW hypothesis — don't layer fixes.

**Phase 4 — Implementation:**
1. Create a failing test case (simplest reproduction).
2. Implement a single fix (no "while I'm here" changes).
3. Verify: regression test passes, full suite passes.
4. **Rule of Three:** if ≥3 fixes failed, STOP and question the architecture. Discuss with the user before more attempts.

### Red Flags — STOP and Return to Phase 1

- "Quick fix for now, investigate later"
- "Just try changing X and see if it works"
- Proposing solutions before tracing data flow
- "One more fix attempt" (when already tried 2+)
- Each fix reveals a new problem in a different place

### Quick Reference

| Phase | Key Activities | Success Criteria |
|-------|---------------|------------------|
| **1. Root Cause** | Read errors, reproduce, check changes, gather evidence, trace data flow | Understand WHAT and WHY |
| **2. Pattern** | Find working examples, compare, identify differences | Know what's different |
| **3. Hypothesis** | Form theory, test minimally, one variable at a time | Confirmed or new hypothesis |
| **4. Implementation** | Create regression test, fix root cause, verify | Bug resolved, all tests pass |

---

## Python Debugging (pdb + debugpy)

### Tool Selection

| Tool | When |
|---|---|
| **`breakpoint()` + pdb** | Local, interactive, simplest. Start here. |
| **`python -m pdb`** | Launch script under pdb with no source edits. |
| **`debugpy`** | Remote/headless/attach to running process. DAP protocol, IDE integration. |
| **`remote-pdb`** | Cleanest terminal-agent choice. Telnet-style pdb over TCP. |

Don't use for things `print()`/`logging.debug` solve in under a minute, or `pytest -vv --tb=long --showlocals` already reveals.

### pdb Quick Reference

| Command | Action |
|---|---|
| `h` / `h cmd` | help |
| `n` | next (step over) |
| `s` | step into |
| `r` | return from current function |
| `c` | continue |
| `unt N` | continue until line N |
| `l` / `ll` | list source / full function |
| `w` | where (stack trace) |
| `u` / `d` | up/down in stack |
| `a` | print function args |
| `p expr` / `pp expr` | print / pretty-print |
| `display expr` | auto-print on every stop |
| `b file:line` / `b func` | set breakpoint |
| `b file:line, cond` | conditional breakpoint |
| `tbreak file:line` | one-shot breakpoint |
| `!stmt` | execute arbitrary Python |
| `interact` | full Python REPL in current scope (Ctrl+D exit) |
| `q` | quit |

### Recipes

**Local breakpoint (easiest):**
```python
def compute(x, y):
    result = some_helper(x)
    breakpoint()           # drops into pdb here
    return result + y
```

**Launch script under pdb:**
```bash
python -m pdb path/to/script.py arg1 arg2
(Pdb) b path/to/script.py:42
(Pdb) c
```

**Debug a pytest test:**
```bash
pytest tests/test_file.py::test_name --pdb -p no:xdist   # pdb on failure
pytest tests/test_file.py::test_name --trace             # pdb at start
pytest tests/test_file.py --showlocals --tb=long         # no pdb, just locals
```

**Post-mortem on any exception:**
```bash
python -m pdb -c continue script.py   # pdb catches crash
```
```python
import pdb, sys
try:
    run_the_thing()
except Exception:
    pdb.post_mortem(sys.exc_info()[2])
```

**Remote debug with debugpy (attach to running process):**
```bash
pip install debugpy
```
Pattern A — source edit, wait for client:
```python
import debugpy
debugpy.listen(("127.0.0.1", 5678))
debugpy.wait_for_client()
debugpy.breakpoint()
```
Pattern B — no source edit:
```bash
python -m debugpy --listen 127.0.0.1:5678 --wait-for-client your_script.py
```
Pattern C — attach to PID:
```bash
python -m debugpy --listen 127.0.0.1:5678 --pid <pid>
```

**remote-pdb (cleanest for terminal agents):**
```bash
pip install remote-pdb
```
```python
from remote_pdb import set_trace
set_trace(host="127.0.0.1", port=4444)
```
```bash
nc 127.0.0.1 4444   # get (Pdb) prompt
```

### Pitfalls

1. **pdb under pytest-xdist silently does nothing.** Always use `-p no:xdist` or `-n 0`.
2. **`breakpoint()` in CI/non-TTY hangs.** Never commit it. Pre-commit grep: `rg -n 'breakpoint\(\)' --type py`
3. **`PYTHONBREAKPOINT=0`** disables all `breakpoint()` calls. Check env if breakpoint isn't hitting.
4. **`debugpy.listen` only blocks with `wait_for_client()`.** Without it, execution continues before client attaches.
5. **Attach-to-PID fails on hardened kernels.** Fix: `echo 0 | sudo tee /proc/sys/kernel/yama/ptrace_scope`
6. **pdb only debugs current thread.** For multithreaded, use debugpy (thread-aware DAP).
7. **asyncio:** `pdb` works in coroutines but `await` in pdb requires Python 3.13+. For older, use `interact` mode or `!stmt` tricks.
8. **Forking/multiprocessing:** pdb doesn't follow forks. Each child needs its own `breakpoint()`.

---

## Node.js Debugging (inspect + CDP)

### Tool Selection

- **`node inspect`** — built-in, zero install, CLI REPL. Prefer first.
- **`ndb` / CDP via `chrome-remote-interface`** — scriptable, automated breakpoints, scope capture.

### `node inspect` REPL Quick Reference

| Command | Action |
|---|---|
| `c` / `cont` | continue |
| `n` / `next` | step over |
| `s` / `step` | step into |
| `o` / `out` | step out |
| `pause` | pause running code |
| `sb('file.js', 42)` | set breakpoint |
| `sb('funcName')` | break on function |
| `cb('file.js', 42)` | clear breakpoint |
| `breakpoints` | list all |
| `bt` | backtrace |
| `list(5)` | show 5 lines around position |
| `watch('expr')` | auto-evaluate on pause |
| `repl` | JS REPL in current scope (Ctrl+C exit) |
| `exec expr` | evaluate once |
| `restart` / `kill` | restart or kill script |
| `.exit` | quit debugger |

### Recipes

**Launch paused on first line:**
```bash
node inspect path/to/script.js
node --inspect-brk $(which tsx) path/to/script.ts
```

**Attach to running process:**
```bash
kill -SIGUSR1 <pid>          # enable inspector
node inspect -p <pid>        # attach
# or by URL:
node inspect ws://127.0.0.1:9229/<uuid>
```

**Start with inspector from beginning:**
```bash
node --inspect script.js              # listen, keep running
node --inspect-brk script.js          # listen AND pause on first line
node --inspect=0.0.0.0:9230 script.js # custom host:port
```

**TypeScript via tsx:**
```bash
node --inspect-brk --import tsx script.ts
```

**Programmatic CDP (automated debugging):**
```bash
mkdir -p /tmp/cdp-tools && cd /tmp/cdp-tools && npm i chrome-remote-interface
```
```javascript
const CDP = require('chrome-remote-interface');
(async () => {
  const client = await CDP({ port: 9229 });
  const { Debugger, Runtime } = client;
  Debugger.paused(async ({ callFrames, reason }) => {
    const top = callFrames[0];
    console.log(`PAUSED: ${reason} @ ${top.url}:${top.location.lineNumber + 1}`);
    for (const scope of top.scopeChain) {
      if (scope.type === 'local' || scope.type === 'closure') {
        const { result } = await Runtime.getProperties({
          objectId: scope.object.objectId, ownProperties: true,
        });
        for (const p of result)
          console.log(`  ${scope.type}.${p.name} =`, p.value?.value ?? p.value?.description);
      }
    }
    await Debugger.resume();
  });
  await Runtime.enable();
  await Debugger.enable();
  await Debugger.setBreakpointByUrl({ urlRegex: '.*app\\.tsx$', lineNumber: 119 });
  await Runtime.runIfWaitingForDebugger();
})();
```

**Vitest tests under debugger:**
```bash
node --inspect-brk ./node_modules/vitest/vitest.mjs run --no-file-parallelism src/app/foo.test.tsx
```

**Heap snapshots & CPU profiles (via CDP):**
```javascript
// CPU profile
await client.Profiler.enable();
await client.Profiler.start();
await new Promise(r => setTimeout(r, 5000));
const { profile } = await client.Profiler.stop();
require('fs').writeFileSync('/tmp/cpu.cpuprofile', JSON.stringify(profile));

// Heap snapshot
await client.HeapProfiler.enable();
const chunks = [];
client.HeapProfiler.addHeapSnapshotChunk(({ chunk }) => chunks.push(chunk));
await client.HeapProfiler.takeHeapSnapshot({ reportProgress: false });
require('fs').writeFileSync('/tmp/heap.heapsnapshot', chunks.join(''));
```

### Pitfalls

1. **Wrong line numbers in TS source.** Breakpoints hit emitted JS, not `.ts`. Either break in `dist/*.js` or use `--enable-source-maps` (CDP clients only; `node inspect` CLI doesn't follow sourcemaps).
2. **`--inspect` vs `--inspect-brk`.** Use `--inspect-brk` when you need breakpoints before any code runs; `--inspect` races past.
3. **Port collisions.** Default is 9229. Use `--inspect=0` for random port. List targets: `curl -s http://127.0.0.1:9229/json/list`
4. **Child processes.** `--inspect` on parent does NOT inspect children. Propagate with `NODE_OPTIONS='--inspect-brk'`.
5. **Ctrl+C while paused** leaves target paused. `cont` first or `kill` explicitly.
6. **Security.** Always bind to `127.0.0.1` (default). `--inspect=0.0.0.0` exposes arbitrary code execution.

---

## Hermes TUI Slash Commands

### Architecture

```
Python backend (hermes_cli/commands.py)     <- canonical COMMAND_REGISTRY (source of truth)
       │
       ▼
TUI gateway (tui_gateway/server.py)         <- slash.exec / command.dispatch
       │
       ▼
TUI frontend (ui-tui/src/app/slash/)        <- local handlers + fallthrough
```

### Investigation Steps

1. **Check TUI frontend:**
   ```bash
   search_files --pattern "/commandname" --file_glob "*.ts" --path ui-tui/
   search_files --pattern "/commandname" --file_glob "*.tsx" --path ui-tui/
   ```

2. **Examine TUI command definition:**
   ```bash
   read_file ui-tui/src/app/slash/commands/core.ts
   ```

3. **Check Python backend:**
   ```bash
   search_files --pattern "CommandDef" --file_glob "*.py" --path hermes_cli/
   search_files --pattern "commandname" --path hermes_cli/commands.py --context 3
   ```

4. **Check gateway implementation:**
   ```bash
   search_files --pattern "complete.slash|slash.exec" --path tui_gateway/
   ```

### Fix: Missing Command Autocomplete

1. Add `CommandDef` to `COMMAND_REGISTRY` in `hermes_cli/commands.py`:
   ```python
   CommandDef("commandname", "Description", "Session",
              cli_only=True, aliases=("alias",),
              args_hint="[arg1|arg2]",
              subcommands=("arg1", "arg2")),
   ```
2. Set availability: `cli_only=True` (CLI/TUI only), `gateway_only=True` (messaging only), neither = everywhere, `gateway_config_gate="display.foo"` (config-gated).
3. For server-side commands, add handler in `HermesCLI.process_command()` (`cli.py`).
4. For gateway commands, add handler in `gateway/run.py`.

### Common Issues

1. **Command in TUI but not autocomplete** → missing from `COMMAND_REGISTRY`.
2. **Autocomplete shows but doesn't work** → check `tui_gateway/server.py` handler and `createSlashHandler.ts`. Local TUI handlers take precedence over gateway dispatch.
3. **Different behavior CLI vs TUI** → different implementations in `cli.py` vs TUI local handler.
4. **Config persists but UI doesn't update live** → must also patch nanostore state (`patchUiState(...)`) and thread through all render paths.
5. **Gateway silently ignores** → check `GATEWAY_KNOWN_COMMANDS` includes the canonical name; verify any `gateway_config_gate` is truthy.

### Debugging Tactics

- **Python side hangs:** use `remote-pdb` `set_trace()` inside `_SlashWorker.exec` or the command handler.
- **Ink side not reacting:** `node inspect` → `sb('dist/app.js', <line>)` after `npm run build`.
- **Registry mismatch:** compare `COMMAND_REGISTRY` entry against TUI's local command list side-by-side.

### Pitfalls

- Set correct category in `CommandDef`: "Session", "Configuration", "Tools & Skills", "Info", "Exit".
- Aliases propagate automatically downstream (Telegram, Slack, autocomplete, help) — no extra file changes.
- `subcommands` tuple must match TUI code.
- `cli_only=True` commands won't work in gateway unless `gateway_config_gate` is set and truthy.
- After adding live UI state, search ALL consumers of old prop/helper and thread new state through all render paths (not just active streaming path).
- **Rebuild TUI before testing:** `cd /home/bb/hermes-agent && npm --prefix ui-tui run build`

### Verification

1. Rebuild: `npm --prefix ui-tui run build`
2. Run TUI: `hermes --tui`
3. Type `/` → verify command in autocomplete with correct description/args.
4. Execute command → expected behavior, config updates, live UI reflects change.
5. For gateway commands, test from messaging platform or run `scripts/run_tests.sh tests/gateway/`.
