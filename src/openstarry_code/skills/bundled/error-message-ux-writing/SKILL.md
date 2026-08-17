---
name: error-message-ux-writing
description: >
  Write and review user-facing error messages that are actionable, free of
  secrets, and paired with stable machine codes. Use when error messages,
  错误文案, exception messages for users, API error payloads, toast/alert copy,
  form validation text, or when UX/review flags vague, leaky, or untranslatable
  errors. Complements code-quality-standards; does not replace logging style
  (see logging-message-style).
---

# Error Message UX Writing

Grounded in product UX and API hygiene: users need **what happened**, **what
to do next**, and a **stable code** for support; systems need codes for
metrics and i18n. Prefer clarity and safety over developer dump text.

## When To Use

- Drafting or rewriting messages shown in UI, mobile alerts, CLI stderr meant for humans, email/SMS failure notices, or API `message` / `detail` fields for clients.
- Designing error envelopes (`code`, `message`, `details`, `requestId`) for REST/gRPC/GraphQL.
- Reviewing exceptions that bubble to users (HTTP 4xx/5xx bodies, form validation, payment/auth failures).
- Chinese/English product copy: 错误文案, 提示语, 校验失败文案.
- **Not** for operator/debug logs → `logging-message-style`. **Not** for full error-handling architecture alone → `code-quality-standards` (this skill owns **user-visible wording and codes**).

## Repo Config First

1. Read product copy guides, design system error patterns, `AGENTS.md` / i18n locales (`en`, `zh-CN`, …), and API error schemas already in the repo.
2. Honor existing **error code catalogs** (enums, protobuf `ErrorCode`, OpenAPI examples). Extend the catalog; do not invent one-off free-text-only failures on a new path.
3. Match nearby tone: formal B2B vs consumer; second person (“you”) vs neutral; sentence case vs title case; trailing period policy.
4. Prefer the project’s i18n keys (`errors.payment.card_declined`) over hard-coded strings in components when the app is localized.
5. Repo rules outrank this skill unless they leak secrets, stack traces, or unstable strings used as API contracts — surface that conflict.

## Core Principles

| Principle | Practice |
| --- | --- |
| Actionable | Say what the user can do next (retry, fix field, contact support with code) |
| Specific, not scary | “Card declined — try another card or contact your bank” beats “Something went wrong” *and* “FATAL EXCEPTION” |
| No secrets | Never put tokens, passwords, connection strings, internal hosts, raw SQL, or full stack traces in user text |
| Stable machine code | `PAYMENT_CARD_DECLINED` / `err.payment.card_declined` for clients, metrics, and support — human text may change with i18n |
| Honest HTTP/status mapping | 401 vs 403 vs 404 vs 409 vs 422 vs 429 vs 5xx match the real class of failure |
| Safe on existence | Avoid user-enumeration oracles (“email not registered”) when auth policy forbids them |
| One primary problem | Lead with the main failure; secondary hints go in `details` or help links |
| Localizable | No concatenated fragments that break grammar; interpolate named placeholders |

**Audience split.** **User message** = safe, short, actionable. **Log / span** = structured, detailed, redacted (`logging-message-style`). **Support** = `requestId` / `traceId` + stable `code`. Never force one string to serve all three.

## Workflow

1. **Classify the failure.** Invalid input, authn, authz, not found, conflict, rate limit, dependency down, internal defect, maintenance. Pick status + stable code from the catalog (or add one with review).
2. **Separate layers.** Map domain error → transport status → user copy → log event. Do not `throw new Error(e.stack)` into the API body.
3. **Draft the user sentence.**
   - **What** failed (in product language, not class names).
   - **Why** only if it helps and is safe (optional).
   - **Next step** (required when the user can act).
4. **Attach machine fields.** `code` (stable), `requestId` / `traceId`, optional field path for forms (`field: "email"`), optional `retryAfter` for 429.
5. **Strip leaks.** Remove paths under server roots, SQL, JWT payloads, internal IPs, vendor raw errors, and exception type names that reveal stack/framework versions if policy requires.
6. **i18n.** Move copy to locale files; use ICU/named placeholders (`{filename}`, `{limit}`). Keep `code` language-neutral.
7. **Validation vs system errors.** Field errors: per-field, concrete rule (“Use 8+ characters”). System errors: calm, no blame, include support path + code.
8. **Verify.** Same code → same meaning across clients. Copy length OK for toast/mobile. Auth endpoints checked for enumeration. No secrets in fixtures/snapshots.

## Message Shape (recommended)

```text
[Product-language what] + [safe why if useful] + [next step].
+ code: STABLE_ERROR_CODE
+ requestId: opaque correlation id
```

API sketch (adapt to repo schema):

```json
{
  "code": "PAYMENT_CARD_DECLINED",
  "message": "Your card was declined. Try another card or contact your bank.",
  "requestId": "req_7f3a…",
  "details": [{ "field": "cardNumber", "issue": "declined" }]
}
```

## Good Vs Bad Examples

**Vague vs actionable**

```text
# bad
Something went wrong.
Error.
Failed.
请重试。   # retry what? why?

# good
We could not save your changes. Check your connection and try again.
If this keeps happening, contact support with code SAVE_FAILED (ref req_7f3a).
# good 中文
无法保存更改。请检查网络后重试；仍失败时请向支持提供错误码 SAVE_FAILED（编号 req_7f3a）。
```

**Secret / internal leak (bad) vs safe (good)**

```text
# bad
SQLSTATE[23505] duplicate key on users_email_key
Connection refused to redis://prod-redis-1.internal:6379
javax.crypto.BadPaddingException at com.example.AuthFilter:241
Invalid JWT: eyJhbGciOi... full token ...

# good
This email is already registered. Sign in or reset your password. (code EMAIL_IN_USE)
# or, if enumeration-sensitive policy:
Unable to complete sign-up. (code SIGNUP_REJECTED)  # same message for multiple causes
We could not complete authentication. Try again or reset your password. (code AUTH_FAILED)
```

**Exception for developers vs message for users**

```typescript
// bad: surface exception message to UI
catch (e) {
  return res.status(500).json({ message: String(e) });
}

// good: map to stable code + safe copy; log elsewhere
catch (e) {
  logger.error({ err: e, code: "INVOICE_CREATE_FAILED" }, "invoice create failed");
  return res.status(500).json({
    code: "INVOICE_CREATE_FAILED",
    message: "We could not create the invoice. Try again in a few minutes.",
    requestId: req.id,
  });
}
```

**Form validation**

```text
# bad
Invalid input.
Error in field 3.
格式错误

# good
Enter a valid work email (name@company.com).
Password must be at least 8 characters and include a number.
# good 中文
请输入有效的工作邮箱（name@company.com）。
密码至少 8 位且包含数字。
```

**Authorization honesty without oversharing**

```text
# bad (leaks existence of other tenants' resources)
Order 1842 belongs to another user.

# good
You do not have access to this order. (code ORDER_FORBIDDEN)
# or 404 if product hides existence:
Order not found. (code ORDER_NOT_FOUND)
```

## Anti-Patterns

- Using full exception messages, stack traces, or `e.toString()` as UX copy.
- Unstable prose as the only API contract (“message” changes break clients).
- Blame-y or sarcastic tone (“You broke it”, “Impossible input”).
- Concatenating untranslated fragments (`"不能" + fieldName + "为空"` without i18n).
- Different user text for the same `code`, or same text for contradictory codes.
- Putting recovery secrets in the message (temporary passwords, magic-link tokens).
- Humorous 500 pages that omit a support path or reference id.

## Routing

| Need | Skill |
| --- | --- |
| User-facing error copy, codes, 错误文案 | **This skill** (primary) |
| Structured logs, levels, PII redaction in logs | `logging-message-style` |
| Error handling design, retries, cleanup, tests | `code-quality-standards` (helper on production changes) |
| Naming of error types/codes in code | `naming-conventions-general` |
| API inventory / OpenAPI error schemas | `api-recon-and-docs` |
| Auth/JWT failures in assessment context | `api-auth-and-jwt-abuse` (security testing; not copywriting) |

Always apply **`code-quality-standards`** when the same change implements failure paths; messages must match real behavior and security boundaries.

## Output Checklist

- [ ] Repo error schema / code catalog / i18n pattern identified and followed
- [ ] Failure classified (input / auth / conflict / rate limit / dependency / internal)
- [ ] Stable `code` present; human `message` is not the only contract
- [ ] Message states what failed and a concrete next step when the user can act
- [ ] No secrets, stack traces, internal hosts, SQL, or raw tokens in user text
- [ ] Status/code mapping honest; enumeration policy respected on auth-sensitive flows
- [ ] Field-level validation errors are specific and attached to fields
- [ ] `requestId` / `traceId` available for support on non-trivial failures
- [ ] Copy localizable (named placeholders; no broken concatenation)
- [ ] Logs carry detail separately (`logging-message-style`); UX string stays safe
- [ ] Tests/snapshots assert codes (and critical copy) without locking flaky prose worldwide unless intentional

## Rules

- User-visible errors are part of the security and support surface — prefer boring clarity over cleverness.
- Prefer stable codes over fragile client matching on human prose.
- Never use one string for UX, logs, and support without redaction boundaries.
- Update i18n keys and code catalogs in the same change as new failure paths.
