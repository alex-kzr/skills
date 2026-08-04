---
name: tailwind-design-system
description: "Tailwind CSS v4: utility-first styling, design tokens, component libraries, responsive patterns, and dark mode. Use when writing Tailwind CSS, building component libraries, implementing design systems, or standardizing UI patterns. Formerly included separate tailwind-css skill for browser-runtime patterns."
---

# Tailwind CSS v4 + Design Systems

Build production-ready UIs with Tailwind CSS v4, including CSS-first configuration, design tokens, component variants, responsive patterns, accessibility, and browser-runtime utility patterns.

> **Note**: This skill targets Tailwind CSS v4 (2024+). For v3 projects, refer to the [upgrade guide](https://tailwindcss.com/docs/upgrade-guide).

## When to Use This Skill

- Writing Tailwind CSS utility classes or custom components
- Creating a component library with Tailwind v4
- Implementing design tokens and theming with CSS-first configuration
- Building responsive and accessible components
- Standardizing UI patterns across a codebase
- Migrating from Tailwind v3 to v4
- Setting up dark mode with native CSS features
- Using browser-runtime Tailwind (CDN, JIT in-browser)

---

## CSS-First Configuration (v4)

Tailwind v4 replaces `tailwind.config.js` with CSS-first `@theme` configuration:

```css
@import "tailwindcss";

@theme {
  --color-primary: #6366f1;
  --color-primary-dark: #4f46e5;
  --font-display: "Inter", sans-serif;
  --breakpoint-3xl: 1920px;
}
```

### Design Tokens
Define tokens as CSS custom properties in `@theme`. They automatically generate utilities (`bg-primary`, `text-primary`, `font-display`, etc.).

---

## Component Variants

```css
@layer components {
  .btn {
    @apply inline-flex items-center px-4 py-2 rounded-lg font-medium transition-colors;
  }
  .btn-primary {
    @apply bg-primary text-white hover:bg-primary-dark;
  }
}
```

---

## Responsive Patterns

Mobile-first breakpoints. Use container queries for component-level responsiveness:
```css
@container (min-width: 400px) {
  .card { @apply grid-cols-2; }
}
```

---

## Dark Mode

v4 uses native CSS `prefers-color-scheme`:
```css
@media (prefers-color-scheme: dark) {
  :root {
    --color-background: theme(--color-gray-900);
  }
}
```

---

## Browser-Runtime Patterns

For prototyping or runtime Tailwind (no build step):

### CDN (v4 Play CDN)
```html
<script src="https://cdn.tailwindcss.com"></script>
```
Configure inline: `<script>tailwind.config = { theme: { extend: { ... } } }</script>`

### JIT In-Browser
For dynamic class generation in HyperFrame or similar runtimes:
```js
import { compile } from 'tailwindcss/browser';
const css = await compile('@tailwind utilities; .custom { @apply p-4; }');
```

### Pitfalls (Browser Runtime)
- CDN mode does not purge — ships all utilities (larger CSS).
- `@apply` in browser runtime may not resolve custom theme values without configuration.
- For production, always use the build step with proper purging.

---

## Accessibility

- Ensure color contrast meets WCAG AA (4.5:1 for text).
- Use `focus-visible:ring` for keyboard navigation.
- Test with screen readers: semantic HTML + ARIA where needed.
- `sr-only` utility for visually hidden but accessible text.
