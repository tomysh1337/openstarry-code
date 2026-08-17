---
name: accessibility-a11y-checklist
description: >
  Frontend accessibility (a11y) testing checklist at WCAG high level: semantic
  HTML, keyboard, focus, names/roles, contrast, forms, media, and ARIA discipline.
  Use when accessibility, a11y, 无障碍, WCAG, screen reader, keyboard navigation,
  ARIA, focus trap, color contrast, or accessible UI review. Complements
  code-quality-standards; does not replace product design systems or legal audits.
---

# Accessibility (a11y) Checklist

Practical **WCAG-oriented** checklist for building and reviewing UI so people can
perceive, operate, understand, and use content with assistive tech and keyboards.
This skill is **engineering guidance**, not a formal conformance audit or legal
advice. Prefer the product’s design system and accessibility policy when present.

Target orientation: **WCAG 2.2 Level AA** patterns at a high level (perceivable,
operable, understandable, robust). Cite specific success criteria only when the
repo or compliance target requires them.

## Use When

- Building or reviewing UI for keyboard, screen reader, contrast, or forms a11y
- Adding modals, menus, custom controls, tables, or rich media
- Fixing audit findings (axe, Lighthouse, WAVE, manual SR pass)
- Choosing native HTML vs ARIA; fixing focus order and focus traps
- User mentions: accessibility, a11y, 无障碍, WCAG, ARIA, screen reader,
  键盘可访问, 对比度, focus visible, alt text, accessible name

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| General code reliability, security, tests | `code-quality-standards` |
| User-facing error *copy* wording | `error-message-ux-writing` |
| i18n/l10n string extraction and locales | `i18n-l10n-guidelines` |
| Visual polish / brand UI only | `frontend-design` / design skills |
| XSS / DOM sink security testing | `xss-cross-site-scripting` |

## Repo Config First

Repo design system, a11y policy, and tooling **outrank** this skill’s defaults.

1. **Policy / target:** WCAG level (A/AA/AAA), Section 508, EN 301 549, internal
   checklist, or “best effort” — match the stated bar
2. **Design system:** existing accessible components (Button, Dialog, Tabs,
   Select) — **reuse** them; do not reimplement primitives without cause
3. **Tooling:** axe-core/jest-axe, eslint-plugin-jsx-a11y, Storybook a11y addon,
   Playwright/Cypress a11y, Lighthouse CI gates already in the repo
4. **Tokens:** color contrast pairs, focus ring tokens, motion/reduced-motion
   tokens, type scale minimums documented in Figma/tokens
5. **Patterns nearby:** how modals trap focus, how toasts are announced, skip
   links, landmark layout in app shells
6. **i18n:** accessible names and `aria-label` must go through locale catalogs
   when the app is localized (`i18n-l10n-guidelines`)
7. **Framework helpers:** React Aria / Radix / Headless UI / Angular CDK a11y /
   Flutter Semantics — prefer project-standard libraries

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that would ship inaccessible critical paths (auth, pay, delete).

## Core Principles

| Principle | Practice |
| --- | --- |
| Native first | Prefer `<button>`, `<a href>`, `<label>`, `<input>`, landmarks over div+ARIA |
| Name, role, value | Every interactive control has an accessible name and correct role/state |
| Keyboard parity | All pointer actions reachable and completable via keyboard |
| Visible focus | `:focus-visible` (or equivalent) never removed without a clear replacement |
| Don’t sole-rely on color | Errors, required, selection also use text/icon/pattern |
| Structure over style | Headings, lists, tables, and landmarks convey structure |
| ARIA is a patch | No ARIA is better than wrong ARIA; fix HTML first |
| Announce changes | Live regions / focus moves for async and dialog results |
| Respect user settings | `prefers-reduced-motion`, zoom to ~200%, high contrast where feasible |
| Test with real tools | Automated **plus** keyboard **plus** one screen reader pass on critical flows |

## Workflow

1. **Inventory critical paths.**
   - Auth, search, checkout/pay, create/edit/delete, settings, navigation
   - Custom widgets (date pickers, menus, virtual lists, canvases)
2. **Check design system coverage.**
   - Use existing accessible primitives; note gaps needing new patterns
3. **Semantics pass.**
   - One `<h1>` per view (or documented exception); logical heading order
   - Landmarks: `header`/`nav`/`main`/`footer`/`aside` (or ARIA equivalents once)
   - Lists for list-like UI; tables for tabular data with headers
4. **Keyboard and focus pass.**
   - Tab order matches visual reading order; no keyboard traps
   - Modals: focus in on open, restore on close, Escape closes when expected
   - Skip link to main content on multi-chrome layouts
5. **Name and control pass.**
   - Icon-only buttons have accessible names
   - Form fields have programmatic labels; errors associated (`aria-describedby`)
   - Links: descriptive text (avoid “click here” alone)
6. **Sensory and media pass.**
   - Contrast for text/UI components vs background (AA targets as policy)
   - Text alternatives for meaningful images; decorative images empty/alt suppressed
   - Captions/transcripts for video/audio when product requires
7. **Dynamic UI pass.**
   - Loading/error toasts: polite/assertive live regions as appropriate
   - Route changes: focus management to main heading or consistent target
8. **Automate and manually verify.**
   - Run project a11y linters/tests; fix serious/critical first
   - Manual keyboard-only pass; one SR smoke (NVDA/VoiceOver/JAWS per platform)
9. **Document exceptions.**
   - Known gaps, third-party widgets, and tracked remediations

## High-Level WCAG Map (orientation)

| Theme | High-level expectations (AA-oriented) |
| --- | --- |
| Perceivable | Text alternatives; captions when required; adaptable structure; contrast; text resize/zoom; not color-only |
| Operable | Keyboard accessible; enough time; no seizure flashes; navigable (titles, focus order, link purpose); input modalities |
| Understandable | Readable language; predictable navigation/focus; input assistance (labels, errors, suggestions) |
| Robust | Valid-enough markup; name/role/value for components; compatible with AT |

Do not claim “WCAG AA compliant” from this checklist alone without a defined
audit process and product policy.

## Component Quick Checks

### Buttons and links

- Buttons perform actions; links navigate (correct element and semantics)
- Disabled state is exposed and not focus-trapping oddly
- Hit target reasonably large (design system minimum)

### Forms

- Visible label + programmatic association (`label for` / wrapping / `aria-labelledby`)
- Required fields indicated in text or programmatically, not color alone
- Errors: identified, described, and focus moved or summarized accessibly
- Do not use `placeholder` as the only label

### Dialogs / drawers

- `role="dialog"` (or native `<dialog>`) + labelled by title
- Focus trap while open; background inert/aria-hidden as pattern requires
- Initial focus on logical control; return focus to invoker on close

### Menus, tabs, comboboxes

- Prefer design-system/Radix/React Aria patterns for arrow-key models
- `aria-expanded`, `aria-selected`, `aria-controls` kept in sync with UI
- Typeahead and active descendant only when implementing full pattern correctly

### Images and icons

- Meaningful: non-empty `alt` (or accessible name on SVG)
- Decorative: `alt=""` / `aria-hidden="true"` so AT skips them
- Informative icon beside text: hide icon from AT to avoid double speech

### Tables

- `<th>` with `scope` or explicit headers; caption/summary when helpful
- Do not use tables for layout

## Good / Bad Examples

### Semantic control

**Good**

```html
<button type="button" aria-expanded="false" aria-controls="filters-panel">
  Filters
</button>
```

**Bad**

```html
<div class="btn" onclick="toggleFilters()">Filters</div>
```

### Icon-only button name

**Good**

```html
<button type="button" aria-label="Close dialog">
  <svg aria-hidden="true" focusable="false">…</svg>
</button>
```

**Bad**

```html
<button type="button"><svg>…</svg></button>
<!-- No accessible name; SR may say "button" only -->
```

### Form label and error

**Good**

```html
<label for="email">Email</label>
<input id="email" type="email" autocomplete="email"
       aria-invalid="true" aria-describedby="email-err" />
<p id="email-err" role="alert">Enter an email like name@company.com.</p>
```

**Bad**

```html
<input type="text" placeholder="Email" />
<span style="color:red">Invalid</span>
<!-- Placeholder-only label; error not associated -->
```

### Focus styles

**Good**

```css
/* Keep a visible focus indicator; match design tokens */
:focus-visible {
  outline: 2px solid var(--focus-ring);
  outline-offset: 2px;
}
```

**Bad**

```css
*:focus {
  outline: none; /* removed with no replacement */
}
```

### Color not sole indicator

**Good**

```html
<p><span class="error-icon" aria-hidden="true"></span> Password is required</p>
```

**Bad**

```html
<!-- Only red border, no text/icon explaining the error -->
<input style="border-color: red" />
```

### Live region for async status

**Good**

```html
<div aria-live="polite" aria-atomic="true" class="sr-only" id="status"></div>
<!-- On save success: status.textContent = "Settings saved." -->
```

**Bad**

```html
<!-- Status only changes a green checkmark image with empty alt; no announcement -->
```

### Heading / landmark structure

**Good**

```html
<body>
  <a class="skip-link" href="#main">Skip to main content</a>
  <header>…</header>
  <nav aria-label="Primary">…</nav>
  <main id="main">
    <h1>Account settings</h1>
    <h2>Security</h2>
  </main>
</body>
```

**Bad**

```html
<div class="header">…</div>
<div class="content">
  <div class="title-xl">Account settings</div>
  <div class="title-lg">Security</div>
</div>
```

### Wrong ARIA

**Good** — native element, minimal ARIA:

```html
<nav aria-label="Breadcrumb">
  <ol>
    <li><a href="/">Home</a></li>
    <li aria-current="page">Billing</li>
  </ol>
</nav>
```

**Bad**

```html
<div role="button" tabindex="0" aria-label="Submit" role="link">Submit</div>
<!-- Conflicting roles; reinvented button -->
```

## Anti-Patterns

- Removing focus outlines globally
- `div`/`span` click handlers without keyboard and role support
- Positive `tabindex` values that scramble order (`tabindex="1"+`)
- `aria-hidden="true"` on focusable elements still in tab order
- Accessible name mismatch vs visible label (WCAG label-in-name issues)
- Auto-playing media with sound; flashing content
- Infinite carousels that cannot be paused
- Opening modals without focus management
- Relying only on automated axe scores as “done”
- Hard-coding English `aria-label` in a multi-locale app
- Claiming full WCAG compliance without audit scope and evidence

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| a11y review, WCAG checklist, keyboard/SR, ARIA | **This skill** | — |
| Implementing accessible components in product code | **This skill** | `code-quality-standards` |
| Error message wording for users | `error-message-ux-writing` | this for association/announce |
| Locale strings, RTL, pluralization | `i18n-l10n-guidelines` | this for translated accessible names |
| Visual design system polish | design/frontend skills | this for a11y constraints |
| XSS via DOM sinks in UI | `xss-cross-site-scripting` | — |

### Routing to `code-quality-standards`

Keep **this skill primary** for accessibility criteria and review order. Always
apply **`code-quality-standards`** when implementing or fixing UI:

- Prefer clear component APIs; avoid inaccessible defaults in shared primitives
- Validate props for required labels on icon-only controls at boundaries
- Add regression tests (unit/component/e2e) for focus, names, and critical paths
- Do not “fix” a11y by disabling lint rules without a tracked exception
- Keep behavior stable: focus restore and Escape handlers must be reliable
- Treat a11y bugs with the same severity process as other user-blocking defects

This skill specializes **accessible UX structure and verification**. It does not
replace reliability, security, or general test policy.

## Checklist

- [ ] Repo a11y target, design-system components, and tooling identified
- [ ] Critical user paths listed (including auth and destructive actions)
- [ ] Semantic HTML / landmarks / heading order verified
- [ ] All interactive elements keyboard operable; no traps
- [ ] Focus visible; modal focus in/out and restore correct
- [ ] Controls have accessible names; roles/states accurate
- [ ] Forms: labels, required indication, associated errors
- [ ] Images/icons: meaningful vs decorative handled
- [ ] Color not the only cue; contrast meets policy targets
- [ ] Dynamic updates announced or focused appropriately
- [ ] Motion respects `prefers-reduced-motion` where applicable
- [ ] Zoom/reflow does not break essential tasks (per policy)
- [ ] Automated a11y checks run; serious issues fixed or tracked
- [ ] Manual keyboard pass done; SR smoke on critical flows
- [ ] Localized accessible strings via i18n when app is multi-locale
- [ ] Third-party widgets reviewed or wrapped for a11y
- [ ] `code-quality-standards` applied for implementation quality and tests
