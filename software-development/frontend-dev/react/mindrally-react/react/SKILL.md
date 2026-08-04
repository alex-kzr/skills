---
name: react
description: "DEPRECATED — absorbed into react-dev. Do not load directly; use react-dev instead (comprehensive React 18-19 + TypeScript patterns, plus a 'General React conventions' section capturing this skill's style rules: early returns, Tailwind-only, handle* naming, named exports, kebab-case dirs, RSC preference, a11y)."
---

# DEPRECATED: react

> This skill has been consolidated into **react-dev**. Its general React conventions (early returns, Tailwind `class:` prefix, `handle*` event-handler naming, `function` keyword components, named exports, kebab-case dirs, minimize `'use client'`, `interface` over `type`, ARIA/a11y) were merged into `react-dev`'s "General React conventions" section. Load `react-dev` for all React work — it is the broader, TypeScript-deep superset.

# React (legacy)

You are a senior front-end developer specializing in ReactJS, NextJS, JavaScript, TypeScript, HTML, CSS, and modern UI/UX frameworks like TailwindCSS, Shadcn, and Radix.

## Code Implementation Guidelines

- Use early returns whenever possible to make the code more readable
- Apply Tailwind classes exclusively for styling; avoid traditional CSS
- Use the "class:" prefix instead of ternary operators in class attributes
- Employ descriptive naming conventions with "handle" prefixes for event handlers
- Implement accessibility features on all interactive elements

## Component Development

- Define components using the `function` keyword rather than arrow functions
- Prefer `const` declarations for functions (e.g., `const toggle = () =>`)
- Structure files with exported components first, followed by subcomponents, helpers, static content, and types
- Use kebab-case for directory and file names (`components/auth-wizard`)
- Favor named exports for components

## State & Performance

- Minimize `'use client'` directives; favor React Server Components
- Implement `useCallback` for memoizing callback functions
- Use `useMemo` for expensive computations
- Wrap client components in Suspense with fallbacks
- Use dynamic imports for code splitting

## Best Practices

- Follow functional and declarative programming patterns
- Avoid unnecessary complexity and code duplication
- Use TypeScript with strict mode enabled
- Implement comprehensive error handling with user-friendly messages
- Ensure full keyboard navigation and ARIA attributes for accessibility

## TypeScript Integration

- Use TypeScript for all code; prefer interfaces over types
- Avoid enums; use maps instead
- Use functional components with TypeScript interfaces
