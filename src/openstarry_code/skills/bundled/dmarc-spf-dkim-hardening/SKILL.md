---
name: dmarc-spf-dkim-hardening
description: >
  Assess and harden email authentication for owned domains: SPF, DKIM, and
  DMARC (policy rollout, alignment, reporting). Use when reviewing DNS TXT
  records, spoofing resistance, p=none→quarantine→reject progression, third-party
  senders, BIMI readiness, or aggregate/forensic report setup on domains you
  control — not for forging mail or attacking third-party domains.
---

# DMARC / SPF / DKIM Hardening

Harden **email authentication** (SPF, DKIM, DMARC) for domains you own or are
explicitly authorized to manage. Goal: reduce spoofing while keeping legitimate
mail (corporate MTA, ESP, marketing, ticketing) deliverable.

## Scope And Authorization

- **In scope:** DNS and mail systems for **owned** or written-scope domains;
  staging subs; lab zones; vendor senders you may configure.
- **Out of scope:** spoofing third-party brands; bulk unsolicited mail; abusing
  open relays; harvesting `rua`/`ruf` of domains you do not operate.
- Prefer **DNS TXT review + controlled test messages** from approved paths.
  Gate `p=reject` behind monitoring and a change window.
- Redact DKIM private keys, SMTP credentials, and report payloads with PII.

## When To Use

- Inventory or fix SPF / DKIM / DMARC for an owned apex or subdomain
- Spoof tests still pass receiver checks; brand impersonation risk
- Moving DMARC from `p=none` toward `quarantine` / `reject`
- Multiple ESPs break alignment (Google, Microsoft, SES, SendGrid, etc.)
- SPF too many lookups, `+all`/`~all` gaps, missing or noisy `rua`/`ruf`
- BIMI needs aligned DMARC at enforcement; post-incident forged From: / BEC

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| App session/cookie theft | `cookie-security-flags`, ATO skills |
| Password-reset Host poisoning | `password-reset-poisoning` |
| Secrets in DNS/CI | `secrets-management-hygiene` |
| General change practice | `code-quality-standards` |
| TLS/edge HTTP hardening | `nginx-security-headers` |

## Core Model

```
From (RFC5322) → SPF (envelope path) → DKIM (sig) → DMARC (align + policy + reports)
```

| Control | Artifact | Hardened direction |
| --- | --- | --- |
| **SPF** | `v=spf1` TXT | Explicit `ip4`/`ip6`/`include`; end `-all` when inventory done; never `+all` |
| **DKIM** | `selector._domainkey` TXT | 2048-bit (or org-approved); rotate; sign From/Date/Subject/Message-ID |
| **DMARC** | `_dmarc` TXT | `p=` rollout; `rua=mailto:...`; set `sp=`; tune `aspf`/`adkim` |
| **Alignment** | SPF domain or DKIM `d=` vs From | Org or strict; third parties need aligned domain/CNAME |
| **Reporting** | `rua` / `ruf` | Monitored mailbox or analyzer |

**Good proof:** Authentication-Results show SPF/DKIM pass **and** DMARC aligned;
unauthorized sources fail policy as intended.  
**Bad proof:** “TXT exists” without alignment, lookup count, or fail-mode checks.

## Workflow

### 1. Inventory domains and senders

1. List apex + mail-relevant subs; map MTAs, Google/M365, ESPs, CRM, CI notify.
2. Capture public TXT (owned domain only):

```bash
dig +short TXT example.com
dig +short TXT _dmarc.example.com
dig +short TXT selector1._domainkey.example.com
```

### 2. SPF

1. Parse `include:`, `a`, `mx`, `ip4`/`ip6`, `redirect=`; count DNS lookups (max 10).
2. Terminal: `+all`/missing → critical; `~all` during discovery; prefer `-all` when proven.
3. Cover ESP envelope domains or use aligned custom domains; no duplicate SPF TXT.

### 3. DKIM

1. List selectors (ESP docs + sample `DKIM-Signature`); verify public key and length.
2. Confirm pass on production-like mail; watch list-manager rewrites.
3. Rotate: publish new selector → switch sign → retire old; never commit private keys.

### 4. DMARC and alignment

1. Read `p`, `sp`, `pct`, `aspf`, `adkim`, `fo`, `rua`/`ruf`.
2. Rollout: **`p=none`** (monitor) → **`quarantine`** → **`reject`** using aggregate data.
3. Alignment: SPF-aligned return-path **or** DKIM `d=` must match From (org default).
4. Third parties: custom bounce/From or CNAME DKIM so **From** aligns (vendor domain
   pass without alignment still **fails DMARC**).
5. Set `sp=` deliberately; park unused subs that could spoof the brand.

### 5. Verify and operate

1. Send one test per authorized path; record Authentication-Results (spf/dkim/dmarc).
2. Optional authorized fail-path check before enforce; do not spam third parties.
3. Triage `rua` unknowns before tightening `p=`; lower TTL during DNS cuts, then restore.
4. Document sender owners; on new ESP re-run alignment. Keys → `secrets-management-hygiene`;
   DNS/IaC PRs → `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SPF/DKIM/DMARC audit and enforcement rollout | **This skill** | — |
| DKIM keys, SMTP secrets, DNS API tokens | `secrets-management-hygiene` | this skill |
| DNS/IaC PRs, automation, tests | `code-quality-standards` | this skill |
| Phishing landing / web auth | web/ATO skills | this skill for From: domain auth only |
| Reset link Host header issues | `password-reset-poisoning` | not a DMARC substitute |

## Output Checklist

- [ ] Scope: owned/authorized domains; change window for `p=` moves
- [ ] Sender inventory with owners
- [ ] SPF: mechanisms, lookups ≤10, terminal policy, no duplicate TXT
- [ ] DKIM: selectors, key length, sample pass, rotation plan, no keys in VCS
- [ ] DMARC: `p`/`sp`/`pct`/alignment; `rua` monitored
- [ ] Alignment matrix per sender (SPF and/or DKIM vs From)
- [ ] Test Authentication-Results evidence (redacted)
- [ ] Aggregate unknowns triaged; target path none → quarantine → reject
- [ ] Residual exceptions and secrets/IaC hygiene noted

## Rules

- Defense and **owned-domain** operations only — no third-party spoofing.
- Records exist ≠ protection; require **alignment + enforced policy**.
- Never `+all`; treat `~all` as temporary during discovery.
- Do not jump to `p=reject` without report-backed sender coverage.
- Keep private keys out of public DNS and chat logs.
