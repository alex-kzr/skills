---
name: react-router-declarative-mode
description: Build React applications using React Router's declarative mode with BrowserRouter. Use when configuring routes with JSX, navigating with Link/NavLink, or reading URL params and search params without data loaders or actions.
license: MIT
metadata:
  source: https://github.com/remix-run/agent-skills/tree/main/skills/react-router-declarative-mode
---

# React Router Declarative Mode

Declarative mode uses `<BrowserRouter>`, `<Routes>`, and `<Route>` for basic client-side routing without data loading features.

## When to Apply

- Using `<BrowserRouter>` for routing
- Configuring routes with `<Routes>` and `<Route>`
- Navigating with `<Link>`, `<NavLink>`, or `useNavigate`
- Reading URL params with `useParams`
- Working with search params using `useSearchParams`
- Accessing location with `useLocation`

## References

| Reference                  | Use When                                          |
| -------------------------- | ------------------------------------------------- |
| [`references/routing.md`](react-router-declarative-mode/references/routing.md) | Configuring routes, nested routes, dynamic params |
| [`references/navigation.md`](react-router-declarative-mode/references/navigation.md) | Links, NavLink active states, programmatic nav    |
| [`references/url-values.md`](react-router-declarative-mode/references/url-values.md) | Reading params, search params, location           |

## Critical Patterns

### Basic Route Setup

```tsx
import { BrowserRouter, Routes, Route } from "react-router";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="about" element={<About />} />
        <Route path="dashboard" element={<Dashboard />}>
          <Route index element={<DashboardHome />} />
          <Route path="settings" element={<Settings />} />
        </Route>
        <Route path="users/:userId" element={<User />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### NavLink Active States

```tsx
<NavLink
  to="/dashboard"
  className={({ isActive }) => (isActive ? "active" : "")}
>
  Dashboard
</NavLink>
```

### Reading URL Params

```tsx
const { userId } = useParams();
```

### Working with Search Params

```tsx
const [searchParams, setSearchParams] = useSearchParams();
const query = searchParams.get("q");
```

## Further Documentation

https://reactrouter.com/docs

## Install

```bash
npx skills add remix-run/agent-skills
```
