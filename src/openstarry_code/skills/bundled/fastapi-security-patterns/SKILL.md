---
name: fastapi-security-patterns
description: >
  Secure FastAPI apps: Depends-based auth, CORS/TrustedHost, HTTPS, security
  headers, Pydantic boundaries, JWT/OAuth2 schemes, and safe middleware order.
  Use when FastAPI security, FastAPI CORS, Depends auth, OAuth2PasswordBearer,
  TrustedHostMiddleware, APIRouter guards, or hardening Starlette/FastAPI APIs.
---

# FastAPI Security Patterns

Defensive security for **FastAPI / Starlette** you own or may harden. Prefer
`Depends`, Pydantic models, and existing middleware over ad-hoc route checks.

## Use When

| Situation | Direction |
| --- | --- |
| FastAPI auth via `Depends`, OAuth2/JWT Bearer, API keys | **This skill** (primary) |
| CORS, TrustedHost, HTTPS redirect, proxy headers | This skill |
| Router guards, role/scope checks, OpenAPI exposure | This skill |
| Body/query/path validation with Pydantic | This + `input-validation-patterns` |
| JWT algorithm/claims abuse assessment | `api-auth-and-jwt-abuse` |
| Errors, tests, reliability baseline | `code-quality-standards` |

Triggers: FastAPI security, Depends auth, OAuth2PasswordBearer, CORSMiddleware,
TrustedHostMiddleware, HTTPBearer, Starlette middleware.

Not primary for Express (`express-middleware-security`), injection class testing,
or unauthorized third-party attacks.

## Repo Config First

Repo settings **outrank** defaults here.

1. App factory (`main.py` / `create_app()`) — middleware order
2. Settings/env: `SECRET_KEY`, `CORS_ORIGINS`, `ALLOWED_HOSTS`
3. Auth module: `get_current_user`, JWT helpers, session store
4. Routers: `APIRouter(dependencies=[...])`, path-level `Depends`
5. CORS / proxy: `CORSMiddleware`, trusted proxy hop config
6. OpenAPI: prod exposure of `/docs`, `/redoc`, `/openapi.json`
7. Neighbor endpoints: copy mature auth + error patterns
8. Body limits/timeouts at uvicorn/gunicorn/proxy

Surface conflicts: auth skipped on some routers, `allow_origins=["*"]` with
credentials, or JWT verify with unpinned algorithms.

## Workflow

1. **Map surface** — public vs authenticated routers; cookie vs Bearer; docs URLs.
2. **Trust boundaries** — path/query/body/header/cookie; uploads; WebSocket; tasks.
3. **Middleware order (outer → inner)** — proxy/TrustedHost → HTTPS redirect →
   CORS → session (if any) → routes. Prefer **auth in `Depends`**, not opaque global middleware.
4. **Authenticate once, authorize always** — Bearer/OAuth2/cookie via `Depends`;
   load user server-side; composable `require_roles(...)`; never trust client `X-User-Id` alone.
5. **Validate with Pydantic** — `Field` bounds; `extra="forbid"` when policy requires;
   see `input-validation-patterns`.
6. **CORS / hosts** — explicit origin allowlist; credentials only with concrete origins;
   `TrustedHostMiddleware` for known hosts.
7. **Token hygiene** — pin algorithms; short `exp`; validate `iss`/`aud` when used;
   secrets in env/vault. Deep token abuse → `api-auth-and-jwt-abuse`.
8. **Errors / docs** — no stacks in prod responses; protect or disable OpenAPI UIs in prod.
9. **Verify** — 401/403, expired JWT, oversize body, CORS preflight, CSRF if cookies.

## Good / Bad Examples

**Good — Depends auth + router guard:**

```python
async def get_current_user(
    cred: HTTPAuthorizationCredentials = Depends(HTTPBearer()),
) -> User:
    user = await users_from_jwt(cred.credentials)  # pinned alg, verify exp
    if not user:
        raise HTTPException(status_code=401, detail="unauthorized")
    return user

def require_roles(*roles: str):
    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail="forbidden")
        return user
    return _dep

router = APIRouter(prefix="/admin", dependencies=[Depends(require_roles("admin"))])
```

**Bad:** optional header ignored → still returns admin data; no signature verify.

**Good — CORS:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # concrete https origins
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Bad:** `allow_origins=["*"]` + `allow_credentials=True`; reflecting any `Origin`.

**Good — strict model:** `ConfigDict(extra="forbid")` + `Field(min_length=..., max_length=...)`.

**Bad:** raw `await request.json()` dict driving SQL or shell strings.

## Routing

| Need | Skill |
| --- | --- |
| FastAPI Depends, CORS/hosts, OpenAPI exposure | **This skill** (primary) |
| Allowlists, schemas, fail-closed parsing | `input-validation-patterns` |
| JWT alg/claims abuse, Bearer flaws | `api-auth-and-jwt-abuse` |
| Implementation quality, errors, tests | `code-quality-standards` (always) |
| Express/Node middleware | `express-middleware-security` |
| Cookie CSRF / session fixation | `csrf-cross-site-request-forgery`, `session-fixation-management` |

Keep **this skill primary** for FastAPI wiring. Always apply
**`code-quality-standards`**; use **`input-validation-patterns`** for boundary
schemas; **`api-auth-and-jwt-abuse`** when tokens/JWKS/authN bypass are in scope.

## Checklist

- [ ] Middleware order and env allowlists inventoried
- [ ] Auth via `Depends`; no anonymous access on sensitive routers
- [ ] Authorization on every object/action (not only authentication)
- [ ] Pydantic bounds/enums; size limits aligned with proxy
- [ ] CORS origins explicit; no `*` + credentials
- [ ] Trusted hosts / HTTPS / proxy trust correct for deploy
- [ ] JWT secrets not hardcoded; algorithms pinned server-side
- [ ] Prod docs/OpenAPI exposure matches policy
- [ ] Errors omit stacks; cookie auth has Secure/HttpOnly/SameSite + CSRF if needed
- [ ] Tests: 401/403, expired token, invalid body, CORS preflight
- [ ] Routed helpers applied: `input-validation-patterns`, `api-auth-and-jwt-abuse`, `code-quality-standards`
