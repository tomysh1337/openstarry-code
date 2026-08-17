---
name: origin-ip-concealment
description: >
  Hide and keep hidden the real origin server IP behind a CDN/WAF edge for owned
  infrastructure: DNS hygiene, historical and cert leaks, origin firewall
  allowlists, authenticated origin pulls, and continuous exposure checks.
  Use when placing origins behind Cloudflare/CloudFront/Fastly/Akamai/Azure CDN,
  locking origin to edge-only, remediating direct-to-origin hits, or reviewing
  DNS/mail/CT leaks that bypass the CDN — not for attacking third-party sites.
---

# Origin IP Concealment Behind CDN

Keep the **real origin address off the public Internet path**: clients reach only
CDN/WAF anycast; origin accepts traffic only from the edge (and approved ops
paths). Prefer the org’s CDN product, DNS, and cloud firewall IaC over ad-hoc
iptables on a single host.

## Scope And Authorization

- **In scope:** origins, DNS, certs, mail, cloud SGs/NSGs/firewalls, and CDN
  origin settings you **own** or are contracted to harden; labs and CTF infra
  under explicit rules of engagement.
- **Out of scope:** discovering or DDoS’ing third-party origins; scanning the
  Internet for “real IPs” without authorization; weakening production TLS or
  opening origin world-wide “just to test” without change control and rollback.
- Prefer **config + authoritative DNS + CT/history review** over active probes.
  Controlled connectivity checks only from approved vantage points to owned IPs.
- Redact origin IPs, bastion addresses, and customer identifiers in tickets and
  public docs. Pair secret material (origin tokens, mTLS keys) with
  `secrets-management-hygiene`.

## When To Use

- Putting an app **behind CDN/WAF** and ensuring origin is not still public
- **Direct-to-origin** requests succeed (Host header, bypass CDN IP)
- Hardening **origin allowlists** (CDN published ranges, authenticated pulls, mTLS)
- Cleaning **DNS/history/CT/mail** artifacts that still publish origin A/AAAA
- Post-incident: origin flooded or scanned despite “we use a CDN”
- Mentions: origin IP leak, real IP behind Cloudflare, CDN bypass, authenticated
  origin pull, origin shield, grey-cloud, direct-to-origin, 回源 IP, 源站隐藏

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| CDN cache keys, Vary, purge | `cdn-cache-key-design` |
| Host/XFH cache poison (authorized) | `host-header-cache-poison` |
| Generic SG/firewall methodology | `firewall-rule-review` / cloud SG skills |
| nginx edge headers / TLS termination | `nginx-security-headers` |
| SSRF to metadata/internal | `ssrf-server-side-request-forgery` / `cloud-metadata-ssrf-defenses` |
| Implementation quality baseline | `code-quality-standards` |

## Workflow

1. **Map the intended path.** Document public hostnames → CDN anycast → (optional
   shield) → origin host/LB/private IP. List every origin listener (80/443 and
   admin ports). Note dual-stack AAAA. Mark which names must stay “orange-cloud”
   / proxied vs DNS-only (grey) and why.

2. **Inventory leak surfaces (owned data first).**

   | Surface | What to check |
   | --- | --- |
   | Live DNS | A/AAAA for apex, www, api, staging, mail, cdn-origin, internal CNAMEs |
   | Historical DNS | Passive DNS / org DNS exports / old runbooks still listing origin |
   | Certificates | CT logs and current SANs; origin-only hostnames on public certs |
   | Mail / SPF / MX | SPF `ip4:`/`ip6:`, MX A records pointing at app origin |
   | App content | Absolute URLs, error pages, `Server` banners, debug hostnames |
   | Third-party | Status pages, monitoring agents, CI deploy hooks hitting origin IP |
   | Cloud metadata | Elastic IPs, public NLB/ALB still attached “for convenience” |

3. **Remove origin from public resolution.** Public names should resolve only to
   CDN/anycast (or private for non-public envs). Prefer **origin hostnames that
   never appear in public DNS** (CDN “origin hostname” private, or resolved only
   inside the edge control plane). Deprecate grey-cloud records that publish the
   real IP. Split mail to dedicated MTAs — do not co-host MX on the app origin.

4. **Lock origin ingress to the edge.**

   | Control | Practice |
   | --- | --- |
   | Network allowlist | SG/NSG/firewall: 443 (and 80 only if needed) from **CDN published IP ranges** or private path only; deny `0.0.0.0/0` to origin |
   | Authenticated origin pull | CDN shared secret / custom header verified at origin **and** network lock — header alone is forgeable if origin is public |
   | mTLS to origin | Client cert required from edge; pin/rotate via secrets hygiene |
   | Host validation | Origin vhost accepts only expected `Host` / SNI; reject bare-IP access |
   | Admin ports | SSH/RDP/DB never on the same public IP path; bastion/VPN/SSM only |
   | Range updates | Automate CDN range refresh; stale allowlists break or re-open holes |

5. **Eliminate residual public attachments.** Disassociate unused Elastic IPs;
   prefer private origin + CDN private connectivity / origin shield / tunnel
   products when the platform supports them. Ensure staging and “old prod” IPs
   are not still world-open with production Host headers.

6. **Verify concealment (owned checks only).**

   - From an external approved host: public hostname → CDN; origin IP:port →
     **timeout/reset/deny** (not app 200) when not coming from edge ranges.
   - With CDN client cert/header as configured: edge → origin succeeds.
   - Re-check DNS/CT/mail after changes; search org repos for hard-coded origin IPs.
   - Spot-check historical DNS remediation (TTL expiry, old A records gone).

7. **Operate continuously.** Alert on unexpected public listeners and SG drift;
   subscribe to CDN range changes; re-audit after migrations. Document exception
   origins (partners that must hit origin) with owner + expiry.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Origin IP hide/lock behind CDN, leak remediation | **This skill** | — |
| CDN cache key / Vary / purge | `cdn-cache-key-design` | this for origin exposure |
| Cloud SG world-open on origin | `aws-security-groups-review` / `firewall-rule-review` | this for CDN-only intent |
| nginx Host / TLS at origin | `nginx-security-headers` | this for who may connect |
| Origin tokens, mTLS keys, pull secrets | `secrets-management-hygiene` | this for placement |
| Authorized Host/cache attacks | `host-header-cache-poison` | this for direct-origin risk |
| IaC/firewall/app verify automation | `code-quality-standards` | **always** on changes |

## Output Checklist

- [ ] Intended client → CDN → origin path documented (incl. dual-stack)
- [ ] Public DNS only points at CDN/anycast for customer hostnames
- [ ] No residual A/AAAA/MX/SPF/history/CT/runbook leaks of origin (or tracked exceptions)
- [ ] Origin SG/firewall denies world; allows CDN ranges and/or private path only
- [ ] Authenticated pull and/or mTLS in place where product supports; not header-only on open IP
- [ ] Origin rejects bare-IP / wrong Host; admin ports off public origin path
- [ ] External check: direct origin closed; via CDN open
- [ ] CDN IP-range update process and SG drift alerts defined
- [ ] Secrets for origin auth handled with `secrets-management-hygiene`
- [ ] `code-quality-standards` applied to IaC, origin auth middleware, and tests
