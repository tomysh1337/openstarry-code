---
name: bug-bounty-methodology
description: >
  End-to-end bug bounty workflow for authorized public or private programs only:
  program selection, scope discipline, recon handoff, testing prioritization,
  evidence quality, and professional reporting. Use when hunting on HackerOne,
  Bugcrowd, Intigriti, YesWeHack, vendor portals, or private invites — not for
  unsolicited testing of sites without a program or written permission.
---

# Bug Bounty Methodology (Authorized Programs Only)

## Scope And Authorization

- **Only** test assets explicitly **in scope** on a published program policy, private invite brief, or equivalent written authorization.
- Program rules **outrank** generic pentest habits: rate limits, excluded vulnerability classes, forbidden automation, data-handling, safe-harbor text, and disclosure timelines are binding.
- **Never** treat “interesting subdomain,” lookalike brand, or third-party SaaS embedded in the app as in-scope unless the policy names it.
- Prefer **non-destructive** proof. Avoid DoS, spam, social engineering of employees, physical attacks, and ransomware-style demos unless the program **explicitly** allows that class (rare).
- Use **your own** accounts or program-provided test accounts. Do not access other users’ real personal data beyond the minimum needed to prove impact; stop and report if you hit sensitive PII dumps.
- Redact cookies, session tokens, API keys, `Authorization` headers, and personal data in screenshots and public writeups until the program allows disclosure.
- Safe harbor applies only when you comply with the policy. Willful out-of-scope testing is not “bounty methodology.”

## Use When

| Situation | Direction |
| --- | --- |
| Starting or structuring a bug bounty engagement on a named program | **This skill** |
| Interpreting scope, wildcards, exclusions, and duplicate risk | **This skill** |
| Improving report quality, severity narrative, and retest notes | **This skill** |
| Building hostname/API inventory inside program scope | `recon-and-methodology` (primary for recon depth) |
| Specific vuln class already identified (IDOR, XSS, …) | Matching class skill as **primary** |
| Supply-chain / SBOM / dependency hygiene on in-scope artifacts | `sbom-and-supply-chain` / `dependency-confusion` |
| Secrets found in repos, JS, CI, or responses | `secrets-management-hygiene` |
| Vendor asks for secure fix guidance in code | `code-quality-standards` |

Do **not** use this skill to justify testing targets **without** a program or contract.

## Core Idea

Bug bounty success is **process × scope discipline × evidence**, not random scanner noise.  
Workflow: **policy → scope map → attack surface → prioritized tests → minimal PoC → clear report → retest**.  
Maximize signal: fewer high-quality findings beat dozens of out-of-scope or duplicate noise reports.

## Workflow

### 1. Program selection and policy lock

1. Read the **entire** policy: scope, out-of-scope, eligibility, rewards, response targets, and “known issues.”
2. Extract a **rules card** you keep open while testing:

   | Field | Notes |
   | --- | --- |
   | Program / asset | URL of policy, last updated date |
   | In-scope | Domains, wildcards, apps, API, IPs |
   | Out-of-scope | Third parties, marketing sites, `*.example-cdn.com`, etc. |
   | Excluded classes | e.g. rate limit, best-practice, self-XSS, missing headers only |
   | Auth rules | Credential stuffing ban, 2FA, test accounts |
   | Automation | Scanner allowed? RPS limits? |
   | Data rules | No exfil, max records, PII handling |
   | Report channel | Platform form only vs email |
   | Disclosure | VDP vs bounty; public disclosure rules |

3. If policy is ambiguous (e.g. “all company properties”), **ask the program** or start with clearly listed assets only.
4. Create a local folder: `policy/`, `scope/`, `recon/`, `notes/`, `evidence/`, `reports/`, `redacted/`.

### 2. Scope table (living document)

Build before heavy active testing (`recon-and-methodology` for discovery techniques):

| Asset | Type | In scope? | Auth | Source | Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `app.example.com` | web | yes | user | policy | P1 | main app |
| `api.example.com` | API | yes | token | policy | P1 | |
| `static.vendor.com` | CDN | no | — | policy exclusion | — | skip |
| `dev.example.com` | staging | ? | — | CT / guess | hold | confirm before test |

Rules of thumb:

- **Wildcard** `*.example.com` still excludes names the policy carves out and most third-party CNAMEs.
- **IP scope** does not automatically include every vhost on shared hosting — stay on named hosts.
- **Mobile apps** may be in scope while their backend hosts need separate listing — verify both.
- Re-check scope when you find a new host; do not “assume brand = scope.”

### 3. Account and environment setup

1. Register hunter accounts with **identifiable** usernames/emails when the program requests it (aids triage and safe harbor).
2. Prepare **two** roles for authz work (User A / User B, or user vs admin if allowed) early — required for IDOR quality.
3. Configure proxy (Burp/ZAP/mitmproxy), separate browser profile, and logging that does not sync secrets to personal cloud unencrypted.
4. Set **soft rate limits** below program caps; back off on `429` / WAF blocks; never turn a research script into an availability incident.
5. Prefer staging if the program lists it and impact is equivalent; note production-only findings carefully (data minimization).

### 4. Recon (scoped) — hand depth to recon skill

1. Passive first: policy assets, certificate transparency for **in-scope** base domains, public docs, mobile package API hosts, JS endpoint harvest.
2. Resolve and tag CDN vs origin; exclude third-party SaaS.
3. Light active discovery only on confirmed in-scope hosts; throttle content discovery.
4. Output a surface summary: apps, APIs, auth mechanisms, interesting parameters, admin panels, file upload, SSRF-prone features, webhooks.
5. Primary skill for recon mechanics: **`recon-and-methodology`**. Return here for prioritization and reporting.

### 5. Prioritize testing (impact × likelihood × uniqueness)

Typical high-ROI order for bounty (adjust to program history and technology):

| Priority | Theme | Next skill examples |
| --- | --- | --- |
| P0 | Broken access control / multi-tenant IDOR | `idor-broken-object-authorization` |
| P0 | AuthN/session/JWT/OAuth flaws | `api-auth-and-jwt-abuse`, `oauth-oidc-misconfiguration` |
| P1 | Injection with clear impact | `injection-checking` → class skill |
| P1 | SSRF to cloud metadata / internal | `ssrf-server-side-request-forgery` |
| P1 | RCE-class file upload / deserial / CMDi | matching skills |
| P2 | XSS with real session impact | `xss-cross-site-scripting` |
| P2 | Business logic / race / payment | `business-logic-vuln`, `race-condition` |
| P3 | CSRF, open redirect, cache, clickjack (when in scope and impactful) | matching skills |
| Process | Secrets in public assets, dependency confusion on **disclosed** packages | `secrets-management-hygiene`, `dependency-confusion`, `sbom-and-supply-chain` |

**Avoid low-signal defaults** that many programs mark N/A or informative: missing security headers alone, email spoofing without infra proof, logout CSRF, verbose errors without impact, automated scanner dumps without validation.

### 6. Proof-of-concept standards

1. **Minimal steps:** numbered reproduction from a clean state (browser or `curl`).
2. **One variable:** show the single change that causes the bug (ID swap, header, parameter).
3. **Impact statement:** what an attacker gains (read org A’s invoices; execute JS as victim; hit `169.254.169.254`; escalate role). Tie to confidentiality, integrity, availability, or authZ boundary.
4. **Evidence:** request/response pairs, redacted screenshots, short video only if UI-heavy; timestamps and account IDs used.
5. **Blast radius check:** stop after proving access to **your** second account’s object or a program-approved canary — do not bulk-download customer data.
6. **Root cause hypothesis:** e.g. “missing server-side tenant check on `GET /api/invoices/{id}`” — helps triage and fix; pair remediation detail with `code-quality-standards` when appropriate.

```http
# Example evidence skeleton (redact tokens)
GET /api/v1/invoices/1002 HTTP/1.1
Host: api.example.com
Authorization: Bearer <REDACTED_USER_A>
Cookie: session=<REDACTED>

HTTP/1.1 200 OK
{"id":1002,"owner":"user_B","total":"..."}
```

### 7. Duplicate and known-issue hygiene

1. Search the program’s reports (if visible), hacktivity, and your own past submissions for the same endpoint/class.
2. If a variant of a known class exists on a **different** asset or with **higher** impact, state the delta clearly (“previous report fixed user IDs; admin export still trusts client `org_id`”).
3. Collate related weak spots into **one** report when they share root cause; split when assets or impact differ enough for separate triage.

### 8. Report writing (triage-friendly)

Structure:

1. **Title:** clear, specific — `[IDOR] Read other users’ invoices via GET /api/v1/invoices/{id}`
2. **Summary:** 2–4 sentences: what, where, impact.
3. **Severity:** your estimate using the program’s scale (CVSS optional if they use it); explain **why**, not only a number.
4. **Affected assets:** exact hosts/paths/app versions; confirm in-scope citation (policy line or asset name).
5. **Steps to reproduce:** numbered, complete, minimal.
6. **PoC material:** HTTP logs, screenshots, optional script **without** destructive payloads.
7. **Impact:** realistic attacker story aligned with program’s asset value.
8. **Remediation:** concrete fix (server-side authZ, fix redirect allowlist, parameterized query); avoid vague “sanitize input.”
9. **Supporting info:** browser/tool versions, account emails used, discovery date, whether issue is production or staging.

Tone: professional, neutral, no threats or ransom language. Assume the triage analyst is skilled but unfamiliar with your full recon path.

### 9. Submission, communication, and retest

1. Submit only through the **authorized** channel.
2. Respond promptly to triage questions; provide extra logs rather than arguing severity first.
3. Accept CWE/severity adjustments when impact was overstated; update with better PoC if under-triaged.
4. On fix: retest exactly the original steps plus close variants; report residual risk honestly.
5. Respect disclosure timelines; do not publish before permission or automated platform disclosure rules allow.
6. After close: store redacted notes for your methodology; do not recycle other hunters’ private details.

### 10. Operations hygiene for hunters

| Topic | Practice |
| --- | --- |
| Secrets | Never commit program cookies or API keys to public Git; use `secrets-management-hygiene` habits |
| Automation | Scope-limited; respect robots only as courtesy — **policy** is the authority; avoid noisy full-port scans unless allowed |
| Collaboration | Team/private program rules on sharing; no duplicate spam across teammates without coordination |
| Legal | Leave immediately if you exit scope; document and notify program if accidental access to sensitive data occurred |
| Burnout | Rotate targets; deep-dive one app area rather than shallow-scanning everything |

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Bounty program workflow, scope, reporting quality | **This skill** | — |
| Asset inventory, passive/active recon mechanics | `recon-and-methodology` | this skill for policy/scope gates |
| Dependency / package namespace confusion on in-scope packages | `dependency-confusion` | this skill for program rules on supply chain |
| SBOM / broad SCA / pin hygiene review when allowed | `sbom-and-supply-chain` | this skill |
| Exposed secrets, tokens, keys in scope assets | `secrets-management-hygiene` | this skill for report framing |
| Secure fix / patch review in application code | `code-quality-standards` | class skill for vuln type |
| Specific vulnerability class testing | Matching class skill | this skill for report + scope |
| API map / OpenAPI / GraphQL surface | `api-recon-and-docs` | this + recon |
| WAF research | `waf-bypass-techniques` | only if policy allows and after baseline finding |

## Checklist

- [ ] Program policy read end-to-end; rules card filled; last-updated date noted
- [ ] Written confirmation that target assets are in scope (policy text or invite)
- [ ] Out-of-scope and excluded classes listed and respected
- [ ] Scope table maintained; new hosts verified before testing
- [ ] Test accounts (ideally dual-role) ready; rate limits configured
- [ ] Recon passive-before-active; surface summary completed
- [ ] Test plan prioritized by impact; class skills used for deep work
- [ ] PoC minimal, reproducible, non-destructive; sensitive data minimized
- [ ] Report: title, summary, asset, steps, evidence, impact, remediation
- [ ] Tokens/PII redacted in attachments; raw evidence stored privately
- [ ] Duplicate/known-issue check performed
- [ ] Triage follow-ups answered; retest documented after fix
- [ ] Disclosure only per program rules
- [ ] No out-of-scope hosts, third-party systems, or prohibited techniques used

## Rules

- **Authorized programs only.** No program / no SOW → no testing under this skill.
- Scope and policy beat curiosity. When unsure, ask or skip.
- Prove impact with the least invasive method; never “borrow” real customer data sets.
- Do not DDoS, brute-force credentials, phish employees, or chain into third-party vendors off-scope.
- One solid report with clean evidence outperforms scanner noise.
- Keep hunter secrets and session material out of public repos and writeups (`secrets-management-hygiene`).
- Hand off recon depth, vuln classes, supply chain, and code fixes to the specialized skills above; remain the **orchestrator** for bounty process and report quality.
---

# Note

This skill is the **front door for bug bounty process**. It does not replace class-specific exploitation skills. Always keep the program policy as the highest-priority document for the engagement.
