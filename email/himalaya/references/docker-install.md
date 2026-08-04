# Installing Himalaya in Docker/Restricted Environments

When `curl`, `wget`, `cargo`, and `apt-get` are all unavailable (common in
stripped Docker containers), install the pre-built binary via Python's
stdlib:

## Download + install via Python

```python
import urllib.request, json, shutil, os

# Get the latest release metadata
req = urllib.request.Request(
    'https://api.github.com/repos/pimalaya/himalaya/releases/latest'
)
req.add_header('User-Agent', 'Hermes')
with urllib.request.urlopen(req) as r:
    data = json.loads(r.read())

# Find the linux amd64 asset
for asset in data['assets']:
    name = asset['name']
    if 'linux' in name.lower() and ('x86_64' in name or 'amd64' in name):
        url = asset['browser_download_url']
        urllib.request.urlretrieve(url, '/tmp/himalaya.tar.gz')
        break

# Extract and install
os.system('tar xzf /tmp/himalaya.tar.gz -C /tmp/')
os.makedirs(os.path.expanduser('~/.local/bin'), exist_ok=True)

# MUST use shutil.copy2, NOT os.rename.
# /tmp and $HOME are often on different filesystems in Docker
# (overlay2 vs volume mount), causing OSError 18 "Invalid cross-device link".
shutil.copy2('/tmp/himalaya', os.path.expanduser('~/.local/bin/himalaya'))
os.chmod(os.path.expanduser('~/.local/bin/himalaya'), 0o755)
```

## Pitfalls

- **`OSError: [Errno 18] Invalid cross-device link`** — you used `os.rename`
  between `/tmp` (overlay2) and a volume mount. Use `shutil.copy2` instead.
- **`PermissionError` on `/usr/local/bin/`** — install to `~/.local/bin/`
  and add it to PATH.
- **`curl: command not found`** — don't pipe `curl | sh`; use the Python
  downloader above.
