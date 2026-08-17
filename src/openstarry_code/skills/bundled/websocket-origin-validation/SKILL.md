---
name: websocket-origin-validation
description: >
  Authorized testing of WebSocket Origin header validation, cookie-authenticated
  upgrades, and CSWSH-style (cross-site WebSocket hijacking) risks on the HTTP
  Upgrade path. Use when assessing whether browsers can open a session-backed
  WebSocket from a foreign origin, whether Origin is missing/weak/allowlist-bypassed,
  or when SameSite and CSRF-like upgrade defenses need evidence — not for general
  message authz, rate limits, or binary frame reverse engineering.
---

# WebSocket Origin Validation (CSWSH-Focused)

Deep-dive on **Origin checks and cookie attachment at WebSocket upgrade**. Complements
`websocket-security` with an Origin/CSWSH-first model: ambient session on
`Upgrade: websocket`, then bidirectional read/write if the socket opens.

## Scope And Authorization

- **In scope:** owned apps, written pentest/bug-bounty scope listing the WS/WSS host,
  and labs/CTFs. PoC pages only on approved exploit hosts or local HTML under program
  rules — no phishing real users or hijacking third-party sessions.
- Prefer staging and **your** test accounts. Limit rates; no production amplification.
  Redact cookies, tokens, `Sec-WebSocket-Key`, and PII. Browser threat model (cookie +
  Origin) is primary; native clients are not CSWSH. Gate DoS under `websocket-security`.

## When To Use

- WebSocket authenticates primarily via **cookies** on the upgrade request.
- Suspected missing, reflected, prefix-matched, or `null`-trusted `Origin` checks.
- Need CSWSH evidence: foreign page → **101** → sensitive events or state-changing sends.
- Cookie flags (`SameSite`, `Secure`, Domain/Path) may allow/block cross-site upgrades.
- Keywords: CSWSH, cross-site WebSocket, Origin validation, cookie WS auth, CSRF-like upgrade.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Full WS authz, injection, rate limits, hardening survey | `websocket-security` |
| Opaque binary frames / opcodes / state machine RE | `websocket-binary-reverse-engineering` |
| Classic form/API CSRF (non-WS) | `csrf-cross-site-request-forgery` |
| Credentialed CORS HTTP reads / TLS plaintext | `cors-credentialed-requests` / `tls-plaintext-acquisition` |

## Workflow

### 1. Baseline legitimate upgrade

Capture an honest client upgrade (DevTools, Burp, or PCAP after TLS plaintext):

```http
GET /socket HTTP/1.1
Host: app.example
Upgrade: websocket
Connection: Upgrade
Origin: https://app.example
Cookie: session=...
Sec-WebSocket-Version: 13
Sec-WebSocket-Key: ...
```

Record path/query (tokens in query are high risk), auth type, cookie flags, and
response (**101** vs 4xx).

### 2. Confirm ambient cookie auth on upgrade

| Check | Weak outcome |
| --- | --- |
| No cookie / expired session | Still **101** and usable socket |
| Cookie only, no non-cookie secret | Cross-site browser can attach cookie |
| Auth deferred to first message only | Upgrade always opens; auth skippable |

If a secret browsers cannot set from pure `new WebSocket(url)` is required **and**
enforced server-side, CSWSH impact drops — still test Origin for defense-in-depth.

### 3. Origin validation matrix

Replay one variable at a time: allowed app origin; `https://evil.example`;
prefix/suffix tricks (`app.example.evil.example`, `evil.app.example`); `null`;
missing `Origin`; `http://` vs `https://` scheme confusion.

```bash
# Lab only
websocat -H 'Cookie: session=TEST' -H 'Origin: https://evil.example' wss://app.example/socket
websocat -H 'Cookie: session=TEST' -H 'Origin: null' wss://app.example/socket
```

Document status code, whether the connection stays open, and any server log of Origin.

### 4. SameSite and CSRF-like upgrade conditions

CSWSH needs cookies on the cross-site upgrade **and** weak Origin (or no extra
anti-CSRF on connect/actions). **`SameSite=None; Secure`:** cookies often sent
cross-site → Origin/token critical. **`Lax`/`Strict`:** may block cross-site cookies;
retest in target browsers; still report weak Origin for hygiene. **Missing SameSite:**
browser-default dependent — record version. Unlike classic CSRF, a hijacked WS is a
**live channel** (subscribe, push, commands).

### 5. Browser CSWSH PoC (authorized harness only)

From a lab-controlled origin, without setting forbidden headers:

```html
<!-- Lab-only; authorized harness only -->
<script>
  const ws = new WebSocket("wss://app.example/socket");
  ws.onopen = () => { ws.send(JSON.stringify({ action: "list" })); };
  ws.onmessage = (e) => { console.log(e.data); };
</script>
```

Confirm: **101**? Private events? State-changing messages? Try `Origin: null` if
allowlisted. **Not CSWSH** if non-cookie secrets are enforced or cookies never
attach cross-site. Impact: PII events, account actions, admin opcodes. Stop at
clear evidence. Post-connect IDOR/injection/limits → `websocket-security`. Binary
opcodes → `websocket-binary-reverse-engineering`.

## Routing

| Observation | Next skill |
| --- | --- |
| Origin/CSWSH/cookie-upgrade is the core question | **this skill** |
| Broader WS security (message authz, injection, limits) | `websocket-security` |
| Binary frames / envelope / state machine | `websocket-binary-reverse-engineering` |
| Cannot see WSS plaintext | `tls-plaintext-acquisition` |
| Classic non-WS CSRF / credentialed CORS | `csrf-cross-site-request-forgery` / `cors-credentialed-requests` |
| Implement Origin allowlists / secure upgrade | `code-quality-standards` |

Keep **this skill primary** for Origin allowlist quality and CSWSH preconditions.
Use **`websocket-security`** when the engagement needs a full WS security survey.

## Output Checklist

- [ ] Endpoint URL(s), upgrade auth, cookie flags (`SameSite`, `Secure`, Domain/Path)
- [ ] Origin matrix: allowed, attacker, null, missing, bypass candidates
- [ ] CSWSH preconditions and browser PoC (101 / data / actions; browser version)
- [ ] Residual defenses (ticket, first-message token, SameSite blocking)
- [ ] Hand-off: message-layer → `websocket-security`; codecs → `websocket-binary-reverse-engineering`
- [ ] Scope statement; redacted evidence; test account IDs (not passwords)
- [ ] Remediation: exact Origin allowlist (no reflection/`null`); prefer non-cookie
      upgrade secrets; `SameSite` + short sessions; re-auth sensitive ops
