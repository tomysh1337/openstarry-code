---
name: react-component-patterns
description: >
  Structure React components with clear props, hooks, composition, and
  colocation. Use when React components, hooks, props, colocation, compound
  components, React 组件, 组件结构, custom hooks, or when reviewing React UI
  structure. Pairs with code-quality-standards; does not replace repo React
  conventions, ESLint, or design systems.
---

# React Component Patterns

Engineering patterns for **React component structure**: what owns state, how
props and hooks stay readable, how files are colocated, and how composition
beats prop-drilling soup. Prefer the repo’s existing React style (RSC vs CSR,
folder layout, design system) over inventing a second model.

## Use When

- Building or refactoring React / React Native components
- Designing props APIs, children/slots, or compound components
- Extracting or reviewing custom hooks (`use*`)
- Deciding file colocation: component + styles + tests + hooks
- Fixing hook misuse: missing deps, derived state, effects for pure transforms
- User mentions: React components, hooks, props, colocation, compound component,
  React 组件, 组件结构, 自定义 Hook, props 设计, 组合式组件

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Global client vs server state, Redux/Zustand choice | `state-management-guidelines` |
| Visual aesthetics, distinctive UI look | `frontend-design` / `top-design` |
| TS strictness, `any`, import order | `typescript-style-and-eslint` |
| Formatting only | `prettier-eslint-editorconfig` |
| Reliability, errors, tests, security hygiene | `code-quality-standards` |
| Concurrent fetch races / AbortSignal design | `async-concurrency-patterns` |

## Repo Config First

Repo config and neighboring React code **outrank** this skill’s defaults.

1. **React mode:** Next.js App Router / RSC, Pages Router, CRA/Vite SPA, Remix,
   React Native — server components, `"use client"`, and data-fetch placement differ
2. **Component library:** design system packages, `cn`/CVA, Radix, MUI, Chakra —
   compose with them; do not reimplement primitives already in tree
3. **Folder conventions:** feature folders vs `components/` + `hooks/`;
   `index.ts` barrels; `ComponentName/` colocation; story/test suffixes
4. **Lint / types:** `eslint-plugin-react-hooks`, React Compiler flags,
   `tsconfig` JSX settings, path aliases
5. **State stack already chosen:** React Query/SWR, Redux, Zustand, Context —
   route client/server state decisions to `state-management-guidelines`
6. **Styling system:** CSS Modules, Tailwind, styled-components, vanilla-extract —
   match local pattern; do not introduce a second system mid-PR
7. **Neighboring components:** copy 2–3 mature feature components for props
   shape, error/loading UI, and hook extraction thresholds

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that break hooks rules, leak secrets to the client, or mix
server/client boundaries incorrectly.

## Workflow

1. **State the UI contract.**
   - What the user sees/does; loading, empty, error, success
   - Controlled vs uncontrolled inputs; who owns which slice of state
   - Server vs client responsibility (RSC data, client interactivity)
2. **Compose before you configure.**
   - Prefer small components + children/slots over giant prop matrices
   - Lift state only as far as shared consumers need it
3. **Shape props for the caller.**
   - Domain names; narrow unions; avoid boolean soup (`isA` + `isB` + `variant`)
   - Extend native element props when wrapping DOM (`ComponentPropsWithoutRef`)
   - Document required vs optional; sensible defaults at the leaf
4. **Place state and effects deliberately.**
   - Derive during render when possible; do not mirror props into state
   - Effects for sync with external systems only (DOM, network subscriptions)
   - Extract hooks when logic is reused or obscures the render tree
5. **Colocate by change frequency.**
   - Keep component, styles, tests, and private hooks that change together nearby
   - Promote to shared only after a second real consumer appears
6. **Guard boundaries.**
   - Client components: no secrets; validate untrusted props/URL state at edges
   - Lists: stable keys from identity, not array index (unless static)
   - Memoize only when measured or when referential stability is a contract
7. **Verify.**
   - Hooks lint clean; types for public props; smoke the loading/error paths
   - Apply `code-quality-standards` for errors, cleanup, and tests

## Design Principles

| Principle | Practice |
| --- | --- |
| Single responsibility | One component answers one UI question; split layout vs logic vs data glue |
| Composition over configuration | `children`, slots, compound parts > 15 optional booleans |
| Props are the public API | Stable names; break carefully; prefer additive changes |
| Render is a pure function of props + state | No hidden global reads without an explicit store/context |
| Derive, don’t sync | `const fullName = `${first} ${last}`` not `useEffect` to set it |
| Effects are escape hatches | Subscribe, imperative DOM, non-React widgets — not “run when X changes” for pure data |
| Colocation | Code that changes together lives together |
| Accessibility is structure | Semantic elements, labels, focus order — not only ARIA patches |

### Component structure (default skeleton)

When the repo has no stronger template:

```tsx
// FeatureCard.tsx — presentational shell; data loaded by parent or hook
type FeatureCardProps = {
  title: string;
  description?: string;
  onSelect?: () => void;
};

export function FeatureCard({ title, description, onSelect }: FeatureCardProps) {
  return (
    <article>
      <h3>{title}</h3>
      {description ? <p>{description}</p> : null}
      {onSelect ? (
        <button type="button" onClick={onSelect}>
          Select
        </button>
      ) : null}
    </article>
  );
}
```

### Hooks

| Do | Don’t |
| --- | --- |
| Name `useX`; call unconditionally at top level | Call hooks in loops/conditions |
| Return stable, documented tuples/objects | Return new inline identities without need |
| Accept `AbortSignal` / cleanup for async | Ignore cancellation (see `async-concurrency-patterns`) |
| Keep one concern per hook | `useGodObject` that fetches, caches, and formats everything |

### Colocation map (typical)

```text
features/orders/
  OrderList.tsx
  OrderList.test.tsx
  OrderList.module.css   # or co-located Tailwind usage
  useOrderFilters.ts     # private to feature until reused
  api.ts                 # feature fetchers if not global
```

Promote `useOrderFilters` to `shared/hooks/` only when a second feature needs it.

### Server vs client (React 19 / Next-style)

- Default to **Server Components** for static/data display when the stack supports it
- Add `"use client"` only for state, effects, browser APIs, or event handlers
- Pass serializable props across the server→client boundary; no functions/classes
  unless the framework explicitly supports that pattern
- Do not fetch secrets or privileged tokens in client components

## Good / Bad Examples

### Props: composition vs boolean soup

**Good** — variant union + composition:

```tsx
type ButtonProps = {
  variant?: "primary" | "secondary" | "danger";
  children: React.ReactNode;
  onClick?: () => void;
};

export function Button({ variant = "primary", children, onClick }: ButtonProps) {
  return (
    <button type="button" data-variant={variant} onClick={onClick}>
      {children}
    </button>
  );
}

// Caller composes
<Button variant="danger">Delete</Button>
```

**Bad** — exploding booleans:

```tsx
// Bad: mutually unclear combinations
type ButtonProps = {
  isPrimary?: boolean;
  isSecondary?: boolean;
  isDanger?: boolean;
  isLarge?: boolean;
  isSmall?: boolean;
  showIcon?: boolean;
  iconLeft?: boolean;
};
```

### Derived state vs mirrored props

**Good** — derive in render:

```tsx
function Price({ cents, taxRate }: { cents: number; taxRate: number }) {
  const total = Math.round(cents * (1 + taxRate));
  return <span>{(total / 100).toFixed(2)}</span>;
}
```

**Bad** — sync props into state with effects:

```tsx
function Price({ cents, taxRate }: { cents: number; taxRate: number }) {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    setTotal(Math.round(cents * (1 + taxRate)));
  }, [cents, taxRate]);
  return <span>{(total / 100).toFixed(2)}</span>;
}
```

### Controlled input

**Good** — parent owns value when it must coordinate:

```tsx
function SearchField({
  value,
  onChange,
}: {
  value: string;
  onChange: (next: string) => void;
}) {
  return (
    <input
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Search"
    />
  );
}
```

**Bad** — half-controlled (prop initializes once, then drifts):

```tsx
function SearchField({ initial }: { initial: string }) {
  const [value, setValue] = useState(initial);
  // parent cannot reset/update; prop changes ignored
  return <input value={value} onChange={(e) => setValue(e.target.value)} />;
}
```

### Custom hooks

**Good** — focused hook with cleanup:

```tsx
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() =>
    typeof window !== "undefined" ? window.matchMedia(query).matches : false,
  );

  useEffect(() => {
    const mql = window.matchMedia(query);
    const onChange = () => setMatches(mql.matches);
    onChange();
    mql.addEventListener("change", onChange);
    return () => mql.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}
```

**Bad** — conditional hooks / mixed concerns:

```tsx
function useDashboard(userId?: string) {
  if (!userId) return null; // Bad: breaks rules of hooks for callers who branch
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState("light");
  // fetches, websockets, form state all in one…
}
```

### Lists and keys

**Good**

```tsx
{items.map((item) => (
  <OrderRow key={item.id} order={item} />
))}
```

**Bad**

```tsx
{items.map((item, index) => (
  <OrderRow key={index} order={item} /> // identity shifts on reorder/delete
))}
```

### Colocation vs premature share

**Good** — feature-private until second consumer.

**Bad** — `shared/components/MagicTable.tsx` with 40 props used by one screen,
or three competing `Button` primitives in different folders.

## Anti-Patterns

- Prop drilling 5+ levels when context/composition would clarify ownership
- God components (fetch + form + table + modal in one file)
- `useEffect` for pure calculation, filtering, or mapping
- Disabling `react-hooks/exhaustive-deps` without a documented invariant
- Inline anonymous components inside render that reset state every parent render
  (`items.map(() => { function Row() …`) 
- Spreading unknown props onto DOM without filtering (invalid attrs / XSS vectors
  via URLs — validate at boundaries per `code-quality-standards`)
- Default-export-only modules that fight named-export repo style
- Duplicating design-system primitives “just for this screen”
- Client components that embed API keys or privileged business rules
- Premature `React.memo` / `useMemo` / `useCallback` everywhere (noise, false safety)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Component structure, hooks, props, colocation | **This skill** | — |
| Client vs server state, Redux/Zustand/context choice | `state-management-guidelines` | this for component wiring |
| Production correctness, errors, resources, tests, security | `code-quality-standards` | **always apply** on implementation |
| TS/ESLint style only | `typescript-style-and-eslint` | this for component shape |
| Visual design / aesthetics | `frontend-design` / `top-design` | this for structure |
| Async cancel, stale responses, fan-out | `async-concurrency-patterns` | this for where hooks live |
| Naming components/hooks/files | `naming-conventions-general` | this for structure |
| Comments on non-obvious UI invariants | `comment-writing-standards` | — |

### Routing to `code-quality-standards`

Keep **this skill primary** for React structure and composition. Always apply
**`code-quality-standards`** as the implementation baseline when code changes:

- Clear boundaries: UI vs data access vs domain rules
- Error and loading states handled; no swallowed failures in event handlers
- Subscriptions, timers, and listeners cleaned up on unmount
- Untrusted input (URL, form, `postMessage`) validated at the boundary
- Tests for critical interaction paths when blast radius warrants
- No secrets in client bundles or logs

This skill specializes **components, hooks, props, and colocation**. It does not
replace general quality, security, state-library choice, or visual design systems.

## Checklist

- [ ] Repo React mode, folder layout, design system, and lint rules identified
- [ ] UI contract clear: loading / empty / error / success; controlled ownership
- [ ] Composition preferred over large prop/boolean matrices
- [ ] Props typed, narrow, and stable for callers; native prop extension when wrapping DOM
- [ ] State minimal; derived values computed in render, not mirrored via effects
- [ ] Effects only for external systems; cleanup present; hooks lint satisfied
- [ ] Custom hooks focused; no conditional hook calls
- [ ] Colocation by feature; shared only with real second consumers
- [ ] List keys from stable identity; a11y basics (labels, semantics, focus)
- [ ] Server/client boundary respected when using RSC / `"use client"`
- [ ] Memoization only with a reason (measure or required stability)
- [ ] `code-quality-standards` applied for errors, cleanup, security, and verification
- [ ] State library choices deferred to `state-management-guidelines` when relevant
