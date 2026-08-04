---
name: react-native-best-practices
description: Provides React Native performance optimization guidelines for FPS, TTI, bundle size, memory leaks, re-renders, and animations. Applies to tasks involving Hermes optimization, JS thread blocking, bridge overhead, FlashList, native modules, or debugging jank and frame drops.
license: MIT
metadata:
  author: Callstack
  tags: react-native, expo, performance, optimization, profiling
  source: https://github.com/callstackincubator/agent-skills/tree/main/skills/react-native-best-practices
---

# React Native Best Practices

Performance optimization guide for React Native applications, covering JavaScript/React, Native (iOS/Android), and bundling optimizations. Based on Callstack's "Ultimate Guide to React Native Optimization".

## When to Apply

- Debugging slow/janky UI or animations
- Investigating memory leaks (JS or native)
- Optimizing app startup time (TTI)
- Reducing bundle or app size
- Writing native modules (Turbo Modules)
- Profiling React Native performance
- Reviewing React Native code for performance

## Priority-Ordered Guidelines

| Priority | Category | Impact | Prefix |
|----------|----------|--------|--------|
| 1 | FPS & Re-renders | CRITICAL | `js-*` |
| 2 | Bundle Size | CRITICAL | `bundle-*` |
| 3 | TTI Optimization | HIGH | `native-*`, `bundle-*` |
| 4 | Native Performance | HIGH | `native-*` |
| 5 | Memory Management | MEDIUM-HIGH | `js-*`, `native-*` |
| 6 | Animations | MEDIUM | `js-*` |

## Quick Reference

### Optimization Workflow

**Measure → Optimize → Re-measure → Validate**

### Critical: FPS & Re-renders

```bash
# Open React Native DevTools: press 'j' in Metro
```

Common fixes:
- Replace ScrollView with FlatList/FlashList for lists
- Use React Compiler for automatic memoization
- Use atomic state (Jotai/Zustand) to reduce re-renders
- Use `useDeferredValue` for expensive computations

### Critical: Bundle Size

```bash
npx react-native bundle \
  --entry-file index.js \
  --bundle-output output.js \
  --platform ios \
  --dev false --minify true

npx source-map-explorer output.js --no-border-checks
```

Common fixes:
- Avoid barrel imports
- Enable tree shaking (Expo SDK 52+ or Re.Pack)
- Enable R8 for Android native code shrinking

### High: TTI Optimization

Common fixes:
- Disable JS bundle compression on Android (enables Hermes mmap)
- Use native navigation (react-native-screens)
- Preload commonly-used expensive screens

## References (js-*)

| File | Impact | Description |
|------|--------|-------------|
| [`js-lists-flatlist-flashlist.md`](react-native-best-practices/references/js-lists-flatlist-flashlist.md) | CRITICAL | Replace ScrollView with virtualized lists |
| [`js-react-compiler.md`](react-native-best-practices/references/js-react-compiler.md) | HIGH | Automatic memoization |
| [`js-atomic-state.md`](react-native-best-practices/references/js-atomic-state.md) | HIGH | Jotai/Zustand patterns |
| [`js-concurrent-react.md`](react-native-best-practices/references/js-concurrent-react.md) | HIGH | useDeferredValue, useTransition |
| [`js-animations-reanimated.md`](react-native-best-practices/references/js-animations-reanimated.md) | MEDIUM | Reanimated worklets |
| [`js-memory-leaks.md`](react-native-best-practices/references/js-memory-leaks.md) | MEDIUM | JS memory leak hunting |

## References (bundle-*)

| File | Impact | Description |
|------|--------|-------------|
| [`bundle-barrel-exports.md`](react-native-best-practices/references/bundle-barrel-exports.md) | CRITICAL | Avoid barrel imports |
| [`bundle-analyze-js.md`](react-native-best-practices/references/bundle-analyze-js.md) | CRITICAL | JS bundle visualization |
| [`bundle-tree-shaking.md`](react-native-best-practices/references/bundle-tree-shaking.md) | HIGH | Dead code elimination |
| [`bundle-hermes-mmap.md`](react-native-best-practices/references/bundle-hermes-mmap.md) | HIGH | Disable bundle compression |
| [`bundle-r8-android.md`](react-native-best-practices/references/bundle-r8-android.md) | HIGH | Android code shrinking |

## Problem → Skill Mapping

| Problem | Start With |
|---------|------------|
| App feels slow/janky | [`js-measure-fps.md`](react-native-best-practices/references/js-measure-fps.md) → [`js-profile-react.md`](react-native-best-practices/references/js-profile-react.md) |
| Too many re-renders | [`js-profile-react.md`](react-native-best-practices/references/js-profile-react.md) → [`js-react-compiler.md`](react-native-best-practices/references/js-react-compiler.md) |
| Slow startup (TTI) | [`native-measure-tti.md`](react-native-best-practices/references/native-measure-tti.md) → [`bundle-analyze-js.md`](react-native-best-practices/references/bundle-analyze-js.md) |
| Large app size | [`bundle-analyze-app.md`](react-native-best-practices/references/bundle-analyze-app.md) → [`bundle-r8-android.md`](react-native-best-practices/references/bundle-r8-android.md) |
| Memory growing | [`js-memory-leaks.md`](react-native-best-practices/references/js-memory-leaks.md) or [`native-memory-leaks.md`](react-native-best-practices/references/native-memory-leaks.md) |
| Animation drops frames | [`js-animations-reanimated.md`](react-native-best-practices/references/js-animations-reanimated.md) |
| List scroll jank | [`js-lists-flatlist-flashlist.md`](react-native-best-practices/references/js-lists-flatlist-flashlist.md) |

## Install

```bash
npx skills add callstackincubator/agent-skills --skill react-native-best-practices
```
