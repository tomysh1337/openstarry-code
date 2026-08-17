---
name: output-encoding-patterns
description: >
  Context-aware output encoding and safe sinks to prevent XSS, SQL injection,
  and related injection via string composition: HTML/XML, attributes, JS, URL,
  CSS, SQL/NoSQL parameters, shell argv, and log encoding. Use when output
  encoding, 输出编码, contextual escaping, encode for HTML, parameterized
  queries, safe templates, or preventing XSS/SQLi in application code.
  Complements input-validation-patterns and code-quality-standards; not a full
  replacement for xss-cross-site-scripting or sqli-sql-injection assessment skills.
---

# Output Encoding Patterns

Encode or bind data for the **consumer context** so untrusted values cannot break
out of that context (HTML text, attributes, JavaScript strings, URLs, SQL, shell,
logs). Prefer **safe APIs and parameterized interfaces** over manual escaping.
Repository templates, ORM/query builders, and CSP/security headers **outrank**
generic defaults in this skill.

This skill is **defensive secure coding** for systems you own or are authorized
to harden. It is not guidance for exploiting XSS/SQLi against third-party systems.

## Use When

- Rendering **user or third-party data** into HTML, XML, JSON-in-HTML, Markdown→HTML
- Building **URLs, redirects, headers**, or CSS from dynamic values
- Writing **SQL/NoSQL/LDAP** access that might concatenate strings
- Choosing **template auto-escape**, React/Vue text vs raw HTML, or sanitizer libraries
- Fixing injection bugs by correcting **sink encoding** (not only inbound filters)
- Reviewing logging of user input (CRLF / forged log lines)
- User mentions: output encoding, **输出编码**, contextual escaping, HTML encode,
  上下文编码, parameterized query, prepared statement, `textContent` vs
  `innerHTML`, autoescape, OWASP encoders

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Inbound allowlists, schemas, boundary validation | `input-validation-patterns` |
| JSON Schema / OpenAPI contract design | `json-schema-design` |
| General reliability, errors, tests baseline | `code-quality-standards` |
| Authorized XSS testing methodology | `xss-cross-site-scripting` |
| Authorized SQLi testing methodology | `sqli-sql-injection` |
| Unknown injection class (assessment) | `injection-checking` |
| CSP policy bypass testing | `content-security-policy-bypass` |
| Secrets redaction policy in logs | `secrets-management-hygiene` + `logging-message-style` |

## Repo Config First

Repo frameworks, templates, and data-access layers **outrank** this skill.

1. **Template / UI stack:** React/Vue/Svelte/Angular, server templates (Jinja,
   Twig, ERB, Razor, Thymeleaf), email HTML builders — use each stack’s
   **auto-escape defaults** and documented “raw HTML” APIs only with policy
2. **Sanitizers already chosen:** DOMPurify, Bleach, sanitize-html, OWASP Java
   Encoder, etc. — match existing config (allowed tags/attr) rather than adding
   a second library
3. **Data access:** ORM, query builder, prepared statements, stored procedures —
   **reuse** parameter binding; do not introduce string-SQL helpers beside them
4. **Security headers / CSP:** existing CSP, `X-Content-Type-Options`, cookie flags —
   encoding complements CSP; do not weaken CSP to hide encoding bugs
5. **JSON APIs:** standard serializers (`json.dumps`, `JSON.stringify`, framework
   responders) — avoid hand-built JSON strings
6. **Logging stack:** structured loggers and field redaction — follow
   `logging-message-style` conventions already in tree
7. **Neighboring code:** copy mature encode/parameterize patterns from the same
   service before inventing utilities
8. **I18n templates:** locale files and message formats that auto-escape
   interpolations — keep user data out of raw HTML message keys

**Precedence:** If repo rules conflict with defaults below, follow the repo.
Surface conflicts that disable auto-escape globally, use `dangerouslySetInnerHTML`
without sanitization, or build SQL with string format.

## Core Principles

| Principle | Practice |
| --- | --- |
| Context is king | HTML text ≠ attribute ≠ JS ≠ URL ≠ CSS ≠ SQL; encode for the actual sink |
| Prefer safe sinks | `textContent`, parameterized queries, argv arrays, template auto-escape |
| Encode late | Keep data raw in the model; encode at the boundary of each consumer |
| Do not double-encode blindly | Know whether the framework already escaped; avoid broken UX and bypass confusion |
| Validation ≠ encoding | Allowlists help; they do not replace context encoding or bound parameters |
| Least power | Prefer structured builders over string templates for queries and shell |
| Defense in depth | Encoding + CSP + HttpOnly cookies + validation; no single control is enough |
| Codec matching | Same character set and parser the consumer uses (HTML5, JSON, specific DB) |

## Workflow

1. **Inventory sinks.**
   - HTML body/attribute, SVG/MathML, JSON embedded in `<script>`, Markdown HTML
   - URL path/query/fragment, `Location` header, `href`/`src`
   - SQL/NoSQL/LDAP/command line, CSS `style`, email MIME parts
   - Logs, CSV/spreadsheet exports (see also formula injection skill when assessing)
2. **Trace untrusted sources into each sink.**
   - Request fields, DB fields originally from users, partner APIs, admin notes
3. **Choose the control per sink (see Context Matrix).**
   - Prefer APIs that make injection unrepresentable
   - Fall back to vetted encoders for that context only
4. **Keep raw data in domain models.**
   - Do not store pre-HTML-escaped strings in the DB (breaks other channels and search)
5. **Handle rich text deliberately.**
   - If HTML is required: sanitizer with **allowlisted** tags/attr + CSP
   - Default: plain text + encode on render
6. **Cover non-HTML channels.**
   - SQL parameters, shell argv, header encoding, log structuring
7. **Verify.**
   - Unit tests with breakthrough payloads per context
   - Framework escape still on; no global auto-escape disable
   - Pair with `code-quality-standards` tests; use XSS/SQLi skills for authorized assessment depth

## Context Matrix

| Sink context | Do | Do not |
| --- | --- | --- |
| HTML **text** node | Auto-escape templates; `textContent`; framework text bindings | Concatenate into HTML strings; `innerHTML` with raw user data |
| HTML **attribute** | Encode for attributes; prefer quoted attrs; boolean attrs without user data | Unquoted attributes; event handlers (`onclick=…`) with user data |
| **URL** (href/src) | Allowlist scheme (`https:`, maybe `mailto:`); encode query via URL APIs | `javascript:` / `data:` from users; string-glue URLs |
| **JavaScript** string in page | Pass data via `json.dumps` into safe bootstrap; avoid inline JS with user strings | Manually escape for JS with ad-hoc replace; nest HTML+JS without care |
| **JSON** response | Standard JSON serializer | Hand-rolled JSON with unescaped quotes/newlines |
| **CSS** | Avoid user data in style; if unavoidable, strict allowlist (e.g. color hex) | Raw user strings in `style` or CSS files |
| **SQL** | Bound parameters / ORM; allowlist for identifiers (sort columns) | `f"…{user}…"`, `"…" + user`, string `format` for values **or** identifiers |
| **NoSQL** | Typed operators; never splice user JSON as query operators (`$gt`, `$where`) | Merge request body directly into query object |
| **Shell** | `subprocess` argv list / no shell; allowlisted binaries | `shell=True` with user text; bash string interpolation |
| **LDAP** | LDAP-safe encoders / bind APIs | Raw filter concatenation |
| **Logs** | Structured fields; strip/encode CR/LF in messages | Unsanitized multiline user agents forging log lines |
| **CSV/export** | Prefix risky cells / library-safe CSV | Raw `=`/`+`/`-`/`@` cells into Excel without policy |

### Identifier vs value (SQL)

- **Values** (user names, dates, ids in `WHERE`): always **parameters**.
- **Identifiers** (column/table for sort): never parameterize like values in most drivers — use an **allowlist map** (`input-validation-patterns`).

## Good / Bad Examples

### HTML text (template / React)

**Good**

```tsx
// React escapes text children by default
function Bio({ name }: { name: string }) {
  return <p className="bio">Hello, {name}</p>;
}
```

```html
<!-- Server template with auto-escape ON -->
<p>Hello, {{ user.name }}</p>
```

**Bad**

```tsx
// XSS if name is "<img onerror=…>"
function Bio({ name }: { name: string }) {
  return <p dangerouslySetInnerHTML={{ __html: `Hello, ${name}` }} />;
}
```

```html
<p>Hello, {{ user.name | safe }}</p>
<!-- or autoescape off -->
```

### HTML attribute

**Good**

```html
<!-- Framework encodes attribute values; keep quotes -->
<input value="{{ user.nickname }}" />
```

```ts
a.href = urlFromAllowlist; // scheme/host checked first
a.setAttribute("title", userTitle); // DOM API, not string HTML
```

**Bad**

```html
<img src={{ user.avatarUrl }}>
<!-- unquoted + javascript: URL risk -->
<div class={{ user.className }} onclick="{{ user.handler }}">
```

### Safe data bootstrap into JS

**Good**

```html
<script id="boot" type="application/json">{{ user_json_serialized }}</script>
<script>
  const boot = JSON.parse(document.getElementById("boot").textContent);
</script>
```

(where `user_json_serialized` is from a standard JSON encoder, then HTML-encoded
if embedded in HTML text context per framework rules)

**Bad**

```html
<script>
  const name = "{{ user.name }}"; // breaks out with "; alert(1);//
</script>
```

### URL construction

**Good**

```ts
const url = new URL("https://app.example.com/search");
url.searchParams.set("q", userQuery); // correct percent-encoding
// Redirect target:
if (!ALLOWED_HOSTS.has(parsed.host) || parsed.protocol !== "https:") {
  throw new ValidationError("invalid_redirect");
}
```

**Bad**

```ts
res.redirect(req.query.next); // open redirect + scheme injection
const href = "/search?q=" + userQuery; // broken encoding, easier attribute breakouts
```

### SQL parameters

**Good**

```ts
await db.query(
  "SELECT id, email FROM users WHERE email = $1 AND tenant_id = $2",
  [email, tenantId],
);
```

```python
session.execute(
    select(User).where(User.email == email, User.tenant_id == tenant_id)
)
```

**Bad**

```ts
await db.query(`SELECT * FROM users WHERE email = '${email}'`);
```

```python
cursor.execute("SELECT * FROM users WHERE email = '%s'" % email)
```

### NoSQL operator injection

**Good**

```ts
const email = z.string().email().parse(req.body.email);
await users.findOne({ email, tenantId }); // plain equality fields only
```

**Bad**

```ts
await users.findOne({ email: req.body.email });
// body: {"email": {"$ne": null}} → unexpected match
```

### Shell

**Good**

```python
subprocess.run(["/usr/bin/convert", input_path, output_path], check=True)
```

**Bad**

```python
os.system(f"convert {user_filename} out.png")
```

### Rich text (when product requires HTML)

**Good**

```ts
import DOMPurify from "dompurify";

const clean = DOMPurify.sanitize(userHtml, {
  ALLOWED_TAGS: ["b", "i", "em", "strong", "a", "p", "ul", "ol", "li", "code"],
  ALLOWED_ATTR: ["href", "title", "rel"],
  ALLOW_DATA_ATTR: false,
});
// Also enforce rel="noopener noreferrer" on anchors; CSP in depth
```

**Bad**

```ts
el.innerHTML = userHtml; // full XSS surface
// or regex-only strip of "<script>"
```

### Logs

**Good**

```ts
logger.info("login_failed", { userId, reason: "bad_password" });
// user-controlled strings as structured fields, not format strings
```

**Bad**

```ts
logger.info(`login failed for ${username}\nINFO admin became root`);
```

## Anti-Patterns

- Global “disable auto-escape” for convenience
- Blacklist filters (`replace("<script>", "")`) as XSS defense
- Storing HTML-escaped data as the only form in the database
- Encoding for the wrong context (HTML-escape then put into JS or SQL)
- Parameterizing SQL values but concatenating `ORDER BY` / column names from input
- `dangerouslySetInnerHTML` / `v-html` / `[innerHTML]` without sanitizer + policy
- Building JSON, XML, or multipart bodies with string templates
- Trusting client-side encoding only
- Using `eval`, `new Function`, or dynamic `setTimeout(string)` on user data
- Assuming validation of “no `<` character” equals safe HTML attribute/URL use
- Weakening CSP (`unsafe-inline`) instead of fixing encoding sinks

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Context encoding, safe sinks, XSS/SQLi prevention in code, 输出编码 | **This skill** | — |
| Inbound schemas, allowlists, bounds | `input-validation-patterns` | this for every sink that still emits data |
| Implementing encode helpers, templates, tests | `code-quality-standards` | **always apply** on code changes |
| Authorized XSS testing / payload methodology | `xss-cross-site-scripting` | this when **fixing** sinks |
| Authorized SQLi testing methodology | `sqli-sql-injection` | this when **fixing** queries |
| Injection class unknown (assessment) | `injection-checking` | this for defensive encode map |
| CSP bypass assessment | `content-security-policy-bypass` | this for app encoding |
| CSV formula / export injection assessment | `csv-formula-injection` | this for defensive export encoding |
| Log field design and redaction style | `logging-message-style` | this for CR/LF and injection into logs |
| Secrets never in logs | `secrets-management-hygiene` | `logging-message-style` |

### Routing to `code-quality-standards`

Keep **this skill primary** for *which* encoding or safe API applies per sink.
Always apply **`code-quality-standards`** when implementing or reviewing code:

- Prefer clear interfaces that cannot accept “raw HTML” without an explicit type
  or reviewed sanitizer boundary
- No silent catch of encoding/sanitizer failures on security-critical renders
- Tests include breakthrough strings per context (`<`, quotes, newlines, `$ne`, `';`)
- Avoid `any` flowing into templates or query builders
- Document intentional raw-HTML paths with owners and sanitizer config
- Regression tests when fixing XSS/SQLi class bugs

### Routing to `input-validation-patterns`

Use **`input-validation-patterns`** for parse/allowlist/schema at ingress.
Use **this skill** wherever data leaves toward a parser (browser, DB, shell).
Features that accept text and render or query it need **both**.

### Routing to assessment skills

- **`xss-cross-site-scripting` / `sqli-sql-injection`:** primary for authorized
  offensive methodology and impact proof.
- **This skill:** primary when writing or fixing product code to eliminate sinks.

## Checklist

- [ ] Repo template auto-escape, sanitizer, ORM/query, and CSP settings identified
- [ ] Sinks inventoried: HTML, attr, URL, JS bootstrap, SQL/NoSQL, shell, CSS, logs, exports
- [ ] Untrusted data sources traced into each sink
- [ ] Safe APIs preferred (text bindings, bound parameters, argv lists, JSON serializers)
- [ ] Context-correct encoders used only where safe APIs are unavailable
- [ ] No global auto-escape off; raw HTML paths explicit, sanitized, and reviewed
- [ ] URLs: scheme/host allowlist + URL/query APIs for encoding
- [ ] SQL/NoSQL: parameters for values; allowlists for identifiers/operators
- [ ] Rich text: tag/attr allowlist sanitizer + CSP defense in depth
- [ ] Domain models store raw data; encode at output boundaries
- [ ] Logs structured; CR/LF and format-string injection considered
- [ ] CSV/export formula-safe handling when Excel consumers exist
- [ ] Tests cover per-context breakthrough payloads; fixes locked with regression tests
- [ ] `input-validation-patterns` applied at ingress for the same feature
- [ ] `code-quality-standards` applied for implementation quality and verification
- [ ] Assessment-depth testing handed to XSS/SQLi skills when engagement requires it

## Rules

- Encode for the **actual** consumer context; never one generic “escape all” for every sink.
- Prefer APIs that make injection unrepresentable over manual string munging.
- Validate input and encode output — neither replaces the other.
- Parameterize queries; allowlist identifiers; never shell-interpolate untrusted text.
- Repo frameworks and ORMs win; this skill supplies the context map and review bar.
- Defensive engineering and authorized hardening only.
---

# Note

This skill owns **context-aware output encoding and safe sink selection**.
Pair with `input-validation-patterns` at ingress, `code-quality-standards` on
implementation, and XSS/SQLi assessment skills when authorized testing depth is
required rather than product-code defense.
