---
name: vercel-react-best-practices
description: React and Next.js performance optimization guidelines from Vercel Engineering. This skill should be used when writing, reviewing, or refactoring React/Next.js code to ensure optimal performance patterns. Triggers on tasks involving React components, Next.js pages, data fetching, bundle optimization, or performance improvements.
license: MIT
metadata:
  author: vercel
  version: "1.0.0"
  source: https://github.com/vercel-labs/agent-skills/tree/main/skills/react-best-practices
---

# Vercel React Best Practices

Comprehensive performance optimization guide for React and Next.js applications, maintained by Vercel. Contains 70 rules across 8 categories, prioritized by impact to guide automated refactoring and code generation.

## When to Apply

Reference these guidelines when:
- Writing new React components or Next.js pages
- Implementing data fetching (client or server-side)
- Reviewing code for performance issues
- Refactoring existing React/Next.js code
- Optimizing bundle size or load times

## Rule Categories by Priority

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | Eliminating Waterfalls | CRITICAL | `async-` |
| 2 | Bundle Size Optimization | CRITICAL | `bundle-` |
| 3 | Server-Side Performance | HIGH | `server-` |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH | `client-` |
| 5 | Re-render Optimization | MEDIUM | `rerender-` |
| 6 | Rendering Performance | MEDIUM | `rendering-` |
| 7 | JavaScript Performance | LOW-MEDIUM | `js-` |
| 8 | Advanced Patterns | LOW | `advanced-` |

## Quick Reference

### 1. Eliminating Waterfalls (CRITICAL)

- [`async-cheap-condition-before-await`](react-best-practices/rules/async-cheap-condition-before-await.md) - Check cheap sync conditions before awaiting flags or remote values
- [`async-defer-await`](react-best-practices/rules/async-defer-await.md) - Move await into branches where actually used
- [`async-parallel`](react-best-practices/rules/async-parallel.md) - Use Promise.all() for independent operations
- [`async-dependencies`](react-best-practices/rules/async-dependencies.md) - Use better-all for partial dependencies
- [`async-api-routes`](react-best-practices/rules/async-api-routes.md) - Start promises early, await late in API routes
- [`async-suspense-boundaries`](react-best-practices/rules/async-suspense-boundaries.md) - Use Suspense to stream content

### 2. Bundle Size Optimization (CRITICAL)

- [`bundle-barrel-imports`](react-best-practices/rules/bundle-barrel-imports.md) - Import directly, avoid barrel files
- [`bundle-analyzable-paths`](react-best-practices/rules/bundle-analyzable-paths.md) - Prefer statically analyzable import and file-system paths to avoid broad bundles and traces
- [`bundle-dynamic-imports`](react-best-practices/rules/bundle-dynamic-imports.md) - Use next/dynamic for heavy components
- [`bundle-defer-third-party`](react-best-practices/rules/bundle-defer-third-party.md) - Load analytics/logging after hydration
- [`bundle-conditional`](react-best-practices/rules/bundle-conditional.md) - Load modules only when feature is activated
- [`bundle-preload`](react-best-practices/rules/bundle-preload.md) - Preload on hover/focus for perceived speed

### 3. Server-Side Performance (HIGH)

- [`server-auth-actions`](react-best-practices/rules/server-auth-actions.md) - Authenticate server actions like API routes
- [`server-cache-react`](react-best-practices/rules/server-cache-react.md) - Use React.cache() for per-request deduplication
- [`server-cache-lru`](react-best-practices/rules/server-cache-lru.md) - Use LRU cache for cross-request caching
- [`server-dedup-props`](react-best-practices/rules/server-dedup-props.md) - Avoid duplicate serialization in RSC props
- [`server-hoist-static-io`](react-best-practices/rules/server-hoist-static-io.md) - Hoist static I/O (fonts, logos) to module level
- [`server-no-shared-module-state`](react-best-practices/rules/server-no-shared-module-state.md) - Avoid module-level mutable request state in RSC/SSR
- [`server-serialization`](react-best-practices/rules/server-serialization.md) - Minimize data passed to client components
- [`server-parallel-fetching`](react-best-practices/rules/server-parallel-fetching.md) - Restructure components to parallelize fetches
- [`server-parallel-nested-fetching`](react-best-practices/rules/server-parallel-nested-fetching.md) - Chain nested fetches per item in Promise.all
- [`server-after-nonblocking`](react-best-practices/rules/server-after-nonblocking.md) - Use after() for non-blocking operations

### 4. Client-Side Data Fetching (MEDIUM-HIGH)

- [`client-swr-dedup`](react-best-practices/rules/client-swr-dedup.md) - Use SWR for automatic request deduplication
- [`client-event-listeners`](react-best-practices/rules/client-event-listeners.md) - Deduplicate global event listeners
- [`client-passive-event-listeners`](react-best-practices/rules/client-passive-event-listeners.md) - Use passive listeners for scroll
- [`client-localstorage-schema`](react-best-practices/rules/client-localstorage-schema.md) - Version and minimize localStorage data

### 5. Re-render Optimization (MEDIUM)

- [`rerender-defer-reads`](react-best-practices/rules/rerender-defer-reads.md) - Don't subscribe to state only used in callbacks
- [`rerender-memo`](react-best-practices/rules/rerender-memo.md) - Extract expensive work into memoized components
- [`rerender-memo-with-default-value`](react-best-practices/rules/rerender-memo-with-default-value.md) - Hoist default non-primitive props
- [`rerender-dependencies`](react-best-practices/rules/rerender-dependencies.md) - Use primitive dependencies in effects
- [`rerender-derived-state`](react-best-practices/rules/rerender-derived-state.md) - Subscribe to derived booleans, not raw values
- [`rerender-derived-state-no-effect`](react-best-practices/rules/rerender-derived-state-no-effect.md) - Derive state during render, not effects
- [`rerender-functional-setstate`](react-best-practices/rules/rerender-functional-setstate.md) - Use functional setState for stable callbacks
- [`rerender-lazy-state-init`](react-best-practices/rules/rerender-lazy-state-init.md) - Pass function to useState for expensive values
- [`rerender-simple-expression-in-memo`](react-best-practices/rules/rerender-simple-expression-in-memo.md) - Avoid memo for simple primitives
- [`rerender-split-combined-hooks`](react-best-practices/rules/rerender-split-combined-hooks.md) - Split hooks with independent dependencies
- [`rerender-move-effect-to-event`](react-best-practices/rules/rerender-move-effect-to-event.md) - Put interaction logic in event handlers
- [`rerender-transitions`](react-best-practices/rules/rerender-transitions.md) - Use startTransition for non-urgent updates
- [`rerender-use-deferred-value`](react-best-practices/rules/rerender-use-deferred-value.md) - Defer expensive renders to keep input responsive
- [`rerender-use-ref-transient-values`](react-best-practices/rules/rerender-use-ref-transient-values.md) - Use refs for transient frequent values
- [`rerender-no-inline-components`](react-best-practices/rules/rerender-no-inline-components.md) - Don't define components inside components

### 6. Rendering Performance (MEDIUM)

- [`rendering-animate-svg-wrapper`](react-best-practices/rules/rendering-animate-svg-wrapper.md) - Animate div wrapper, not SVG element
- [`rendering-content-visibility`](react-best-practices/rules/rendering-content-visibility.md) - Use content-visibility for long lists
- [`rendering-hoist-jsx`](react-best-practices/rules/rendering-hoist-jsx.md) - Extract static JSX outside components
- [`rendering-svg-precision`](react-best-practices/rules/rendering-svg-precision.md) - Reduce SVG coordinate precision
- [`rendering-hydration-no-flicker`](react-best-practices/rules/rendering-hydration-no-flicker.md) - Use inline script for client-only data
- [`rendering-hydration-suppress-warning`](react-best-practices/rules/rendering-hydration-suppress-warning.md) - Suppress expected mismatches
- [`rendering-activity`](react-best-practices/rules/rendering-activity.md) - Use Activity component for show/hide
- [`rendering-conditional-render`](react-best-practices/rules/rendering-conditional-render.md) - Use ternary, not && for conditionals
- [`rendering-usetransition-loading`](react-best-practices/rules/rendering-usetransition-loading.md) - Prefer useTransition for loading state
- [`rendering-resource-hints`](react-best-practices/rules/rendering-resource-hints.md) - Use React DOM resource hints for preloading
- [`rendering-script-defer-async`](react-best-practices/rules/rendering-script-defer-async.md) - Use defer or async on script tags

### 7. JavaScript Performance (LOW-MEDIUM)

- [`js-batch-dom-css`](react-best-practices/rules/js-batch-dom-css.md) - Group CSS changes via classes or cssText
- [`js-index-maps`](react-best-practices/rules/js-index-maps.md) - Build Map for repeated lookups
- [`js-cache-property-access`](react-best-practices/rules/js-cache-property-access.md) - Cache object properties in loops
- [`js-cache-function-results`](react-best-practices/rules/js-cache-function-results.md) - Cache function results in module-level Map
- [`js-cache-storage`](react-best-practices/rules/js-cache-storage.md) - Cache localStorage/sessionStorage reads
- [`js-combine-iterations`](react-best-practices/rules/js-combine-iterations.md) - Combine multiple filter/map into one loop
- [`js-length-check-first`](react-best-practices/rules/js-length-check-first.md) - Check array length before expensive comparison
- [`js-early-exit`](react-best-practices/rules/js-early-exit.md) - Return early from functions
- [`js-hoist-regexp`](react-best-practices/rules/js-hoist-regexp.md) - Hoist RegExp creation outside loops
- [`js-min-max-loop`](react-best-practices/rules/js-min-max-loop.md) - Use loop for min/max instead of sort
- [`js-set-map-lookups`](react-best-practices/rules/js-set-map-lookups.md) - Use Set/Map for O(1) lookups
- [`js-tosorted-immutable`](react-best-practices/rules/js-tosorted-immutable.md) - Use toSorted() for immutability
- [`js-flatmap-filter`](react-best-practices/rules/js-flatmap-filter.md) - Use flatMap to map and filter in one pass
- [`js-request-idle-callback`](react-best-practices/rules/js-request-idle-callback.md) - Defer non-critical work to browser idle time

### 8. Advanced Patterns (LOW)

- [`advanced-effect-event-deps`](react-best-practices/rules/advanced-effect-event-deps.md) - Don't put `useEffectEvent` results in effect deps
- [`advanced-event-handler-refs`](react-best-practices/rules/advanced-event-handler-refs.md) - Store event handlers in refs
- [`advanced-init-once`](react-best-practices/rules/advanced-init-once.md) - Initialize app once per app load
- [`advanced-use-latest`](react-best-practices/rules/advanced-use-latest.md) - useLatest for stable callback refs

## Install

```bash
npx skills add vercel-labs/agent-skills --skill vercel-react-best-practices
```
