# GitHub Web Automation: Login & Token Creation

## Problem

GitHub actively blocks automated web login attempts. Running `curl` or `requests` to POST `/session` with username/password **will fail** — even with correct credentials, proper headers, and CSRF tokens.

## Signals of Blocked Login

- HTTP 200 (no redirect to dashboard)
- Session cookie `logged_in=no`
- HTML error: *"There have been several failed attempts to sign in from this account or IP address. Please wait a while and try again later."*

## Why It Fails

1. **JavaScript challenge** — GitHub's login form sets `javascript-support: unknown` by default. Changing to `true` isn't enough; the server expects a JS-computed token from the client-side script.
2. **Rate limiting** — ~5 failed attempts from one IP triggers a temporary block (~30-60 minutes).

## What Actually Works

### For Git Operations Only (clone/push/pull)

GitHub still accepts password-based Basic Auth for the **Git HTTP transport**. A `credential.helper store` with username:password works fine:

```bash
git config --global credential.helper store
echo "https://user:password@github.com" > ~/.git-credentials
git ls-remote https://github.com/git/git.git HEAD  # should work
```

### For API Access

You **must** have a Personal Access Token (classic). Password alone won't work for the REST API (returns 401 "Requires authentication").

The Authorizations API (`POST /authorizations`) that used to allow creating tokens via Basic Auth is **fully removed** (returns 404).

### Creating a Token Programmatically

Options:
1. **User provides an existing token** — use `gh auth login --with-token` or export `GITHUB_TOKEN`
2. **Manual browser flow** — user creates the token at https://github.com/settings/tokens
3. **Headless browser** — Playwright/Selenium can handle the login (JS challenge) and token creation form. Heavy dependency, not recommended for one-off setup.

## Device Verification

When GitHub detects a login from a new device/IP, it sends a verification code to the account email. This happens AFTER a successful password check redirects to `/sessions/verified-device`.

### Retrieving the Code via IMAP

Use Python's `imaplib` to fetch the verification code from email:

```python
import imaplib, email, re

conn = imaplib.IMAP4_SSL('imap.example.com', 993)
conn.login('user@example.com', 'password')
conn.select('INBOX')

# Search for GitHub verification emails
status, msgs = conn.search(None, 'FROM', 'noreply@github.com')
for eid in reversed(msgs[0].split()[-5:]):  # last 5
    _, data = conn.fetch(eid, '(RFC822)')
    msg = email.message_from_bytes(data[0][1])
    
    # Extract body
    body = ''
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == 'text/plain':
                body = part.get_payload(decode=True).decode(errors='replace')
                break
    else:
        body = msg.get_payload(decode=True).decode(errors='replace')
    
    # Find 6-8 digit verification code
    codes = re.findall(r'\b(\d{6,8})\b', body)
    if codes:
        print(f'Code: {codes[0]}')  # e.g., 217720
        break

conn.logout()
```

The IMAP server may reject multi-keyword searches (e.g., `SUBJECT "verification code"`). Use only `FROM` as the search criterion and filter client-side.

### Submitting the Code

```python
# Get the verified-device page
resp = session.get('https://github.com/sessions/verified-device')
soup = BeautifulSoup(resp.text, 'html.parser')
auth_token = soup.find('input', {'name': 'authenticity_token'})['value']

# Submit verification code
session.post('https://github.com/sessions/verified-device', data={
    'authenticity_token': auth_token,
    'otp': '217720',
})
```

After successful verification, the session is authenticated and can access `/settings/tokens/new`.

## Pitfalls

- **Don't retry in a loop.** If `logged_in=no` appears, stop — the IP is rate-limited.
- **The `_gh_sess` cookie is the session identifier.** Without a valid one, every page redirects to `/login`.
- **The verification code is single-use.** If the first login attempt triggers device verification, the code is tied to that session's cookie jar. Re-using the same code with a fresh jar fails.
- **curl `-L` (follow redirects) can lose POST cookies.** When POSTing to `/session`, let curl return the redirect response, then manually GET the `Location` URL with the cookie jar.
