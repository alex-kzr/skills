---
name: playwright-page-opening
description: "Open pages via Playwright, verify loading, inspect state, and update Confluence pages. Covers generic safe page opening, Confluence-specific page opening (auth, expand macros, SPA rendering), and Confluence page updating. Formerly split into playwright-page-opening + playwright-confluence-page-opener + playwright-confluence-page-updater."
---

# Playwright Page Operations

Use Playwright to open web pages, verify loading, inspect visible state, and update Confluence pages. This skill covers three related workflows.

---

## Generic Page Opening

Open a URL in Playwright, verify it loads, inspect visible state, and report the result. Safe (read-only) operations only.

### When to Use
- Open a specific URL and check whether it loads.
- Capture title, URL, visible text, screenshot.
- Verify page elements before further interaction.

### Workflow
1. Navigate to URL.
2. Wait for load state (`networkidle` or `domcontentloaded`).
3. Capture: title, URL, visible text, screenshot (if needed).
4. Report: load status, key elements, any errors.

### Safety Constraints
- Do NOT submit forms, click buttons that change state, or interact with sensitive data unless explicitly requested.
- Limit to observation and reporting.

### Example
```js
const { chromium } = require('playwright');
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url, { waitUntil: 'networkidle' });
const title = await page.title();
const content = await page.textContent('body');
```

---

## Confluence Page Opening

Specialized page opening for Atlassian Confluence Cloud — handles SPA rendering, authentication, expand macros.

### Additional Steps vs Generic
1. **Authentication**: Use `storageState` (saved browser session) or Basic Auth headers.
2. **SPA wait**: Confluence is a SPA — wait `5000ms` after initial load for dynamic content.
3. **Expand macros**: Click all expand buttons to reveal hidden content.
4. **State classification**: loaded / login_required / access_denied / page_not_found / timeout.
5. **Metadata extraction**: title, breadcrumbs, last updated, page ID, visible content text.

### Expand Macro Pattern
```js
const expandButtons = page.locator('[data-testid="expand-container"] button, .expand-control, [aria-label="Expand"]');
const count = await expandButtons.count();
for (let i = 0; i < count; i++) {
  try { await expandButtons.nth(i).click({ timeout: 1000 }); await page.waitForTimeout(300); } catch {}
}
```

### Page Load Verification
- Check for `#content` or `.wiki-content` element.
- Check for login redirect: URL contains `/login.action` or login form present.
- Check for 404: `.error-panel` or "Page Not Found" text.

---

## Confluence Page Updating

Update Confluence Cloud pages via Playwright — either through browser UI automation or by combining Playwright auth with REST API calls.

### Approach A: Browser UI
1. Authenticate with saved `storageState`.
2. Navigate to page, click "Edit".
3. Modify content in editor.
4. Click "Publish" / "Save".
5. Verify update succeeded (version number changed).

### Approach B: Playwright Auth + REST API
1. Use Playwright's `context.request` or extracted auth headers.
2. `PUT /rest/api/content/{id}` with incremented version.
3. See `aw-confluence-page-reader` for REST API details.

### Pitfalls
- Always increment version number (`current + 1`).
- Page title must be passed explicitly — do not trust GET response title.
- Use Python for Cyrillic content (PowerShell corrupts encoding).
