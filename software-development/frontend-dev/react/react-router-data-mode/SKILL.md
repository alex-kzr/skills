---
name: react-router-data-mode
description: Build React applications using React Router's data mode with createBrowserRouter and RouterProvider. Use when working with route objects, loaders, actions, Form, useFetcher, or pending/optimistic UI without the Vite plugin.
license: MIT
metadata:
  source: https://github.com/remix-run/agent-skills/tree/main/skills/react-router-data-mode
---

# React Router Data Mode

Data mode uses `createBrowserRouter` and `RouterProvider` to enable data loading, actions, and pending UI without the framework's Vite plugin. Ideal for existing React applications adding data loading and mutation capabilities.

## When to Apply

- Using `createBrowserRouter` with route objects
- Loading data with `loader` property on routes
- Handling mutations with `action` property
- Navigating with `<Link>`, `<NavLink>`, `<Form>`, `redirect`, and `useNavigate`
- Implementing pending/loading UI states with `useNavigation`
- Using `useFetcher` for mutations without navigation

## References

| Reference                    | Use When                                  |
| ---------------------------- | ----------------------------------------- |
| [`references/routing.md`](react-router-data-mode/references/routing.md) | Configuring routes, nested routes, layout |
| [`references/route-object.md`](react-router-data-mode/references/route-object.md) | Understanding route object properties     |
| [`references/data-loading.md`](react-router-data-mode/references/data-loading.md) | Loading data with loaders                 |
| [`references/actions.md`](react-router-data-mode/references/actions.md) | Handling forms, mutations, validation     |
| [`references/navigation.md`](react-router-data-mode/references/navigation.md) | Links, programmatic navigation, redirects |
| [`references/pending-ui.md`](react-router-data-mode/references/pending-ui.md) | Loading states, optimistic UI             |
| [`references/ssr.md`](react-router-data-mode/references/ssr.md) | Server-side rendering with data mode      |

## Critical Patterns

### Basic Router Setup

```tsx
import { createBrowserRouter, RouterProvider } from "react-router";

const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Home },
      { path: "about", Component: About },
    ],
  },
]);

ReactDOM.createRoot(root).render(<RouterProvider router={router} />);
```

### Forms & Mutations

```tsx
// ✅ Search - use Form method="get"
<Form method="get">
  <input name="q" />
</Form>

// ✅ Inline mutations - use useFetcher
const fetcher = useFetcher();
<fetcher.Form method="post" action={`/favorites/${id}`}>
  <button>{optimistic ? "★" : "☆"}</button>
</fetcher.Form>
```

### Optimistic UI

```tsx
function FavoriteButton({ itemId, isFavorite }) {
  const fetcher = useFetcher();
  const optimistic = fetcher.formData
    ? fetcher.formData.get("favorite") === "true"
    : isFavorite;

  return (
    <fetcher.Form method="post" action={`/items/${itemId}/favorite`}>
      <input type="hidden" name="favorite" value={String(!optimistic)} />
      <button>{optimistic ? "★" : "☆"}</button>
    </fetcher.Form>
  );
}
```

## Further Documentation

https://reactrouter.com/docs

## Install

```bash
npx skills add remix-run/agent-skills
```
