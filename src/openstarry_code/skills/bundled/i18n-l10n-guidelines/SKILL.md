---
name: i18n-l10n-guidelines
description: >
  Internationalization and localization patterns for apps: no hardcoded UI
  strings, message catalogs, ICU plurals/interpolation, locale negotiation,
  dates/numbers/currency, RTL, and pseudo-loc. Use when i18n, l10n, 国际化,
  本地化, localization, react-i18next, next-intl, FormatJS, ICU messages,
  locale, RTL, or translating UI. Complements code-quality-standards.
---

# i18n / l10n Guidelines

**Internationalization (i18n)** makes software ready for multiple locales.
**Localization (l10n)** supplies locale-specific strings and formats. Prefer
extractable message catalogs, stable keys, and locale-aware formatters over
string concatenation and hardcoded UI copy.

This skill covers frontend/app patterns; follow the repo’s existing i18n library
and locale set. It is not a translation-vendor process manual.

## Use When

- Adding or refactoring UI copy, labels, errors, emails, or empty states
- Introducing multi-locale support or a new language
- Fixing hardcoded strings, broken plurals, or brittle concatenation
- Formatting dates, numbers, currency, units, or lists per locale
- RTL layout, locale routing (`/en/`, `/zh-CN/`), or language switchers
- User mentions: i18n, l10n, 国际化, 本地化, localization, translation keys,
  ICU, react-intl, i18next, next-intl, gettext, RTL, `zh-CN`, locale

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Accessibility names/roles/keyboard | `accessibility-a11y-checklist` |
| Error *tone* and stable error codes | `error-message-ux-writing` |
| General implementation quality | `code-quality-standards` |
| API versioning / contract evolution | `api-versioning-design` |
| Log message style (operators) | `logging-message-style` |

## Repo Config First

Repo i18n stack, locale inventory, and extraction tooling **outrank** defaults.

1. **Library:** react-i18next, next-intl, FormatJS/react-intl, vue-i18n,
   Angular i18n, gettext/Fluent, Flutter `intl`, or server-side catalogs —
   **match it**
2. **Catalog layout:** `locales/en.json`, namespaces per feature, ICU vs
   mustache placeholders, flat vs nested keys — copy nearby modules
3. **Source locale:** usually `en` or `en-US`; document which is canonical
4. **Locale list & fallback:** supported BCP 47 tags, fallback chain
   (`zh-HK` → `zh-Hans` → `en`), and behavior when a key is missing
5. **Routing / detection:** path prefix, subdomain, cookie, `Accept-Language`,
   user profile preference — do not invent a second negotiation path
6. **Extraction/CI:** formatjs extract, i18next-parser, lingui, eslint
   `i18next/no-literal-string`, crowdin/lokalise pipelines already in repo
7. **Formatting:** `Intl.*`, library wrappers, or shared `formatDate` helpers —
   reuse project utilities
8. **Design/RTL:** logical CSS (`margin-inline`), existing dir="rtl" patterns
9. **Neighbor skills:** user-visible errors still need stable `code`s
   (`error-message-ux-writing`); a11y labels must be translated
   (`accessibility-a11y-checklist`)

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that ship user-visible English-only on a multi-locale product
path, or that break RTL critical flows.

## Core Principles

| Principle | Practice |
| --- | --- |
| No hardcoded UI strings | User-visible text lives in catalogs (or framework message files) |
| Stable keys | Semantic keys (`checkout.payNow`) or documented ID policy; avoid renumbering |
| Full sentences | Translate whole sentences; do not stitch grammar from fragments |
| Named placeholders | `{name}`, `{count}` — not positional `%s` soup when avoidable |
| ICU plurals/select | Use plural/select categories; never `count === 1 ? …` in UI code for grammar |
| Locale-aware format | Dates, numbers, currency via `Intl` / shared helpers, not hand-rolled |
| Separate code from copy | Translators edit catalogs; code owns keys and placeholder contracts |
| Fallback safely | Missing translation falls back without crashing; log in dev |
| Don’t translate everything | Locale tags, log codes, API enums, feature flags stay stable |
| Test with pseudo-loc | Stretch strings and RTL before release |

## What To Externalize vs Keep in Code

| Externalize (l10n) | Keep stable (usually not translated) |
| --- | --- |
| Buttons, labels, titles, nav | Error/machine `code` (`PAYMENT_DECLINED`) |
| Validation and empty states | Feature flag names, analytics event names |
| Email/SMS user bodies (templates) | Internal log messages (see logging skill) |
| `aria-label` / alt when product-facing | Protocol enums, ISO currency codes in APIs |
| Legal marketing blurbs in-app | User-generated content (moderate; don’t “translate” blindly) |

Brand names may stay untranslated by policy; document exceptions.

## Workflow

1. **Discover repo i18n.**
   - Library, catalogs, namespaces, scripts (`extract`, `validate`), CI checks
   - Supported locales and fallback; how user locale is chosen
2. **Inventory strings in the change.**
   - UI copy, ARIA labels, tooltips, errors, emails, images with text
   - Hardcoded concatenations and plural branches
3. **Choose keys and namespace.**
   - Follow existing naming (`feature.section.purpose`)
   - Prefer intent over UI location alone if copy is reused
4. **Write source messages as full ICU-friendly sentences.**
   - Placeholders for variables; plural/select as needed
   - Never embed HTML blindly; use rich-text APIs the library supports
5. **Wire code to t()/FormattedMessage/useTranslations.**
   - Pass values as named params; format dates/numbers outside or with formatters
6. **Format locale-sensitive data.**
   - `Intl.NumberFormat`, `DateTimeFormat`, `RelativeTimeFormat`, `ListFormat`
   - Time zones: store UTC/instant; display in user or explicit zone
7. **Layout for expansion and RTL.**
   - Allow ~30–50% text growth; avoid fixed-width text containers
   - Use logical properties; mirror icons only when direction-dependent
8. **Extract and sync.**
   - Run extractors; add keys to all locale files or mark TODO via pipeline
   - Do not ship empty keys for required locales without fallback policy
9. **Verify.**
   - Switch locale in UI; pseudo-locale; RTL smoke; missing-key reporting
   - Snapshot tests: prefer keys/codes over full translated prose unless intentional

## Message Design

### Keys

```text
# good — stable, semantic
cart.itemCount
settings.privacy.saveSuccess
auth.errors.sessionExpired

# bad — brittle or opaque
str_1842
page2.div.span.text
Click_here_button_v3
```

### Interpolation

**Good** — whole sentence, named placeholder:

```json
{
  "welcome.user": "Welcome back, {name}."
}
```

```ts
t("welcome.user", { name: displayName });
```

**Bad** — concatenated fragments:

```ts
// Broken in many languages (order/gender/grammar)
t("welcome.prefix") + name + t("welcome.suffix");
```

### Plurals (ICU)

**Good**

```json
{
  "cart.itemCount": "{count, plural, =0 {Your cart is empty} one {# item} other {# items}}"
}
```

**Bad**

```ts
const label = count === 1 ? "1 item" : `${count} items`;
```

### Select / gender / status (when required)

```json
{
  "order.state": "{status, select, shipped {Shipped} pending {Pending} other {Updated}}"
}
```

Prefer explicit product status copy over grammatical gender unless the locale
process requires it.

### Rich text

Use the library’s rich/component interpolation (`<link>`, `<bold>`) so translators
see structure. Avoid `dangerouslySetInnerHTML` with translated raw HTML unless
the pipeline sanitizes and the repo already does this safely.

## Locale, Negotiation, and Routing

| Topic | Guidance |
| --- | --- |
| Tags | BCP 47: `en`, `en-US`, `zh-CN`, `zh-TW`, `pt-BR` — be consistent |
| Detection order | Documented: user setting → cookie → `Accept-Language` → default |
| URL strategy | Match repo: prefix `/zh-CN/…`, subdomain, or query; keep canonical links |
| Fallback | Chain to source locale; never blank the whole page on one missing key |
| Language switcher | Sets preference + navigates; does not leave mixed-locale chrome |

## Dates, Numbers, Currency

**Good**

```ts
const price = new Intl.NumberFormat(locale, {
  style: "currency",
  currency: "USD",
}).format(amount);

const day = new Intl.DateTimeFormat(locale, {
  dateStyle: "medium",
  timeZone,
}).format(instant);
```

**Bad**

```ts
const price = `$${amount.toFixed(2)}`; // locale, symbol position, separators wrong
const day = `${mm}/${dd}/${yyyy}`; // US-centric
```

- Money: pass **numeric amount + currency code**; format at the edges
- Do not pre-format strings in the API if clients must localize (unless API is display-only by contract)

## RTL and Layout

- Set `dir="rtl"` / `dir="ltr"` from locale (or `dir="auto"` only where appropriate)
- Prefer CSS logical properties: `margin-inline-start`, `padding-inline`, `inset-inline`
- Flip directional icons (chevrons, back arrows); do not mirror universal glyphs (play, checkmarks) blindly
- Check overflow, truncation (`text-overflow`), and sticky columns in RTL
- Forms and tables: alignment and column order remain readable

## Good / Bad Examples

### Hardcoded vs catalog

**Good**

```tsx
<button type="submit">{t("checkout.payNow")}</button>
```

**Bad**

```tsx
<button type="submit">Pay now</button>
```

### Error copy + stable code

**Good**

```ts
// code stays stable for clients/metrics; message is localized
return {
  code: "PAYMENT_CARD_DECLINED",
  message: t("errors.payment.cardDeclined"),
};
```

**Bad**

```ts
return { message: "Your card was declined." }; // English-only, no code
```

### String split (grammar trap)

**Good**

```json
{
  "files.uploaded": "{name} uploaded {count, plural, one {# file} other {# files}}."
}
```

**Bad**

```ts
`${user} uploaded ${n} file` + (n === 1 ? "" : "s");
```

### Shared formatter helper

**Good**

```ts
// reuse project helper
formatCurrency(amountCents / 100, { locale, currency });
```

**Bad**

```ts
// each feature reimplements separators differently
```

### Namespace hygiene

**Good** — feature namespace, reuse common actions:

```text
common.cancel
common.save
settings.profile.title
```

**Bad** — duplicate “Cancel” keys per screen with divergent translations and no reuse policy.

### Pseudo-localization mindset

**Good** — CI or dev locale `en-XA` / accented wrappers to catch overflow and missing keys.

**Bad** — only testing LTR English at perfect string lengths.

## Anti-Patterns

- Hardcoded user-visible strings in components, templates, or mobile views
- Building sentences from translated word fragments
- Plural logic in code (`if count == 1`) for natural-language grammar
- Positional format args that translators cannot reorder safely
- Translating machine codes, enums, or API paths that clients branch on
- Embedding unescaped user input into HTML translations
- One giant JSON for all apps without namespaces (merge hell) *or* chaotic key sprawl with no conventions
- Shipping half-translated locales without fallback or QA
- Forcing all users into browser language while ignoring account preference
- Fixed-width buttons that clip German or Finnish strings
- Assuming all CJK is “one Chinese”; distinguish `zh-CN` / `zh-TW` / etc. per product

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| i18n architecture, catalogs, no hardcoded UI strings, 国际化 | **This skill** | — |
| Accessible names must also be translated | **This skill** | `accessibility-a11y-checklist` |
| Error wording + stable codes | `error-message-ux-writing` | this for locale files |
| Log/operator messages | `logging-message-style` | — |
| Implementing extraction hooks, helpers, tests | **This skill** | `code-quality-standards` |
| TS/JS style of i18n wrappers | language style skill | this for patterns |

### Routing to `code-quality-standards`

Keep **this skill primary** for localization structure and message design. Always
apply **`code-quality-standards`** when implementing i18n plumbing:

- Fail safely on missing keys (fallback + diagnostics), not uncaught exceptions in prod
- Validate locale tags at boundaries; reject or normalize unknown tags per policy
- Keep pure formatting helpers testable; freeze behavior with table-driven locale cases
- Do not log PII from translation params; redact secrets in debug catalogs
- Cover critical paths with tests that assert keys/codes and a sample locale render
- Avoid global mutable locale state races in concurrent/SSR contexts
  (`async-concurrency-patterns` when relevant)

This skill specializes **multi-locale readiness and copy externalization**. It
does not replace reliability, security, or general test policy.

## Checklist

- [ ] Repo i18n library, catalog layout, locales, and fallback chain identified
- [ ] Locale negotiation / routing matched (no second competing mechanism)
- [ ] No new user-visible hardcoded strings in the changed surface
- [ ] Keys follow project naming/namespaces; stable and semantic
- [ ] Messages are full sentences with named placeholders
- [ ] Plurals/select use ICU (or library equivalent), not ad-hoc code branches
- [ ] Dates/numbers/currency use locale-aware formatters
- [ ] Time zone strategy clear (store instant; display with zone)
- [ ] RTL / logical CSS checked when supporting RTL locales
- [ ] Layout tolerates string expansion; critical controls not clipped
- [ ] `aria-label` / alt / errors go through catalogs when localized
- [ ] Machine `code`s remain stable; only human text is translated
- [ ] Extract/validate scripts run; catalogs updated for supported locales
- [ ] Missing-key behavior verified; pseudo-loc or second locale smoke done
- [ ] SSR/hydration locale consistency checked when applicable
- [ ] `code-quality-standards` applied for helpers, boundaries, and tests
