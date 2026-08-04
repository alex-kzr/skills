# Hermes Docker Container: Git & GitHub Setup

When the agent runs inside the Hermes Docker container, several environment quirks affect GitHub setup.

## Mount Namespace Isolation

The Hermes agent process may run in a different mount namespace than the container's root filesystem. **Binaries installed via `apt-get install` inside the container may not be visible to the agent process.**

**Rule**: always run git/curl/gh commands via `docker exec hermes <command>`, never directly.

```bash
# RIGHT — works
docker exec hermes git --version

# WRONG — git may not be in agent's PATH
git --version
```

Installing packages requires root:
```bash
docker exec -u root hermes apt-get update -qq
docker exec -u root hermes apt-get install -y -qq git curl
```

## Home Directory

The `hermes` user's home is `/hermes/home/`, NOT `/root/`.

```bash
docker exec hermes id
# uid=1001(hermes) gid=0(root) home=/hermes/home
```

All git config and credentials go under this home:
```bash
docker exec hermes git config --global user.name "Name"
docker exec hermes git config --global user.email "email@example.com"
docker exec hermes git config --global credential.helper store
```

## Credential File

`.git-credentials` must be at `/hermes/home/.git-credentials`, owned by `hermes:root`, mode 600.

**Correct setup:**
```bash
# Write as root, then fix ownership
docker exec -u root hermes bash -c 'echo "https://user:TOKEN@github.com" > /hermes/home/.git-credentials && chown hermes:root /hermes/home/.git-credentials && chmod 600 /hermes/home/.git-credentials'
```

**Common pitfall**: writing to `/root/.git-credentials` — this will be inaccessible to the `hermes` user and git won't read it.

## Environment Variables

Environment variables set via `docker run --env` are visible in `docker inspect` but may NOT be in the agent process's environment. To read them:

```bash
# Check what's declared for the container
docker inspect hermes --format '{{range .Config.Env}}{{println .}}{{end}}' | grep AGENT_

# Check what the agent's process actually sees
docker exec hermes env | grep AGENT_ || echo "Not in agent process env"

# Check container PID 1's environment
docker exec hermes cat /proc/1/environ | tr '\0' '\n' | grep AGENT_
```

**Key insight**: the agent process may have a restricted environment. Always verify with `docker inspect` first, then pass needed vars explicitly with `docker exec -e VAR=value`. Do not assume `$VAR` is set in the agent's shell.

Common pattern when env vars are missing from the agent but visible in `docker inspect`:
```bash
# Read from docker inspect and pass explicitly
docker exec -e VAR=$(docker inspect hermes --format '{{range .Config.Env}}{{if eq (index (split . "=") 0) "VAR"}}{{index (split . "=") 1}}{{end}}{{end}}') hermes <command>
```

## Verification

```bash
# Test git HTTPS auth
docker exec hermes git ls-remote https://github.com/git/git.git HEAD

# Test API (requires PAT, password won't work)
docker exec hermes curl -s -H "Authorization: token $TOKEN" https://api.github.com/user
```
