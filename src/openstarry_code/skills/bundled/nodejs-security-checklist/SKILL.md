---
name: nodejs-security-checklist
description: >
  Node.js security checklist for org-owned services: Express/Fastify/Nest
  defaults, validation, injection sinks, sessions/JWT cookies, secrets,
  dependencies, and HTTP hardening. Use when reviewing Node/Express APIs,
  npm risk, helmet/CORS, or release hardening — authorized only.
---

# Node.js Security Checklist

Harden **Node.js** HTTP services and workers you own or are authorized to
assess. Runtime and framework controls — not a general exploit catalog.

## Use When

- Reviewing Node apps (`package.json`, Express/Fastify/Koa/Nest/Hono)
- Middleware: helmet, CORS, rate limits, sessions, JWT cookies
- Prototype pollution, ReDoS, path traversal, SQLi/NoSQLi, XSS, CMDi
- npm/yarn/pnpm lockfile risk; `child_process` / `vm` / `eval`
- Mentions: Node.js security, Express security, helmet, npm audit, Node 安全

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Unknown injection class deep-dive | `injection-checking` → class skill |
| Secret vault/rotation only | `secrets-management-hygiene` |
| Code reliability/tests baseline | `code-quality-standards` |
| Prototype pollution deep methodology | `prototype-pollution` |
| Image packaging only | `dockerfile-best-practices` |

## Repo Config First

Repo settings **outrank** generic defaults.

1. Runtime pin: `.nvmrc` / `engines` / Volta — match CI and prod
2. Framework layout (Express modules, Nest guards/pipes) — do not fork auth style
3. Config: `dotenv`/envalid/platform secrets; `.env.example` placeholders only
4. Validation stack already in use (Zod, Joi, class-validator, TypeBox)
5. Neighbor route middleware order (auth before handler)
6. Package manager + committed lockfile; private registry auth pattern
7. CI: `npm audit`, Socket/Snyk, ESLint security — extend gates
8. Edge TLS vs app cookies; set `trust proxy` only for known hop count

Follow the repo on conflicts; surface `eval`, open CORS+credentials, committed prod `.env`.

## Workflow

1. **Inventory** — routes, webhooks, uploads, SSR, WebSockets, workers, debug/metrics exposure.
2. **HTTP baseline** — `trust proxy`, helmet (or edge headers), CORS allowlist, body size limits.
3. **AuthN/session** — cookie flags; production session store (not MemoryStore multi-instance); JWT alg allowlist; logout/revoke.
4. **AuthZ** — object-level checks on every id; isolate admin routers.
5. **Validation** — schema at boundary; strip unknown keys; cap pagination.
6. **Dangerous APIs** — SQL/NoSQL concat, `exec(user)`, path join escape, SSR XSS, `eval`/`Function`/`vm`, unsafe YAML → `injection-checking` when class unclear.
7. **Prototype pollution** — deep merge of `req.body`; prefer null-prototype maps / safe merge.
8. **Deps + verify** — lockfile, audit High/Critical; dual-account authZ retest; `code-quality-standards` on fixes.

## Good / Bad

**Good**

```js
const data = z.object({ name: z.string().max(100) }).parse(req.body);
await pool.query("SELECT * FROM users WHERE email = $1", [email]);
app.use(helmet());
app.use(cors({ origin: ["https://app.example"], credentials: true }));
```

**Bad**

```js
await db.user.update({ where: { id: req.params.id }, data: req.body });
Object.assign(user, req.body);
await pool.query(`SELECT * FROM users WHERE email = '${email}'`);
exec(`zip -r out.zip ${userDir}`);
app.use(cors({ origin: true, credentials: true }));
const API_KEY = "sk_live_…";  // or committed .env prod secrets
eval(req.body.expr);
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Node/Express/Nest checklist, helmet, npm hygiene | **This skill** | — |
| Implementation quality, tests on fixes | `code-quality-standards` | this |
| API keys, `.env`, vault, rotation | `secrets-management-hygiene` | this for Node load paths |
| Unclear / multi-class injection | `injection-checking` | this for Node sinks |
| SQLi/XSS/SSRF/CMDi/prototype deep dive | matching class skill | this |
| JWT/API auth methodology | `api-auth-and-jwt-abuse` | this for cookie flags |
| Container packaging | `dockerfile-best-practices` | this |
| SBOM / supply-chain gates | `sbom-and-supply-chain` | this |

### Required helpers

- **`code-quality-standards`** — every production code change.
- **`secrets-management-hygiene`** — env keys, registry tokens, session secrets.
- **`injection-checking`** — unknown or multi-type sinks.

## Checklist

- [ ] Node major pinned; lockfile committed; High/Critical deps triaged
- [ ] No secrets in source/images; samples are placeholders
- [ ] `trust proxy` correct; TLS and secure cookies aligned
- [ ] Security headers; CORS allowlisted; body/upload limits; auth rate limits
- [ ] Schema validation + unknown-key strip on writes
- [ ] Object-level authZ; admin routes isolated
- [ ] No string-built SQL/NoSQL/shell; paths jailed to root
- [ ] No `eval`/unsafe `vm`/dynamic `require` on user input
- [ ] Session store prod-safe; JWT algorithms/secrets hardened
- [ ] Prod errors do not leak stacks
- [ ] Fixes: `code-quality-standards`; secrets: `secrets-management-hygiene`; deep inject: `injection-checking`

## Rules

Authorized targets only. Prefer config/code evidence; cite versions for CVEs. Fail closed on missing secrets and authZ. Redact tokens, cookies, and PII.
