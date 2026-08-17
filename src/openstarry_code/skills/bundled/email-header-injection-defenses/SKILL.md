---
name: email-header-injection-defenses
description: >
  Defend mail-sending paths against CRLF / email header injection by rejecting
  control characters, using structured mail APIs, and never concatenating
  untrusted data into raw SMTP or MIME headers. Use when hardening Subject,
  To, From, Cc, Bcc, Reply-To, or custom headers; remediating mail header
  injection findings; or reviewing contact forms, invite mailers, and
  notification builders — authorized and org-owned systems only.
---

# Email Header Injection Defenses

Design and verify **defenses** that stop CR/LF (and related control characters)
in user-influenced values from becoming extra SMTP/MIME headers or recipients.
Defensive hardening only; no exploit payload catalogs.

## Scope And Authorization

- **In scope:** Org-owned apps, workers, and services that build or send email;
  authorized secure-code review; own-project labs and staging mailers.
- **Out of scope:** Third-party mail systems; spam/phishing campaigns; forging
  mail against production recipients you do not own; raw exploit PoCs.
- Residual **offensive** proofs of mail CRLF → `crlf-injection` under written
  scope only. This skill owns **defense design, code review, and fix verification**.
- Redact addresses, tokens in subjects/bodies, API keys, and full message sources
  in tickets and reports. Prefer test inboxes you control.

## When To Use

- Contact, invite, password-reset, receipt, or notification flows set `Subject`,
  `To`/`Cc`/`Bcc`, `From`/`Reply-To`, or custom `X-*` headers from request input
- Code builds raw headers via string concat, templates, or `mail()`/`sendmail`
  flags instead of structured library setters
- Remediating a mail header injection / CRLF-in-email finding
- Mentions: email header injection, SMTP header injection, CRLF in Subject/To,
  `Bcc` smuggling, raw MIME header assembly

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized offensive CRLF / mail header proof | `crlf-injection` |
| HTTP response splitting / Set-Cookie / Location | `crlf-injection` |
| Reset link Host / authority poisoning | `password-reset-poisoning` |
| HTML/script in message body (not headers) | content policy / XSS skills |
| General allowlists at HTTP edge | `input-validation-patterns` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

### 1. Inventory mail header sinks

1. Find send paths: SMTP clients, provider SDKs (SES, SendGrid, Mailgun, …),
   framework mailers, CLI `sendmail`, queue workers that assemble MIME.
2. Per path, list **every header field** that can include user or partner data:
   subject, display names, addresses, reply-to, custom headers.
3. Flag dangerous patterns: string-built header blocks, `headers` arrays joined
   with `\r\n`, shelling out to `sendmail` with user-built headers, copying
   request headers into outbound mail. Prefer removing raw assembly over escape-only.

### 2. Prefer structured mail APIs

| Preference | Approach |
| --- | --- |
| 1. Provider / library API | Discrete `to`, `subject`, `html`/`text` fields |
| 2. MIME object model | Setters (`email.message`, JavaMail, MimeKit-style) |
| 3. Fixed template + typed vars | Body placeholders; headers from constants/validated types |
| 4. Last resort | Manual MIME with validated atoms only — never untrusted raw lines |

Never concatenate untrusted data into header blocks (e.g. `"To: " + user +
"\r\nSubject: " + subject`). Libraries that take a single raw `headers` string
are high risk if that string includes request data.

### 3. Reject control characters (fail closed)

1. **Reject** values containing `\r`, `\n`, `\0`, and other C0 controls before
   any header assignment (including display names).
2. Enforce max lengths on subject, name, and address.
3. Do **not** rely on denylisting the substring `Bcc:` alone — block the framing
   characters that enable new header lines.

### 4. Validate addresses and subjects

1. **Addresses:** parse with a maintained library; allowlist domains for closed
   mailers; multi-recipient only via explicit list types, not free-form header text.
2. **From / envelope:** server-controlled for public forms; no arbitrary user `From`.
3. **Subject / custom headers:** library encoding (e.g. RFC 2047) after forbidding
   CR/LF/NUL. Body HTML/XSS is separate from header validation.

### 5. Transport, ops, and verification

1. Authenticated SMTP or provider API; least-privilege keys; rate-limit outbound
   mail; cap recipients per message.
2. SPF/DKIM/DMARC help spoof impact but **do not** replace header injection fixes.
3. Log message IDs/template names, not secrets; unit-test CR/LF/NUL never reach
   the transport mock; legitimate Unicode subjects still send.
4. Staging residual retest → `crlf-injection` under SOW only. Apply
   `code-quality-standards` on mail code changes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Defend / remediate email header CRLF injection | **This skill** | — |
| Authorized mail/HTTP CRLF proof | `crlf-injection` | this skill for fix design |
| Class unclear | `injection-checking` | this after mail header sink confirmed |
| Reset URL host poisoning (not CRLF headers) | `password-reset-poisoning` | — |
| Boundary schemas / allowlists | `input-validation-patterns` | this for header-specific rules |
| Implement or review mailer code | `code-quality-standards` | **always** with this skill |
| Multi-vector ATO via mail | `account-takeover-methodology` | this for header sinks |

- **`crlf-injection`:** find/prove CRLF including mail. **This skill:** prevent
  and remediate without PoC catalogs.
- **`password-reset-poisoning`:** authority/host in links; different root cause.
- **`code-quality-standards`:** always apply when changing mail-sending code.

## Output Checklist

- [ ] Mail send paths and user-influenced header fields inventoried
- [ ] Raw header string concat / sendmail header files removed from user paths
- [ ] Structured library or provider API used for recipients and subject
- [ ] `\r` `\n` `\0` (and policy C0 set) rejected fail-closed on header values
- [ ] Addresses parsed; From/envelope server-controlled where required
- [ ] Length limits; multi-recipient only via explicit list types
- [ ] Rate limits and secret hygiene on mail credentials
- [ ] Tests cover hostile control chars without sending real spam
- [ ] Residual authorized retest routed to `crlf-injection`
- [ ] `code-quality-standards` applied; PII/tokens redacted in reports
- [ ] No exploit PoCs or bypass catalogs produced under this skill
