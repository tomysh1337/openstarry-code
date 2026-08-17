---
name: acme-dns01-automation
description: >
  Automate ACME DNS-01 certificate issuance and renewal for owned zones:
  TXT hooks, provider APIs, propagation waits, wildcards, multi-name certs,
  cleanup, staging, and rate-limit safety. Use when wiring Certbot, lego,
  acme.sh, Caddy, or Traefik DNS-01 solvers; debugging _acme-challenge TXT
  failures; choosing DNS API scopes; or automating wildcard TLS without
  opening HTTP-01 on port 80 — not for third-party zone takeover or unowned
  ACME/DNS accounts.
---

# ACME DNS-01 Automation

Operate **ACME DNS-01** so a CA validates domain control via
`_acme-challenge.<name>` **TXT** records. Prefer for **wildcards**, internal-only
HTTP surfaces, and multi-SAN sets HTTP-01 cannot cover. Ownership only.

## When To Use

| Situation | Direction |
| --- | --- |
| Issue/renew via DNS-01 (Certbot, lego, acme.sh, Caddy, Traefik) | **This skill** |
| Wildcard `*.example.com` or names without public :80 | **This skill** |
| Auth/cleanup hooks; provider plugins; propagation wait | **This skill** |
| Multi-zone or split-horizon challenge placement | **This skill** |
| Staging→prod ACME cutover; rate-limit recovery | **This skill** |
| Kubernetes Issuer/Certificate CRDs as main surface | `cert-manager-basics` |
| DNS API tokens / ACME account key storage | `secrets-management-hygiene` |
| Edge TLS headers/ciphers only (not issuance) | `nginx-security-headers` |
| TLS capture / RE of live sessions | `tls-plaintext-acquisition` |

## Workflow

### 1. Confirm ownership and ACME environment

1. List FQDNs/wildcards; map each to the **authoritative** zone (and parent if
   challenges are CNAME-delegated).
2. Use **staging ACME** until order + TXT succeed end-to-end.
3. Note rate limits, account key path, and EAB requirements if any.

### 2. Choose client and DNS integration

| Approach | Prefer when |
| --- | --- |
| Native provider plugin (lego, Certbot DNS, acme.sh) | Supported provider; stable API |
| Generic auth/cleanup hooks | Custom DNS API or bastion-only updates |
| Orchestrator solver (cert-manager, Traefik/Caddy DNS) | Cluster/ingress owns lifecycle |

Pin client versions. Prefer **one** automation writer per zone (no racing TXT).

### 3. Least-privilege DNS credentials

1. Scope tokens to TXT create/delete on `_acme-challenge*` — not full zone admin.
2. Keep secrets out of git; inject via env/secret manager
   (`secrets-management-hygiene`). Separate staging vs production tokens.
3. Prefer time-bound or IP-restricted keys when the provider supports them.

### 4. Challenge lifecycle

```text
order → authz per name → present TXT → wait propagation →
CA query → validate → cleanup TXT → finalize CSR → install cert+key
```

1. **Present:** set TXT at `_acme-challenge.<domain>` to the exact token.
2. **Propagate:** wait until **authoritative** NS serve the value (not only a
   public recursive cache). Tune client DNS timeouts for multi-primary lag.
3. **Validate:** then let the client signal the ACME server.
4. **Cleanup:** delete challenge TXT after success or terminal failure.

**CNAME delegation:** if `_acme-challenge` CNAMEs to an automation zone, write
TXT at the **target**; confirm the CA follows CNAMEs.

### 5. Multi-name and wildcard

- Multiple SANs need concurrent or sequential TXT without clobbering siblings.
- Wildcard `*.example.com` requires DNS-01; apex is separate if both are on cert.
- CAA must allow the chosen CA before burning production quota.

### 6. Diagnose failures (owned zones)

| Symptom | Checks |
| --- | --- |
| NXDOMAIN / wrong zone | Authoritative NS; zone cut; FQDN typos |
| Stale TXT | Failed cleanup; multiple writers |
| Propagation timeout | Wait too short; split-horizon wrong view |
| Unauthorized ACME | Account key, EAB, wrong directory URL |
| Rate limited | Prod misused as staging; backoff; stop reissue loops |
| ServFail / DNSSEC | Broken RRSIG after dynamic updates |

```bash
# Owned zone only — query authoritative NS when possible
dig +short TXT _acme-challenge.example.com @ns1.example.com
```

### 7. Install, renew, hand-off

1. Install full chain + key with tight modes; reload services after renew.
2. Dry-run renew before prod cron; monitor days-to-expiry and renew exit codes.
3. Edge policy → `nginx-security-headers`. K8s CRDs → `cert-manager-basics`.
   Code/CI quality → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| DNS-01 hooks, plugins, propagation, wildcards, renew | **This skill** |
| cert-manager Issuer/Certificate/Order/Challenge | `cert-manager-basics` |
| ACME/DNS API key storage and rotation | `secrets-management-hygiene` |
| nginx/edge headers and TLS policy | `nginx-security-headers` |
| Owned HTTPS plaintext / capture | `tls-plaintext-acquisition` |
| Renew job scripts, containers, CI | `code-quality-standards`, `ci-cd-pipeline-patterns` |

Keep **this skill primary** for DNS-01 mechanics; switch for CRDs, org secrets,
or edge policy only.

## Output Checklist

- [ ] Domains/zones owned; ACME directory (staging vs prod) recorded
- [ ] Client + provider/hook chosen; version pinned; single writer per zone
- [ ] DNS credentials least-privilege; not in git; staging/prod separated
- [ ] TXT at correct `_acme-challenge` (or CNAME target); multi-SAN safe
- [ ] Propagation on **authoritative** NS; cleanup after success/failure
- [ ] CAA allows CA; wildcards/SANs match; staging success before prod
- [ ] Cert+key installed; reload/renew dry-run; expiry monitoring
- [ ] Routed: CRDs → `cert-manager-basics`; keys → `secrets-management-hygiene`;
      edge → `nginx-security-headers`; code/CI → `code-quality-standards`

## Scope And Authorization

- **In scope:** DNS zones, ACME accounts, and hosts **you own** or are explicitly
  authorized to automate; lab/staging first; production with change window.
- **Out of scope:** challenges on domains you do not control; stolen or
  over-scoped DNS credentials; mass re-issuance against third parties;
  intentional CAA/DNSSEC breakage on shared infrastructure.
- Prefer **staging ACME** until present → propagate → validate → cleanup works.
  Treat ACME account keys and DNS API tokens as high-tier secrets; redact from
  tickets, chat, logs, and screenshots.
- Do not infer authorization from “sandbox-looking” targets. Gate DNS API writes
  and production ACME directory use on stated ownership or written approval.
