---
name: react-router-framework-mode
description: Build full-stack React applications using React Router's framework mode. Use when configuring routes, working with loaders and actions, handling forms, handling navigation, pending/optimistic UI, error boundaries, or working with react-router.config.ts or other react router conventions.
license: MIT
metadata:
  source: https://github.com/remix-run/agent-skills/tree/main/skills/react-router-framework-mode
---

# React Router Framework Mode

Framework mode is React Router's full-stack development experience with file-based routing, server-side, client-side, and static rendering strategies, data loading and mutations, and type-safe route module API.

## When to Apply

- Configuring new routes (`app/routes.ts`)
- Loading data with `loader` or `clientLoader`
- Handling mutations with `action` or `clientAction`
- Navigating with `<Link>`, `<NavLink>`, `<Form>`, `redirect`, and `useNavigate`
- Implementing pending/loading UI states
- Configuring SSR, SPA mode, or pre-rendering (`react-router.config.ts`)
- Implementing authentication

## References

| Reference                            | Use When                                              |
| ------------------------------------ | ----------------------------------------------------- |
| [`references/routing.md`](react-router-framework-mode/references/routing.md) | Configuring routes, nested routes, dynamic segments   |
| [`references/route-modules.md`](react-router-framework-mode/references/route-modules.md) | Understanding all route module exports                |
| [`references/special-files.md`](react-router-framework-mode/references/special-files.md) | Customizing root.tsx, adding global nav/footer, fonts |
| [`references/data-loading.md`](react-router-framework-mode/references/data-loading.md) | Loading data with loaders, streaming, caching         |
| [`references/actions.md`](react-router-framework-mode/references/actions.md) | Handling forms, mutations, validation                 |
| [`references/navigation.md`](react-router-framework-mode/references/navigation.md) | Links, programmatic navigation, redirects             |
| [`references/pending-ui.md`](react-router-framework-mode/references/pending-ui.md) | Loading states, optimistic UI                         |
| [`references/error-handling.md`](react-router-framework-mode/references/error-handling.md) | Error boundaries, error reporting                     |
| [`references/rendering-strategies.md`](react-router-framework-mode/references/rendering-strategies.md) | SSR vs SPA vs pre-rendering configuration             |
| [`references/middleware.md`](react-router-framework-mode/references/middleware.md) | Adding middleware (requires v7.9.0+)                  |
| [`references/sessions.md`](react-router-framework-mode/references/sessions.md) | Cookie sessions, authentication, protected routes     |
| [`references/type-safety.md`](react-router-framework-mode/references/type-safety.md) | Auto-generated route types, type imports, type safety |

## Version Compatibility

| Feature                 | Minimum Version | Notes                         |
| ----------------------- | --------------- | ----------------------------- |
| Middleware              | 7.9.0+          | Requires `v8_middleware` flag |
| Core framework features | 7.0.0+          | loaders, actions, Form, etc.  |

## Critical Patterns

### Forms & Mutations

**Search forms** - use `<Form method="get">`, NOT `onSubmit` with `setSearchParams`:

```tsx
// ✅ Correct
<Form method="get">
  <input name="q" />
</Form>

// ❌ Wrong
<form onSubmit={(e) => { e.preventDefault(); setSearchParams(...) }}>
```

**Inline mutations** - use `useFetcher`, NOT `<Form>`:

```tsx
const fetcher = useFetcher();
<fetcher.Form method="post" action={`/favorites/${id}`}>
  <button>{optimistic ? "★" : "☆"}</button>
</fetcher.Form>
```

### Layouts

**Global UI belongs in `root.tsx`**:

```tsx
export default function App() {
  return (
    <div>
      <nav>...</nav>
      <Outlet />
      <footer>...</footer>
    </div>
  );
}
```

### Route Module Exports

**`meta` uses `loaderData`**, not deprecated `data`:

```tsx
// ✅ Correct
export function meta({ loaderData }: Route.MetaArgs) { ... }
```

## Further Documentation

https://reactrouter.com/docs

## Install

```bash
npx skills add remix-run/agent-skills
```
