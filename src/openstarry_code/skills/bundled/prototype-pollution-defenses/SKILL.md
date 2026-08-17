---
name: prototype-pollution-defenses
description: >
  Harden JavaScript and TypeScript applications against prototype pollution:
  safe merge/clone, key denylists and allowlists, null-prototype maps, parser
  settings, freeze/seal of config, and regression tests. Use when fixing or
  reviewing deep-merge, defaults, query parsers, lodash/jQuery extend, or
  Object.assign recursion that may accept untrusted objects in owned apps.
---

# Prototype Pollution Defenses

Design and verify **defenses** that stop untrusted keys from polluting
`Object.prototype` (or app defaults via inherited properties). Defensive
hardening and remediation verification only.

## Scope And Authorization

- **In scope:** Org-owned Node/browser/Electron apps where user JSON, nested
  query keys, or message payloads are merged, cloned, or defaulted.
- **Out of scope:** Offensive gadget chains, unauthorized scanning, cross-tenant
  pollution on shared SaaS without approval.
- Prefer proving **controls** (canaries do not stick) over demonstrating RCE.
- Offensive discovery/proof → `prototype-pollution`. This skill owns **fix design,
  implementation, and retest**. Pair code changes with `code-quality-standards`.

## When To Use

- Implementing or reviewing safe `deepMerge` / `defaultsDeep` / `extend` helpers
- Hardening parsers that expand bracket/dotted keys (`qs`, body parsers, URL hash)
- Replacing plain-object dictionaries with `Map` or `Object.create(null)`
- Post-finding remediation after a prototype pollution report
- Mentions: `__proto__`, `constructor.prototype`, lodash/jQuery merge, polluted defaults

Do **not** use as primary:

| Need | Skill instead |
| --- | --- |
| Offensive pollution probes / impact proofs | `prototype-pollution` |
| Generic injection family triage | `injection-checking` |
| Mass assignment of known keys (not prototype) | domain authZ / API skills |
| Implementation quality baseline while coding | `code-quality-standards` |

## Why Pollution Defenses Matter

| Risk path | Defense goal |
| --- | --- |
| Recursive assign of user keys | Never write `__proto__` / `constructor` / `prototype` |
| Query/JSON parsers | Do not expand proto keys into merge sources |
| Config/defaults | No shared mutable defaults; no inherit-based flags |
| AuthZ / shared workers | Own-property reads only; one polluted prototype hits all tenants |

## Workflow

### 1. Inventory sinks and trust boundaries

1. List inputs that become objects: JSON bodies, nested form/query params, YAML
   uploads, WebSocket/postMessage payloads, `JSON.parse` of user strings.
2. Grep merge/clone sites: `merge`, `extend`, `defaultsDeep`, recursive
   `Object.assign`, `for (const k in src) dst[k] = …`.
3. Note libraries/versions (`lodash`, `qs`, `hoek`, jQuery, custom utils).
4. Flag singleton config objects that receive merges (highest blast radius).

### 2. Prefer safe data structures

1. User-keyed maps → `Map` or `Object.create(null)` (no prototype chain).
2. Never use plain `{}` as a multi-tenant or untrusted-key store.
3. Freeze critical config after load (`Object.freeze`; nested where needed).
4. Avoid mutating shared default options; clone with a **safe** copy that skips
   proto keys.

### 3. Harden merge, clone, and assign

Implement/review with `code-quality-standards`:

1. **Allowlist** expected keys at API boundaries when the shape is known.
2. If deep-merge is required, **deny** at every level: `__proto__`, `constructor`,
   `prototype` (check key strings before property access).
3. Assign only after `Object.hasOwn(src, k)`; do not walk the source prototype.
4. Prefer prototype-safe utilities over ad hoc recursion.
5. Do not merge untrusted input into process-global or module-level config.
6. For shallow needs, prefer explicit field pick over recursive merge.

### 4. Parser and edge controls

| Control | Intent |
| --- | --- |
| `qs` / query: disallow prototypes | Block `?__proto__[x]=` expansion |
| Strip/reject `__proto__` in JSON at edge | Defense in depth before merge |
| Disable nested-key expansion if unused | Shrink attack surface |
| Content-type and size limits | Reduce parser abuse |
| Schema validation (Zod, JSON Schema, …) | Drop unknown keys by default |

### 5. Safe property reads (consumers)

1. AuthZ/flags: `Object.hasOwn(obj, 'role')` or Map lookup — never rely on
   bare `obj.isAdmin` if inheritance is possible.
2. Prefer explicit code defaults over “missing key inherits from prototype.”
3. Template/HTTP client options: build from allowlisted fields only.

### 6. Verify defenses (authorized)

1. Fixtures with `__proto__` and `constructor.prototype` canaries; assert
   `({}).canary === undefined` and no stick on `Object.prototype`.
2. Cover nested/array shapes your merge actually walks.
3. Retest the original finding path from `prototype-pollution` reports.
4. CI: ban unbounded recursive assign without key filters; pin/patch unsafe deps.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Defend/remediate prototype pollution in JS/TS | **This skill** | `code-quality-standards` |
| Authorized offensive proof / gadget impact | `prototype-pollution` | this skill for fixes |
| Injection class unclear | `injection-checking` | then pollution skills |
| Implement safe merge/parser/tests | `code-quality-standards` | this skill for pollution rules |
| DOM XSS via polluted library options | `xss-cross-site-scripting` | this + `prototype-pollution` |

- **`prototype-pollution`:** find/prove pollution; remediate and retest here.
- **`code-quality-standards`:** merge helpers, parsers, validation, immutability, tests.
  Do not open `skill-router`; stay on the routes above.

## Output Checklist

- [ ] Sinks inventoried (merge/parser/client) and trust boundary marked
- [ ] Key policy: allowlist and/or deny `__proto__` / `constructor` / `prototype`
- [ ] Dictionaries use `Map` or null-prototype objects where appropriate
- [ ] No untrusted deep-merge into global/singleton config
- [ ] Consumers use `Object.hasOwn` (or Map) for security-sensitive flags
- [ ] Parser settings block prototype keys; schema drops unknown keys if used
- [ ] Regression tests: canary does not stick on `Object.prototype` or `{}`
- [ ] Dependency versions noted; unsafe merge libs patched or wrapped
- [ ] `code-quality-standards` applied to code changes
- [ ] Residual risk and retest evidence documented (redact secrets)

## Rules

- Defense in depth: edge validation **and** safe merge **and** safe reads.
- Prefer allowlists and null-prototype stores over deny-lists alone.
- Never “fix” production by mutating `Object.prototype` in shared processes.
- Authorized hardening only; pair findings with retests, not gadget packs.