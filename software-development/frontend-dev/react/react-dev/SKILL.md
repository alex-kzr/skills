---
name: react-dev
version: 1.0.0
description: This skill should be used when building React components with TypeScript, typing hooks, handling events, or when React TypeScript, React 19, Server Components are mentioned. Covers type-safe patterns for React 18-19 including generic components, proper event typing, and routing integration (TanStack Router, React Router).
metadata:
  source: https://github.com/softaworks/agent-toolkit/tree/main/skills/react-dev
---

# React TypeScript

Type-safe React = compile-time guarantees = confident refactoring.

<when_to_use>

- Building typed React components
- Implementing generic components
- Typing event handlers, forms, refs
- Using React 19 features (Actions, Server Components, use())
- Router integration (TanStack Router, React Router)
- Custom hooks with proper typing

NOT for: non-React TypeScript, vanilla JS React

</when_to_use>

<react_19_changes>

React 19 breaking changes require migration. Key patterns:

**ref as prop** - forwardRef deprecated:

```typescript
// React 19 - ref as regular prop
type ButtonProps = {
  ref?: React.Ref<HTMLButtonElement>;
} & React.ComponentPropsWithoutRef<'button'>;

function Button({ ref, children, ...props }: ButtonProps) {
  return <button ref={ref} {...props}>{children}</button>;
}
```

**useActionState** - replaces useFormState:

```typescript
import { useActionState } from 'react';

type FormState = { errors?: string[]; success?: boolean };

function Form() {
  const [state, formAction, isPending] = useActionState(submitAction, {});
  return <form action={formAction}>...</form>;
}
```

**use()** - unwraps promises/context:

```typescript
function UserProfile({ userPromise }: { userPromise: Promise<User> }) {
  const user = use(userPromise); // Suspends until resolved
  return <div>{user.name}</div>;
}
```

</react_19_changes>

<component_patterns>

**Props** - extend native elements:

```typescript
type ButtonProps = {
  variant: 'primary' | 'secondary';
} & React.ComponentPropsWithoutRef<'button'>;

function Button({ variant, children, ...props }: ButtonProps) {
  return <button className={variant} {...props}>{children}</button>;
}
```

**Children typing**:

```typescript
type Props = {
  children: React.ReactNode;          // Anything renderable
  icon: React.ReactElement;           // Single element
  render: (data: T) => React.ReactNode;  // Render prop
};
```

**Discriminated unions** for variant props:

```typescript
type ButtonProps =
  | { variant: 'link'; href: string }
  | { variant: 'button'; onClick: () => void };
```

</component_patterns>

<event_handlers>

Use specific event types for accurate target typing:

```typescript
function handleClick(e: React.MouseEvent<HTMLButtonElement>) { ... }
function handleSubmit(e: React.FormEvent<HTMLFormElement>) { ... }
function handleChange(e: React.ChangeEvent<HTMLInputElement>) { ... }
function handleKeyDown(e: React.KeyboardEvent<HTMLInputElement>) { ... }
```

</event_handlers>

<hooks_typing>

**useState** - explicit for unions/null:

```typescript
const [user, setUser] = useState<User | null>(null);
const [status, setStatus] = useState<'idle' | 'loading'>('idle');
```

**useRef** - null for DOM, value for mutable:

```typescript
const inputRef = useRef<HTMLInputElement>(null);
const countRef = useRef<number>(0);
```

**Custom hooks** - tuple returns with as const:

```typescript
function useToggle(initial = false) {
  const [value, setValue] = useState(initial);
  return [value, () => setValue(v => !v)] as const;
}
```

</hooks_typing>

<rules>

ALWAYS:
- Specific event types (MouseEvent, ChangeEvent, etc)
- Explicit useState for unions/null
- ComponentPropsWithoutRef for native element extension
- Discriminated unions for variant props
- as const for tuple returns
- ref as prop in React 19 (no forwardRef)
- useActionState for form actions

NEVER:
- any for event handlers
- JSX.Element for children (use ReactNode)
- forwardRef in React 19+
- useFormState (deprecated)
- Forget null handling for DOM refs
- Mix Server/Client components in same file

</rules>

## Install

```bash
npx skills add https://github.com/softaworks/agent-toolkit --skill react-dev
```
