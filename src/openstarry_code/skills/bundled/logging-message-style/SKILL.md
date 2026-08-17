---
name: logging-message-style
description: >
  Standards for application logs: structured fields, correct levels, stable
  message templates, and no PII or secrets. Use when logging style, 日志规范,
  log messages, logger design, slog/zap/logrus/structlog, or when reviews flag
  noisy, string-interpolated, or leaky logs. Complements code-quality-standards;
  does not own user-facing error copy (see error-message-ux-writing).
---

# Logging Message Style

Grounded in modern observability practice: **logs are events**, not print
debugging. Prefer structured fields, stable templates, correct severity, and
strict redaction so logs stay useful, cheap, and safe.

## When To Use

- Adding, editing, or reviewing application/service logs (stdlib `logging`, `slog`, zap, logrus, log4j/slf4j, Winston, pino, structlog, Serilog, etc.).
- Defining log message text, field names, or correlation (`requestId`, `traceId`, `spanId`).
- Fixing noisy logs, inconsistent levels, or incidents involving secret/PII leakage in logs.
- Chinese/English teams: 日志规范, 日志文案, 结构化日志.
- **Not** for end-user error strings → `error-message-ux-writing`. **Not** for full metrics/tracing architecture alone → use repo observability docs + `code-quality-standards` for implementation hygiene.

## Repo Config First

1. Read existing logging setup: logger wrapper, field naming (`snake_case` vs `camelCase`), required context (service, env, version), and sinks (JSON to stdout, OpenTelemetry, vendor agents).
2. Honor lint/security rules (`go-require-error-f`, ESLint no-sensitive-logging, custom semgrep) and `AGENTS.md` redaction policy.
3. Match nearby packages: message language (prefer English for logs unless repo mandates otherwise), whether errors use `err` field vs stringified, and default level per environment.
4. Prefer the project’s **canonical logger** over ad-hoc `console.log` / `print`. Do not introduce a second logging library without an explicit migration plan.
5. Repo rules outrank this skill unless they require logging secrets or unbounded payloads — surface that conflict.

## Core Principles

| Principle | Practice |
| --- | --- |
| Structured over string soup | Fields: `userId`, `orderId`, `durationMs`, `err` — not one interpolated novel |
| Stable message templates | Fixed event name/text; variables in fields (for metrics & alert grouping) |
| Correct level | `DEBUG` detail, `INFO` milestones, `WARN` recoverable, `ERROR` failed op, `FATAL`/`CRITICAL` process dying |
| No secrets / minimal PII | Tokens, passwords, cookies, auth headers, card data, session IDs — never; PII only if policy allows and is masked |
| Context once | Bind `requestId` / `traceId` on the logger/context; do not repeat in every message string |
| Cardinality control | Do not put unbounded unique strings into **message** text (UUIDs, full URLs with query) if that breaks grouping — put them in fields |
| Errors with cause | Log the error object/chain once at the boundary; avoid log-and-rethrow duplicates every layer |
| Cheap enough | Hot paths: avoid DEBUG in production defaults; sample or rate-limit repetitive WARN/ERROR |

**Audience.** Logs are for operators, on-call, and automated systems — not for end users. User copy and stable API codes belong in `error-message-ux-writing`.

## Levels (practical guide)

| Level | Use when | Examples |
| --- | --- | --- |
| DEBUG | Diagnostic detail off by default in prod | Parsed config keys (non-secret), cache miss reason |
| INFO | Expected, significant lifecycle | Server started, migration applied, request completed (if access logs) |
| WARN | Unexpected but handled / degraded | Retry exhausted once then recovered, fallback used, near quota |
| ERROR | Operation failed; needs attention if frequent | Handler failed after retries, dependency hard-fail returned to client |
| FATAL/CRITICAL | Process cannot continue | Cannot bind port, config missing required secret at boot |

Do not log user input validation failures at ERROR (usually DEBUG/INFO). Do not log routine successful requests at ERROR. Do not use ERROR for control flow that is expected (e.g. 401 on protected route without auth).

## Workflow

1. **Identify the event.** One event = one log line/object at the right boundary (e.g. “invoice create failed”), not every intermediate step unless debugging.
2. **Choose level** from the table; confirm env defaults (prod INFO+, dev DEBUG).
3. **Write a stable template.** Prefer constant message / event name: `"invoice_create_failed"` or `"invoice create failed"`. Put variables in structured fields only.
4. **Select fields.** Standard: `code` (domain/stable error code), `err`, `durationMs`, resource ids, peer service name. Align names with existing log schema.
5. **Redact.** Strip `Authorization`, cookies, `password`, `token`, `secret`, `private_key`, full request/response bodies by default. Mask remaining PII per policy (e.g. email → hash or local-part star).
6. **Correlate.** Propagate `requestId`/`traceId` via context; child loggers inherit. Include `code` that matches user-facing API errors when both exist.
7. **Guard volume.** Rate-limit loops; log summaries for bulk jobs (`processed=500 failed=3`) instead of per-item ERROR unless sampling for diagnosis.
8. **Verify.** Grep for f-string/interpolation of secrets; confirm JSON shape in a local run; ensure tests do not assert on volatile timestamps.

## Message Templates

**Prefer (structured)**

```text
event/message: constant phrase
fields: { "orderId": "...", "durationMs": 12, "err": "...", "code": "…" }
```

**Avoid (unstructured)**

```text
"Failed to create order " + orderId + " for user " + email + " with token " + jwt
```

Language sketches (adapt to project logger):

```python
# good — structlog / stdlib style
logger.error(
    "invoice_create_failed",
    code="INVOICE_CREATE_FAILED",
    invoice_id=invoice_id,
    err=str(err),  # or exc_info / exception field per repo
)

# bad
logger.error(f"invoice {invoice_id} failed for {user.email} password={password}: {err!r}")
```

```go
// good — slog
slog.Error("invoice create failed",
    "code", "INVOICE_CREATE_FAILED",
    "invoiceId", id,
    "err", err,
)

// bad
log.Printf("invoice %s failed: %+v", id, err) // unstructured; may dump sensitive structs
```

```typescript
// good — pino
req.log.error({ err, code: "INVOICE_CREATE_FAILED", invoiceId }, "invoice create failed");

// bad
console.log("invoice create failed " + JSON.stringify(req.body));
```

## Good Vs Bad Examples

**Interpolation vs fields**

```text
# bad — unique message per id breaks aggregation
"User 55a1-… failed checkout with total 19.99"

# good
message: "checkout failed"
fields: { "userId": "55a1-…", "totalCents": 1999, "code": "CHECKOUT_FAILED" }
```

**Level misuse**

```text
# bad
ERROR: invalid email format on signup form
ERROR: health check OK
INFO: panic: nil pointer  # should be ERROR/FATAL with stack handling

# good
INFO/DEBUG: signup validation rejected (code=VALIDATION_EMAIL)
DEBUG: health check ok  (or metrics only)
ERROR: handler panic recovered (err=..., stack=redacted or truncated per policy)
```

**Secrets and PII**

```text
# bad
Authorization: Bearer eyJhbG…
cookie: session=…
payload: {"cardNumber":"4111…","cvv":"123"}
password=hunter2
raw body: <full webhook with SSN>

# good
authorization: "[redacted]"
sessionId: "[redacted]"  # or omit
cardLast4: "1111"        # only if required and allowed
# omit password entirely
webhook: { "eventId": "evt_…", "type": "payment.updated" }  # allowlisted fields only
```

**Log-and-rethrow spam**

```java
// bad: ERROR at every layer for one failure
catch (Exception e) {
  log.error("failed in repo", e);
  throw e;
}
// ... again in service, again in controller

// good: add context without duplicate ERROR, or log once at boundary
catch (Exception e) {
  throw new InvoiceException("INVOICE_CREATE_FAILED", e);
}
// controller/middleware:
log.error("invoice create failed", kv("code", code), kv("err", e));
```

**Access / audit logs**

```text
# good: structured access line or dedicated audit event
message: "http_request"
fields: method, path (no raw query secrets), status, durationMs, requestId, userId (if authenticated policy allows)

# bad: dump of all headers and body at INFO for every request
```

## Anti-Patterns

- `print` / `console.log` / `Debug.WriteLine` in production paths.
- Dynamic **message** strings that embed ids, emails, or URLs as the only structure.
- Logging entire `request`/`config` objects without an allowlist.
- Catch blocks that log at ERROR then return 200 success with no signal elsewhere.
- Using WARN/ERROR for expected traffic (failed login without rate signal may be INFO + metrics).
- Different field names for the same concept (`user_id` vs `userId` vs `uid`) in one service.
- Synchronous expensive serialization of huge payloads on the hot path.

## Routing

| Need | Skill |
| --- | --- |
| Log levels, structure, templates, redaction, 日志规范 | **This skill** (primary) |
| User-facing errors / API message + stable codes | `error-message-ux-writing` |
| Error handling, resources, security, tests | `code-quality-standards` (helper on production changes) |
| Commenting non-obvious log/redaction decisions | `comment-writing-standards` |
| Naming field keys / event names | `naming-conventions-general` |
| CRLF / log injection into sinks | `crlf-injection` (security testing angle) |

Always apply **`code-quality-standards`** when the same change implements behavior; logging must not swallow errors without intentional handling, and must not leak sensitive data.

## Output Checklist

- [ ] Uses repo canonical logger and field naming schema
- [ ] Message/event template is stable; variables live in structured fields
- [ ] Level matches severity guide; no ERROR for routine validation
- [ ] No secrets (tokens, passwords, cookies, auth headers, keys) in messages or fields
- [ ] PII minimized/masked per policy; bodies not logged by default
- [ ] Correlation ids bound on context/logger (`requestId` / `traceId`)
- [ ] Domain `code` aligned with user-facing errors when applicable
- [ ] No duplicate ERROR on every layer for a single failure (boundary logging)
- [ ] Hot paths not flooded; bulk operations log summaries
- [ ] Safe for aggregation (controlled cardinality on message text)
- [ ] Tests avoid brittle full-string matches on timestamps/hostnames

## Rules

- Prefer one structured event at the correct boundary over a trail of narrative prints.
- Never log credentials “temporarily” — temporary becomes permanent in retention.
- For one-off incident detail, use sampled DEBUG or a short-lived flag — not a permanent INFO dump.
- Keep log message language consistent (English recommended) so on-call can search one vocabulary.
- Metrics and traces complement logs; do not replace counters with high-volume INFO lines.
- Structure, levels, and redaction are the contract with operators — not optional polish.
