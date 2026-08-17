---
name: vue-component-patterns
description: >
  Structure Vue 3 components with Composition API, props/emits, slots, and
  colocation. Use when Vue, Vue 3, Composition API, props, emits, script setup,
  Vue 组件, 组合式 API, 组件结构, defineProps, defineEmits, or when reviewing
  Vue UI structure. Pairs with code-quality-standards; does not replace repo
  Vue conventions, ESLint, or design systems. React counterpart:
  react-component-patterns.
---

# Vue Component Patterns

Engineering patterns for **Vue 3 component structure**: Composition API
(`<script setup>`), props/emits contracts, slots, state ownership, and file
colocation. Prefer the repo’s existing Vue style (Nuxt vs Vite SPA, Options vs
Composition, folder layout, UI kit) over inventing a second model.

## Use When

- Building or refactoring Vue 3 / Nuxt components
- Designing props, emits, `v-model`, or slot APIs
- Extracting or reviewing composables (`use*`)
- Deciding file colocation: component + styles + tests + composables
- Fixing Composition API misuse: unnecessary watchers, prop mutation, leaky setup
- User mentions: Vue, Vue 3, Composition API, props, emits, colocation, script setup,
  Vue 组件, 组合式 API, 组件结构, 自定义 composable, props 设计, 插槽

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| React components / hooks | `react-component-patterns` |
| Global client vs server state library choice | `state-management-guidelines` (adapt to Pinia/Vue) |
| Visual aesthetics, distinctive UI look | `frontend-design` / `top-design` |
| TS strictness, `any`, import order | `typescript-style-and-eslint` |
| Formatting only | `prettier-eslint-editorconfig` |
| Reliability, errors, tests, security hygiene | `code-quality-standards` |
| Concurrent fetch races / AbortSignal design | `async-concurrency-patterns` |
| a11y checklist | `accessibility-a11y-checklist` |

## Repo Config First

Repo config and neighboring Vue code **outrank** this skill’s defaults.

1. **Vue mode:** Vue 3 SPA (Vite), Nuxt 3/4 (SSR, server routes, auto-imports),
   micro-frontend host — SFC conventions and data-fetch placement differ
2. **API style already in tree:** `<script setup>` + Composition vs Options API
   legacy; match the dominant style in the feature; migrate only with intent
3. **Component library:** design system, Naive UI, Element Plus, Vuetify, Headless
   Vue — compose with them; do not reimplement primitives already in tree
4. **Folder conventions:** feature folders vs `components/` + `composables/`;
   Nuxt `components/` auto-import; `ComponentName/` colocation; story/test suffixes
5. **Lint / types:** `eslint-plugin-vue`, `vue-tsc`, Volar / Takeover mode,
   `tsconfig` paths, unplugin auto-import allowlists
6. **State stack already chosen:** Pinia, Vue Query / TanStack Query Vue,
   provide/inject — route global ownership to `state-management-guidelines`
7. **Styling system:** scoped CSS, CSS Modules, Tailwind, UnoCSS — match local
   pattern; do not introduce a second system mid-PR
8. **Neighboring components:** copy 2–3 mature feature SFCs for props/emits shape,
   loading/error UI, and composable extraction thresholds

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that mutate props, break one-way data flow, leak secrets to the
client, or ignore SSR/hydration constraints.

## Workflow

1. **State the UI contract.**
   - What the user sees/does; loading, empty, error, success
   - Parent-owned vs local state; who emits updates
   - SSR vs client-only responsibility (Nuxt data, client interactivity)
2. **Compose before you configure.**
   - Prefer small components + slots/default slot over giant prop matrices
   - Lift state only as far as shared consumers need it
3. **Shape props and emits for the caller.**
   - Domain names; narrow unions/types; avoid boolean soup
   - Explicit `defineEmits` types; payload shapes stable for parents
   - Prefer `defineModel` / `modelValue` + `update:modelValue` for two-way bindings
   - Document required vs optional; sensible defaults at the leaf
4. **Place state and side effects deliberately.**
   - Prefer `computed` over `watch` for pure derivation
   - Do not mutate props; emit events or use `v-model`
   - Extract composables when logic is reused or obscures the template
5. **Colocate by change frequency.**
   - Keep SFC, styles, tests, and private composables that change together nearby
   - Promote to shared only after a second real consumer appears
6. **Guard boundaries.**
   - Client-only code: no secrets; validate untrusted props/route query at edges
   - Lists: stable `:key` from identity, not array index (unless static)
   - `shallowRef` / `markRaw` only when measured or when deep reactivity is harmful
7. **Verify.**
   - `vue-tsc` / ESLint clean; typed public props/emits; smoke loading/error paths
   - Apply `code-quality-standards` for errors, cleanup, and tests

## Design Principles

| Principle | Practice |
| --- | --- |
| Single responsibility | One component answers one UI question; split layout vs logic vs data glue |
| Composition over configuration | slots, scoped slots, compound parts > 15 optional booleans |
| Props + emits are the public API | Stable names; break carefully; prefer additive changes |
| One-way data flow | Props down, events up; no silent prop mutation |
| Derive, don’t sync | `computed` for derived values; not `watch` + reassignment of mirrors |
| Watchers are escape hatches | External sync, imperative APIs — not pure transforms |
| Colocation | Code that changes together lives together |
| Accessibility is structure | Semantic elements, labels, focus — not only ARIA patches |

### Component structure (default skeleton)

When the repo has no stronger template:

```vue
<!-- FeatureCard.vue — presentational shell; data loaded by parent or composable -->
<script setup lang="ts">
type FeatureCardProps = {
  title: string;
  description?: string;
};

const props = defineProps<FeatureCardProps>();

const emit = defineEmits<{
  select: [];
}>();
</script>

<template>
  <article>
    <h3>{{ props.title }}</h3>
    <p v-if="props.description">{{ props.description }}</p>
    <button type="button" @click="emit('select')">Select</button>
  </article>
</template>
```

### Props and emits

| Do | Don’t |
| --- | --- |
| Type props with `defineProps<T>()` or runtime props + defaults | Leave public props untyped in TS codebases |
| Emit named events with typed payloads | Mutate `props.x` or emit vague `change` without payload docs |
| Use `withDefaults` / default values for optional leaf props | Require the parent to pass every cosmetic default |
| Prefer `defineModel()` for clean `v-model` when Vue 3.4+ is available | Hand-roll half-synced local copies of `modelValue` |
| Validate/normalize untrusted route/query before use | Trust URL strings as domain enums without a boundary |

### Composables

| Do | Don’t |
| --- | --- |
| Name `useX`; call in `setup` / `<script setup>` top level | Hide composable calls behind unpredictable branches that break SSR |
| Return refs/computed with a clear public surface | Return new object identities every call without need |
| Accept `AbortSignal` / `onScopeDispose` for async cleanup | Ignore cancellation (see `async-concurrency-patterns`) |
| Keep one concern per composable | `useGodObject` that fetches, caches, and formats everything |

### Colocation map (typical)

```text
features/orders/
  OrderList.vue
  OrderList.spec.ts
  OrderList.module.css   # or scoped / co-located Tailwind
  useOrderFilters.ts     # private to feature until reused
  api.ts                 # feature fetchers if not global
```

Promote `useOrderFilters` to `composables/` / `shared/` only when a second feature needs it.

### Nuxt / SSR notes

- Prefer Nuxt data utilities (`useAsyncData` / `useFetch`) already adopted by the repo
- Mark browser-only APIs with `onMounted`, `<ClientOnly>`, or `.client` plugins
- Pass serializable state across server→client boundaries; avoid non-serializable
  module singletons that leak across requests
- Do not fetch secrets or privileged tokens in client-only components

## Good / Bad Examples

### Props: composition vs boolean soup

**Good** — variant union + slots:

```vue
<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: "primary" | "secondary" | "danger";
  }>(),
  { variant: "primary" },
);
</script>

<template>
  <button type="button" :data-variant="props.variant">
    <slot />
  </button>
</template>
```

**Bad** — exploding booleans:

```ts
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

**Good** — `computed`:

```vue
<script setup lang="ts">
const props = defineProps<{ cents: number; taxRate: number }>();
const total = computed(() => Math.round(props.cents * (1 + props.taxRate)));
</script>

<template>
  <span>{{ (total / 100).toFixed(2) }}</span>
</template>
```

**Bad** — watch to re-copy derived values:

```vue
<script setup lang="ts">
const props = defineProps<{ cents: number; taxRate: number }>();
const total = ref(0);
watch(
  () => [props.cents, props.taxRate],
  () => {
    total.value = Math.round(props.cents * (1 + props.taxRate));
  },
  { immediate: true },
);
</script>
```

### v-model / one-way flow

**Good** — parent owns value; child emits updates:

```vue
<script setup lang="ts">
const model = defineModel<string>({ required: true });
</script>

<template>
  <input
    :value="model"
    aria-label="Search"
    @input="model = ($event.target as HTMLInputElement).value"
  />
</template>
```

**Bad** — mutate prop directly:

```vue
<script setup lang="ts">
const props = defineProps<{ modelValue: string }>();
function onInput(e: Event) {
  // Bad: mutates prop
  (props as { modelValue: string }).modelValue = (e.target as HTMLInputElement).value;
}
</script>
```

### Emits typing

**Good**

```ts
const emit = defineEmits<{
  save: [payload: { id: string }];
  cancel: [];
}>();

emit("save", { id: orderId });
```

**Bad**

```ts
const emit = defineEmits(["save", "cancel"]);
emit("save", orderId, true, "extra"); // untyped, unstable arity
```

### Composables with cleanup

**Good** — focused composable + dispose:

```ts
import { onScopeDispose, ref } from "vue";

export function useMediaQuery(query: string) {
  const matches = ref(false);
  if (typeof window === "undefined") return matches;

  const mql = window.matchMedia(query);
  const onChange = () => {
    matches.value = mql.matches;
  };
  onChange();
  mql.addEventListener("change", onChange);
  onScopeDispose(() => mql.removeEventListener("change", onChange));
  return matches;
}
```

**Bad** — mixed concerns, no cleanup:

```ts
export function useDashboard(userId?: string) {
  // fetches, websockets, form state, theme… no dispose
  if (!userId) return null;
}
```

### Lists and keys

**Good**

```vue
<OrderRow v-for="item in items" :key="item.id" :order="item" />
```

**Bad**

```vue
<OrderRow v-for="(item, index) in items" :key="index" :order="item" />
```

### Colocation vs premature share

**Good** — feature-private until second consumer.

**Bad** — `shared/components/MagicTable.vue` with 40 props used by one screen,
or three competing `AppButton` primitives in different folders.

## Anti-Patterns

- Prop drilling many levels when provide/inject or composition would clarify ownership
- God SFCs (fetch + form + table + modal in one file)
- `watch` / `watchEffect` for pure calculation, filtering, or mapping
- Mutating props or deep-mutating nested prop objects as a “shortcut”
- Disabling `vue/no-mutating-props` without a documented invariant
- Inline heavy logic in templates that belongs in `computed` or methods
- Spreading unknown attrs onto sensitive elements without understanding fallthrough
- Default-export-only patterns that fight named-export / Nuxt conventions in the repo
- Duplicating design-system primitives “just for this screen”
- Client components that embed API keys or privileged business rules
- Premature `v-memo` / manual ref splitting everywhere (noise, false safety)
- Mixing Options API and Composition API in the same new feature without a migration plan

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Vue component structure, props/emits, composables, colocation | **This skill** | — |
| React component structure (hooks, JSX) | `react-component-patterns` | compare patterns only |
| Client vs server state, Pinia/store choice | `state-management-guidelines` | this for component wiring |
| Production correctness, errors, resources, tests, security | `code-quality-standards` | **always apply** on implementation |
| TS/ESLint style only | `typescript-style-and-eslint` | this for component shape |
| Visual design / aesthetics | `frontend-design` / `top-design` | this for structure |
| Async cancel, stale responses, fan-out | `async-concurrency-patterns` | this for where composables live |
| Naming components/composables/files | `naming-conventions-general` | this for structure |
| a11y structure | `accessibility-a11y-checklist` | this for SFC shape |
| Comments on non-obvious UI invariants | `comment-writing-standards` | — |

### Routing to `code-quality-standards`

Keep **this skill primary** for Vue structure and composition. Always apply
**`code-quality-standards`** as the implementation baseline when code changes:

- Clear boundaries: UI vs data access vs domain rules
- Error and loading states handled; no swallowed failures in event handlers
- Subscriptions, timers, and listeners cleaned up (`onScopeDispose` / `onUnmounted`)
- Untrusted input (route query, form, `postMessage`) validated at the boundary
- Tests for critical interaction paths when blast radius warrants
- No secrets in client bundles or logs

### Routing to `react-component-patterns`

Use **`react-component-patterns`** when the stack is React (hooks, RSC, JSX).
Shared ideas transfer (composition, colocation, derive-don’t-sync), but **APIs
differ** (hooks vs composables, children vs slots, Context vs provide/inject).
Do not force React file shapes onto Vue SFCs. For Vue work, **this skill stays
primary**; treat the React skill as a cross-framework reference only.

This skill specializes **Vue components, props/emits, composables, and colocation**.
It does not replace general quality, security, global state-library choice, or
visual design systems.

## Checklist

- [ ] Repo Vue mode (SPA/Nuxt), folder layout, design system, and lint rules identified
- [ ] UI contract clear: loading / empty / error / success; ownership of state
- [ ] Composition preferred over large prop/boolean matrices
- [ ] Props typed and stable; emits typed with clear payloads; no prop mutation
- [ ] `v-model` / `defineModel` used cleanly when two-way binding is required
- [ ] State minimal; derived values via `computed`, not mirrored via watchers
- [ ] Watchers only for external sync; cleanup present; ESLint Vue rules satisfied
- [ ] Composables focused; dispose listeners/timers/subscriptions
- [ ] Colocation by feature; shared only with real second consumers
- [ ] List keys from stable identity; a11y basics (labels, semantics, focus)
- [ ] SSR/client boundary respected when using Nuxt / SSR
- [ ] Memoization / `v-memo` / shallow APIs only with a reason
- [ ] `code-quality-standards` applied for errors, cleanup, security, and verification
- [ ] React-only tasks routed to `react-component-patterns` instead of this skill
- [ ] State library choices deferred to `state-management-guidelines` when relevant
