---
name: state-management-guidelines
description: >
  Choose and structure application state: client UI state vs server/cache state,
  and when to use React Context, Zustand, Redux, or URL state. Use when state
  management, Redux, Zustand, React Query, server state, client state, 状态管理,
  全局状态, or when deciding where data should live. Pairs with
  code-quality-standards and react-component-patterns.
---

# State Management Guidelines

Decision guide for **where state lives** and **which tool owns it**. Most bugs
labeled “state management” are really **wrong ownership**: server data stuffed
into global stores, or ephemeral UI state lifted into Redux. Prefer the repo’s
existing stack over introducing a second global store.

## Use When

- Choosing or reviewing client state vs server/remote state
- Introducing or expanding Redux, Zustand, Jotai, Recoil, MobX, Context, Signals
- Wiring React Query / TanStack Query, SWR, Apollo, RTK Query caches
- Deciding URL/search-params vs memory vs persistent storage
- Fixing prop drilling, unnecessary global stores, or cache/store duplication
- User mentions: state management, 状态管理, 全局状态, Redux, Zustand, Context,
  React Query, server state, client state, store design

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Component structure, hooks rules, colocation | `react-component-patterns` |
| In-process concurrency, abort, stale responses | `async-concurrency-patterns` |
| Visual UI design | `frontend-design` / `top-design` |
| TS/format only | `typescript-style-and-eslint` / `prettier-eslint-editorconfig` |
| Reliability, errors, tests, security hygiene | `code-quality-standards` |

## Repo Config First

Repo config and neighboring stores **outrank** this skill’s defaults.

1. **Existing state libraries:** package.json + imports — Redux Toolkit, Zustand,
   Context-only, TanStack Query, SWR, Apollo, Valtio, Jotai, etc.
2. **Data layer:** REST/gRPC clients, codegen, OpenAPI hooks — prefer extending
   the established fetch/cache layer over a parallel one
3. **Router state:** Next.js/Remix/React Router loaders, searchParams conventions
4. **Persistence:** already-used patterns for `localStorage`, cookies, session
5. **SSR/RSC:** dehydrated query caches, cookie session, no client-only store
   assumptions on the server
6. **Devtools / lint:** Redux DevTools, why-did-you-render policies, immutability
   helpers already in tree
7. **Neighboring features:** copy 2–3 mature features’ ownership split (what is
   query key vs zustand slice vs local `useState`) before adding a new global

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that create dual sources of truth (same entity in React Query
**and** Redux without a clear sync rule).

## Workflow

1. **Classify each piece of state** (table below). Write the classification down
   for non-trivial features before picking a library.
2. **Prefer the lowest capable layer.**
   - Local `useState` / `useReducer` → URL → Context → lightweight store →
     full Redux-style hub — only climb when requirements demand it
3. **Separate server state from client state.**
   - Server/remote: cache, invalidate, revalidate — do not hand-copy into Redux
     unless the repo already standardizes on that (e.g. RTK Query only)
4. **Define ownership and write path.**
   - Who updates? Optimistic? Source of truth after refresh?
5. **Define scope and lifetime.**
   - Screen-local, session, cross-route, multi-tab, persisted
6. **Implement with one pattern per kind of state** in the feature; avoid
   “Context + Zustand + Redux” for the same concern.
7. **Verify.**
   - Refresh, back/forward, stale cache, logout clears sensitive state
   - Apply `code-quality-standards` for errors, security, and tests

## State Classification

| Kind | Examples | Default home |
| --- | --- | --- |
| **Server / remote** | Users, orders, permissions from API | TanStack Query / SWR / RTK Query / Apollo (repo choice) |
| **URL / route** | Filters, page, selected tab shareable | Router search params / path params |
| **Ephemeral UI** | Modal open, hover, draft caret | Component `useState` / `useReducer` |
| **Form draft** | Controlled fields before submit | Local state or form library; submit → server mutation |
| **Cross-feature client** | Theme, sidebar collapsed, wizard step across pages | Context or small store (Zustand) if many consumers |
| **Complex client domain** | Large offline editor, undo stacks, multi-entity client graph | Redux Toolkit / explicit event model if complexity warrants |
| **Auth session** | Tokens, current user bootstrap | Established auth module only; never ad-hoc duplicates |

### Client state vs server state

| | Client state | Server state |
| --- | --- | --- |
| Source of truth | The browser session / user device | Backend (or BFF) |
| On refresh | Often reset or rehydrate from storage | Refetch or hydrate from cache policy |
| Failure modes | Rare network; mostly logic | Loading, error, stale, conflict |
| Tooling focus | Predictable updates, minimal globals | Cache keys, invalidation, deduping, retries |

**Rule of thumb:** If the data is **from an API and must stay fresh**, it is
server state. If it **only exists to drive UI chrome**, it is client state.

## When To Use Which Tool

### Local React state (`useState` / `useReducer`)

**Use when:** one component or a tight parent/child tree; simple transitions.

**Avoid when:** many distant consumers need the same mutable data; or you are
caching server entities by id.

### URL state

**Use when:** users should share/bookmark/back-button the view (filters, sort,
pagination, selected entity id in master-detail).

**Avoid when:** high-frequency ephemeral UI (every keystroke without debounce),
or secrets.

### React Context

**Use when:** low-frequency values widely needed (theme, locale, auth **handle**,
feature flags); dependency injection of services.

**Avoid when:** high-frequency updates (pointer position, per-keystroke) without
splitting contexts; replacing a query cache; dumping the entire app state into
one mega-provider.

### Zustand (or similar atomic/small store)

**Use when:** cross-route client state with simple setters; less boilerplate than
Redux; selective subscriptions matter.

**Avoid when:** the repo is already standardized on Redux Toolkit; or the “store”
is only caching GET `/orders` (use the server-state library).

### Redux Toolkit (or equivalent Flux)

**Use when:** complex client-side domain logic, time-travel/debug requirements,
many interacting updates, middleware ecosystem already adopted, or team standard.

**Avoid when:** greenfield simple apps with only CRUD lists (Query + local state
usually enough); or dual-writing every API response into slices without RTK Query.

### TanStack Query / SWR / RTK Query

**Use when:** fetching, caching, deduping, revalidation, mutations + invalidation.

**Avoid when:** pure UI toggles; treating query cache as a general event bus.

### Decision sketch

```text
Is it from the network / must reflect backend?
  yes → server-state library (Query/SWR/RTK Query/Apollo)
  no  → Must it be shareable via URL / back button?
          yes → router/URL state
          no  → Only one subtree needs it?
                  yes → useState / useReducer
                  no  → Low-frequency, inject-style?
                          yes → Context
                          no  → Repo has Redux standard or complex domain?
                                  yes → Redux Toolkit (or RTK Query if server)
                                  no  → Zustand / small store
```

## Workflow Details For Stores

1. **Normalize ownership** — one write path per entity; no silent dual updates.
2. **Select minimal slices** — consumers subscribe to what they need (selector /
   shallow compare) to avoid whole-tree rerenders.
3. **Invalidate, don’t duplicate** — after mutations, invalidate query keys or
   update cache explicitly; do not keep a second full copy in Zustand “for speed”
   without a documented sync strategy.
4. **Reset on auth boundaries** — logout clears user-scoped client stores and
   query caches.
5. **SSR safety** — no `window` at module scope; per-request store instances when
   required by the framework.

## Good / Bad Examples

### Server state in a query library

**Good**

```tsx
// Orders come from the API — cache belongs to TanStack Query
const { data, isPending, error } = useQuery({
  queryKey: ["orders", filters],
  queryFn: ({ signal }) => fetchOrders(filters, { signal }),
});

if (isPending) return <Spinner />;
if (error) return <ErrorBanner error={error} />;
return <OrderTable orders={data} />;
```

**Bad** — hand-copy server data into a global client store as the only cache:

```tsx
// Bad: reimplements cache, loading, race handling poorly
const setOrders = useStore((s) => s.setOrders);
useEffect(() => {
  fetchOrders(filters).then(setOrders);
}, [filters]);
const orders = useStore((s) => s.orders);
```

### UI state stays local

**Good**

```tsx
function OrderTable({ orders }: { orders: Order[] }) {
  const [selectedId, setSelectedId] = useState<string | null>(null);
  // selection only matters here
  return (
    <>
      <List orders={orders} selectedId={selectedId} onSelect={setSelectedId} />
      {selectedId ? <Detail orderId={selectedId} /> : null}
    </>
  );
}
```

**Bad** — global store for a single-table selection with one consumer.

### URL for shareable filters

**Good**

```tsx
const [params, setParams] = useSearchParams();
const status = params.get("status") ?? "open";

function onStatusChange(next: string) {
  setParams((p) => {
    p.set("status", next);
    return p;
  });
}
```

**Bad** — Zustand `filters` only, so refresh/share loses the view users care about.

### Context for low-frequency DI

**Good**

```tsx
const ThemeContext = createContext<"light" | "dark">("light");

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light");
  const value = useMemo(() => ({ theme, setTheme }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}
```

**Bad** — one Context holding `{ user, orders, cart, modals, formDrafts, mouseX }`
updated constantly → entire app rerenders.

### Zustand for cross-route client UI

**Good**

```ts
import { create } from "zustand";

type SidebarState = {
  collapsed: boolean;
  toggle: () => void;
};

export const useSidebarStore = create<SidebarState>((set) => ({
  collapsed: false,
  toggle: () => set((s) => ({ collapsed: !s.collapsed })),
}));
```

**Bad** — `useSidebarStore` also stores `orders: Order[]` fetched ad hoc.

### Redux when complexity is real

**Good** — documentable transitions, middleware, entity adapters for a large
client-side editor; or RTK Query as the **one** server cache.

**Bad** — Redux slice per checkbox on a marketing page with three components.

### Mutation + invalidation

**Good**

```tsx
const queryClient = useQueryClient();
const mutation = useMutation({
  mutationFn: updateOrder,
  onSuccess: () => {
    void queryClient.invalidateQueries({ queryKey: ["orders"] });
  },
});
```

**Bad** — mutate API then only `setState` locally; next navigation shows stale list.

## Anti-Patterns

- Dual source of truth: same entity in Query cache and Redux/Zustand without rules
- “Global store for everything” because prop drilling felt annoying once
- Putting form keystrokes in Redux/Zustand without need
- Fetching inside reducers/store setters with no cancellation or error surface
- Mega-Context value recreated every render (`value={{ ... }}` without memo)
- Persisting secrets or tokens in `localStorage` stores against repo auth policy
- Ignoring logout/reset → cross-user data flash
- New state library in one feature while the monorepo standard is another
- Optimistic updates without rollback on failure
- Treating URL as optional when product needs shareable views

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Client vs server state, Redux/Zustand/Context/Query choice | **This skill** | — |
| Component/hooks/props structure | `react-component-patterns` | this for where state lives |
| Abort, stale responses, concurrent fetches | `async-concurrency-patterns` | this for cache ownership |
| Production correctness, errors, resources, tests, security | `code-quality-standards` | **always apply** on implementation |
| TS style for store typings | `typescript-style-and-eslint` | this for architecture |
| Naming stores/slices/keys | `naming-conventions-general` | — |
| User-visible error copy for failed loads | `error-message-ux-writing` | this for error state ownership |

### Routing to `code-quality-standards`

Keep **this skill primary** for state ownership and library choice. Always apply
**`code-quality-standards`** as the implementation baseline when code changes:

- Single source of truth; no hidden global synchronization hacks
- Errors from fetches/mutations observable — not swallowed in stores
- Resources and subscriptions cleaned up; caches bounded where relevant
- Auth-sensitive state cleared on session end; no secrets in logs
- Tests for invalidation, optimistic rollback, and reset-on-logout when risk is high
- Validate untrusted URL/localStorage input before it becomes app state

This skill specializes **state classification and tool selection**. It does not
replace component structure patterns, general quality gates, or visual design.

## Checklist

- [ ] Repo state stack and neighboring feature patterns identified
- [ ] Each new state field classified: server / URL / ephemeral UI / cross-feature client / complex domain
- [ ] Lowest capable layer chosen; no new library without need
- [ ] Server state uses the project cache library (not a hand-rolled global copy)
- [ ] Shareable view state in the URL when product requires it
- [ ] Context limited to low-frequency or DI-style values; split high-frequency updates
- [ ] Zustand/Redux justified by cross-tree client needs or existing standards
- [ ] One write path per entity; invalidation strategy after mutations documented
- [ ] Selectors/subscriptions minimize rerenders
- [ ] Logout/session switch resets user-scoped state and caches
- [ ] SSR/RSC constraints respected (no shared mutable singleton across requests)
- [ ] `code-quality-standards` applied for errors, security, cleanup, and verification
- [ ] Component wiring follows `react-component-patterns` when implementing UI
