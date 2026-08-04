# Docker Container Self-Recreate (Hermes Inside Docker)

When Hermes runs inside a Docker container and you need to modify the container's
own configuration (env vars, volumes, labels), you can't rely on `docker compose`
or `docker-compose` — they may not be installed inside the container.

## Problem

- `docker compose` — may not exist (no compose plugin in container)
- `docker-compose` — may not be installed (no standalone binary)
- Installing via `apt` or `curl` may fail (no network tools, permission denied)
- `docker restart` — does NOT reload environment variables; container must be recreated

## Solution: Manual Recreate via `docker run`

### Step 1: Gather current container parameters

```bash
# Get network, command, groups, restart policy, mounts
docker inspect hermes --format '{{json .HostConfig.NetworkMode}}'
docker inspect hermes --format '{{json .Config.Cmd}}'
docker inspect hermes --format '{{json .HostConfig.GroupAdd}}'
docker inspect hermes --format '{{json .HostConfig.RestartPolicy}}'
docker inspect hermes --format '{{range .Mounts}}{{.Type}}:{{.Source}}:{{.Destination}}:{{.Mode}} {{end}}'

# Get ALL labels (critical for Traefik routing!)
docker inspect hermes --format '{{json .Config.Labels}}'
```

### Step 2: Edit compose file (for future reference)

Compose file lives at the project path (e.g., `/services/hermes/compose/docker-compose.yml`).
Edit via `docker exec` since the host filesystem isn't directly visible:

```bash
# Backup
docker exec hermes cp /services/hermes/compose/docker-compose.yml /services/hermes/compose/docker-compose.yml.bak

# Edit (python works, vim/sed may not be available)
docker exec hermes python3 -c "
with open('/services/hermes/compose/docker-compose.yml') as f:
    content = f.read()
# ... modify content ...
with open('/services/hermes/compose/docker-compose.yml', 'w') as f:
    f.write(content)
"
```

### Step 3: Stop and rename old container

```bash
docker stop hermes
docker rename hermes hermes-old  # safety backup
```

### Step 4: Recreate with full parameters

Use Python subprocess (NOT bash string) to avoid escaping issues with backticks
in Traefik labels like `Host(\`hermes.smartbits.pro\`)`:

```python
import subprocess

cmd = [
    "docker", "run", "-d",
    "--name", "hermes",
    "--restart", "unless-stopped",
    "--group-add", "988",
    "--network", "proxy",
    "-v", "/root/services:/services:rw",
    "-v", "/root/services/hermes/data/hermes:/hermes:rw",
    "-v", "/var/run/docker.sock:/var/run/docker.sock:rw",
]

# Add env vars
for k, v in env_vars:
    cmd.extend(["-e", f"{k}={v}"])

# Add ALL Traefik labels (without them, Traefik won't route!)
for k, v in labels:
    cmd.extend(["--label", f"{k}={v}"])

cmd.extend(["hermes:latest", "hermes", "dashboard",
            "--host", "0.0.0.0", "--port", "9119",
            "--no-open", "--insecure"])

subprocess.run(cmd, capture_output=True, text=True, timeout=30)
```

### Step 5: Verify and cleanup

```bash
# Check env vars in new container
docker exec hermes sh -c 'echo "VAR=$VAR"'

# Remove old container if everything works
docker rm hermes-old
```

## Pitfalls

1. **Bash escaping with backticks**: Traefik label `Host(\`domain\`)` contains backticks
   that bash interprets as command substitution. Use Python `subprocess.run()` with list
   args, never build the command as a single string for bash.

2. **Passwords with `$`**: Values like `pass$word` need single-quote escaping in bash
   or use subprocess list args to avoid `$word` being treated as variable expansion.

3. **Missing labels = broken routing**: Forgetting Traefik labels means the container
   won't receive traffic. Copy ALL labels from `docker inspect`.

4. **`docker restart` is insufficient**: Environment variables are set at container
   creation time. `docker restart` reuses the existing container config — env changes
   won't take effect. Must destroy and recreate.

5. **Mount namespace isolation**: Hermes inside Docker can't directly read/write
   `/services` (bind mount from host). Use `docker exec hermes <cmd>` to access
   host files.

## Env File Location

On this deployment: `/services/hermes/compose/.env`
Variables defined there use `${VAR:-}` syntax in docker-compose.yml to pass through.

## Example: Adding/Updating Environment Variables

In this session, we added `AGENT_GITHUB_TOKEN` and updated `AGENT_GITHUB_PASS`:

```bash
# 1. Add variable to docker-compose.yml (inside container)
docker exec hermes sed -i '/AGENT_GITHUB_PASS=${AGENT_GITHUB_PASS:-}/a\      - AGENT_GITHUB_TOKEN=${AGENT_GITHUB_TOKEN:-}' /services/hermes/compose/docker-compose.yml

# 2. Stop and rename old container
docker stop hermes
docker rename hermes hermes-old

# 3. Recreate with updated env vars from .env
docker run -d \
  --name hermes \
  --restart unless-stopped \
  --network proxy \
  -e AGENT_GITHUB=the.loop@smartbits.pro \
  -e AGENT_GITHUB_PASS=3OpaU66LUca@9 \
  -e AGENT_GITHUB_TOKEN=*** \
  -v /root/services/hermes/data/hermes:/hermes \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /root/services:/services \
  --group-add 988 \
  <all other labels and parameters> \
  hermes:latest

# 4. Verify new variables are present
docker exec hermes env | grep AGENT_GITHUB
# Output should show:
# AGENT_GITHUB=the.loop@smartbits.pro
# AGENT_GITHUB_PASS=3OpaU66LUca@9
# AGENT_GITHUB_TOKEN=***

# 5. Remove old backup if verification succeeds
docker rm hermes-old
```

**Key insight**: `docker restart` does NOT reload environment variables from docker-compose.yml — it keeps the existing container's env. To apply changes, you must destroy and recreate the container.