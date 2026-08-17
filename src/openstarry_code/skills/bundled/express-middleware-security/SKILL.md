---
name: express-middleware-security
description: >
  Secure Express middleware stacks: helmet, CORS, rate limits, body limits,
  trust proxy, auth guards, and correct middleware order. Use when Express
  security, helmet, express-rate-limit, cors package, cookie/session middleware,
  JWT auth middleware, or hardening Node HTTP APIs with Express/Connect.
---

# Express Middleware Security

Defensive middleware for **Express** apps you own or may harden. Prefer a small
ordered stack and shared auth/validation over checks inside every handler.

## Use When

| Situation | Direction |
| --- | --- |
| Helmet, CORS, rate limit, body limits | **This skill** (primary) |
| Auth/JWT/session guards, role checks | This skill |
| `trust proxy`, cookie flags, CSRF with cookies | This skill |
| Request validation (Joi/Zod/express-validator) | This + `input-validation-patterns` |
| JWT algorithm/claims abuse assessment | `api-auth-and-jwt-abuse` |
| Errors, tests, reliability baseline | `code-quality-standards` |

Triggers: Express security, helmet, express-rate-limit, cors middleware,
trust proxy, cookie-parser, csrf-csrf, express-jwt, middleware order.

Not primary for FastAPI (`fastapi-security-patterns`), injection class testing,
or unauthorized third-party attacks.

## Repo Config First

Repo middleware and config **outrank** defaults here.

1. App entry — full `app.use` order in `createApp()` / `app.js` / `server.ts`
2. Env: `CORS_ORIGIN`, `SESSION_SECRET`, `TRUST_PROXY`, rate-limit store
3. Auth helpers: passport, `requireAuth`, JWT verify, session store
4. Validation stack already on routers (Zod/Joi/express-validator)
5. Existing Helmet/CORS — extend; avoid double conflicting headers
6. Reverse-proxy hop count — set `trust proxy` only that far
7. Final error middleware `(err, req, res, next)`
8. Neighbor mounts (`/api/v1`) and auth patterns

Surface: body parser after auth needing body; reflective CORS + credentials;
wrong `trust proxy` breaking rate limits or secure cookies.

## Workflow

1. **Map mounts** — public / authenticated / admin; cookie vs Bearer vs API key.
2. **Order:** `x-powered-by` off → `trust proxy` → Helmet → CORS → rate limit
   (stricter on `/auth`) → body parsers **with limits** → cookies/session →
   CSRF (browser cookies) → auth → validation → handlers → 404 → error handler last.
3. **Authn then authz** — verify session/JWT; set `req.user`; role middleware;
   never trust client `X-User-Id` alone.
4. **Validate at boundary** — schema middleware; allowlist fields; cap JSON size
   (`input-validation-patterns`).
5. **CORS** — explicit origin allowlist; credentials only with concrete origins.
6. **Tokens/sessions** — pin JWT algs; short expiry; rotate SID on login;
   HttpOnly/Secure/SameSite. Deep JWT threats → `api-auth-and-jwt-abuse`.
7. **Rate-limit abuse paths** — login, reset, OTP, costly GETs; key user+IP;
   shared store when multi-instance.
8. **Verify** — 401/403, CORS preflight, oversize 413, 429, no prod stacks.

## Good / Bad Examples

**Good — ordered stack:**

```js
const app = express();
app.disable("x-powered-by");
app.set("trust proxy", 1);
app.use(helmet());
app.use(cors({ origin: process.env.CORS_ORIGINS.split(","), credentials: true }));
app.use("/auth", rateLimit({ windowMs: 15 * 60_000, max: 20 }));
app.use(express.json({ limit: "100kb" }));
app.use(cookieParser());
app.use("/api", requireAuth, apiRouter);
app.use(errorHandler);
```

**Bad:** `cors({ origin: true, credentials: true })` + huge JSON limit + admin
route with no auth middleware.

**Good — guards:**

```js
function requireAuth(req, res, next) {
  try {
    req.user = verifyJwt(bearer(req), { algorithms: ["RS256"] });
    return next();
  } catch {
    return res.status(401).json({ error: "unauthorized" });
  }
}
function requireRole(...roles) {
  return (req, res, next) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ error: "forbidden" });
    }
    next();
  };
}
```

**Bad:** `jwt.decode` only; accept any header `alg`.

**Good:** Zod/Joi middleware → `req.validated` only. **Bad:** raw `req.body` in SQL/shell.

## Routing

| Need | Skill |
| --- | --- |
| Express order, helmet, CORS, limits, guards | **This skill** (primary) |
| Allowlists, schemas, fail-closed parsing | `input-validation-patterns` |
| JWT alg/claims abuse, Bearer flaws | `api-auth-and-jwt-abuse` |
| Implementation quality, errors, tests | `code-quality-standards` (always) |
| FastAPI/Starlette | `fastapi-security-patterns` |
| CSRF / session fixation | `csrf-cross-site-request-forgery`, `session-fixation-management` |
| Rate-limit bypass assessment | `rate-limit-bypass-testing` |

Keep **this skill primary** for Express pipelines. Always apply
**`code-quality-standards`**; **`input-validation-patterns`** for schemas;
**`api-auth-and-jwt-abuse`** when token forgery or authN design is in scope.

## Checklist

- [ ] Full `app.use` order documented; error handler last
- [ ] `x-powered-by` off; Helmet (or equivalent) appropriate
- [ ] `trust proxy` matches real hop count only
- [ ] CORS origins explicit; no reflective origin + credentials
- [ ] Body size limits set; multipart capped separately
- [ ] Rate limits on login/reset/OTP and costly routes
- [ ] Auth on protected mounts; roles where required
- [ ] JWT verify with pinned algorithms; secrets from env/vault
- [ ] Cookie sessions: Secure/HttpOnly/SameSite; CSRF if browser cookies
- [ ] Validation before handlers; allowlisted fields only
- [ ] Prod errors hide stacks; logs omit tokens/passwords
- [ ] Tests: 401/403/400/413/429 and CORS preflight
- [ ] Helpers applied: `input-validation-patterns`, `api-auth-and-jwt-abuse`, `code-quality-standards`
