# Headless Server Auth Troubleshooting

## Problem

`claude auth login` and `claude auth login --console` both attempt to open a browser for OAuth. On headless/SSH-only servers without a browser installed, they fail:

```
Opening browser to sign in…
If the browser didn't open, visit: https://claude.com/cai/oauth/authorize?code=...&state=...
Paste code here if prompted >
```

The process hangs waiting for user input in the terminal, or errors if the terminal is not interactive.

## Solutions (in priority order)

### 1. API Key (Recommended)

Get key from https://console.anthropic.com/settings/keys, then:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

Verify: `claude auth status --text`

### 2. Local Login Then Copy Auth File

1. Run `claude auth login` on a machine with a browser (laptop, desktop)
2. Copy `~/.claude.json` to the server:
   ```bash
   scp ~/.claude.json user@server:~/.claude.json
   ```
3. Verify: `claude auth status --text`

### 3. Install Headless Browser

Option A — agent-browser cache:
```bash
agent-browser install
```

Option B — system package:
```bash
apt install chromium-browser  # Debian/Ubuntu
```

Then `claude auth login` will work normally.

## Pitfalls

- `--console` does NOT bypass the browser requirement — it still tries to open one
- `claude auth login` with `pty=true` alone in Hermes doesn't help — no browser = no OAuth
- Background terminal without pty hangs silently on the OAuth URL display