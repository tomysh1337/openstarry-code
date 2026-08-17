---
name: cdn-waf-bypass-awareness
description: >-
  Authorized CDN/WAF bypass awareness: edge fingerprinting, origin exposure,
  alternate entrypoints, inspection gaps, cache/bot control boundaries, and
  residual-risk notes when CDN or WAF is the primary control. Use when reviewing
  whether Cloudflare/Akamai/Fastly/CloudFront/AWS WAF (or similar) can be skipped
  or inconsistently enforced during scoped assessments or defensive edge reviews.
---

# CDN / WAF Bypass Awareness (Authorized)

Awareness methodology for **how CDN and WAF edges fail as sole controls**:
skipped hops, weaker alternate hosts, origin reachability, and inspection
surfaces that do not match the origin parser. Complements payload-level work
in `waf-bypass-techniques` and defensive tuning in `waf-rule-tuning-basics`.

## Scope And Authorization

- **Authorized only**: owned apps, labs, CTFs, bug bounty / pentest SOW that
  explicitly allows edge, CDN, origin, and bot-mitigation testing.
- Goal is **control quality and residual risk** — show that in-scope traffic
  can skip, weaken, or inconsistently hit CDN/WAF — **not** mass evasion,
  CAPTCHA farming, volumetric floods, or third-party infrastructure abuse.
- Prefer staging, tester allowlists, unique canaries, and low volume. Direct
  origin IP / historical DNS use **only** when origin testing is in scope.
- Shared-cache side effects → canary paths and purge plans (`http-cache-poisoning-basics`,
  `host-header-cache-poison`). Redact cookies, tokens, origin IPs if policy
  requires, and internal WAF rule IDs from public notes.
- “Bypass awareness” alone without app impact is often **informational**; bind
  severity to reachable vulns, data exposure, or failed compensating controls.

## When To Use

- Engagement asks whether **CDN/WAF is skippable** or inconsistently applied.
- Fingerprints show edge products (CF-Ray, `Server: cloudflare`, Akamai,
  Fastly, CloudFront, AWS WAF headers) while app logic may still be reachable
  on other hosts, methods, or content-types.
- Keywords: CDN bypass, WAF skip, origin IP exposure, edge vs origin, bot fight
  inconsistency, secondary API without WAF, cache vs WAF boundary.
- Defensive review: edge is the main control and residual skip paths matter.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Signature/encoding payload retests past WAF | `waf-bypass-techniques` |
| Owned WAF FP triage / rule exceptions | `waf-rule-tuning-basics` |
| CDN cache key / Vary / purge design | `cdn-cache-key-design` |
| Cache poison second-client proofs | `http-cache-poisoning-basics` / `host-header-cache-poison` |
| 401/403 path ACL (not product WAF) | `401-403-bypass-techniques` |
| Rate-limit / CAPTCHA control gaps | `rate-limit-bypass-testing` / `captcha-bypass-research` |

## Workflow

1. **Authorize and fingerprint the edge**  
   Confirm scope for edge, origin, and alternate hostnames. Baseline a normal
   request: status, body class (app HTML vs challenge vs hard block), product
   headers (`cf-ray`, `x-amzn-waf`, `x-cache`, `via`, `server`), bot/JS
   challenge vs pure signature deny, and `Cache-Control` / HIT hints.

2. **Map the control boundary**  
   Document what the edge is supposed to do: TLS termination, WAF signatures,
   bot management, geo/IP rules, rate limits, cache. Note **where** rules bind
   (hostname, path prefix, API gateway vs static zone). Inventory related
   names: www vs api vs mobile vs partner vs staging.

3. **Alternate entrypoint matrix (awareness)**  
   Change **one** surface at a time; compare edge verdict vs origin behavior:

   | Surface | What to check |
   | --- | --- |
   | Host / vhost | Admin, legacy, bare apex, regional CDN aliases in scope |
   | Client class | Browser vs mobile UA vs API client; cookie/bot score paths |
   | Protocol | HTTP/1.1 vs HTTP/2; WebSocket/gRPC if in scope (weaker rules often) |
   | Content-Type | Query vs form vs JSON vs multipart inspection gaps |
   | Method / path | Verb overrides and aliases that skip path-scoped WAF rules |
   | Auth context | Anonymous vs session — some rules only on unauthenticated |

   Success criterion for awareness: **different security posture** (no challenge,
   weaker block, or raw origin errors) on an in-scope surface that still serves
   sensitive app logic.

4. **Origin reachability (scope-gated)**  
   If SOW allows: compare public CDN hostname vs known origin (historical DNS,
   TLS cert SANs, mis-set DNS, backup host). Direct origin with correct `Host`
   that **skips WAF** is a classic residual finding — do not port-scan wide
   ranges or abuse unrelated cloud tenants. Document: origin accepts public
   traffic? TLS valid? App identical? WAF entirely absent?

5. **Inspection vs enforcement gaps**  
   Awareness classes (hand deep work to sibling skills):

   | Class | Signal | Next skill |
   | --- | --- | --- |
   | Signature brittle | Known PoC blocked one encoding, allowed another | `waf-bypass-techniques` |
   | Path ACL only | 403 on string path; origin normalizes differently | `401-403-bypass-techniques` |
   | Cache unkeyed | Edge caches attacker-shaped body for others | cache-poison skills |
   | Bot/CAPTCHA UI-only | API accepts without server verify | `captcha-bypass-research` |
   | Quota key weak | Limits per IP only / trusts client XFF | `rate-limit-bypass-testing` |
   | Desync | Edge and origin disagree on request framing | `request-smuggling` / `http2-specific-attacks` |

6. **Prove residual risk, not “200 means bypass”**  
   Soft challenges, soft-404, and cached block pages mislead. Prefer evidence
   that **origin processed** the request (app error oracle, authenticated body,
   debug header only from origin, timing). If bypass only enables a class PoC,
   keep class skill primary for impact.

7. **Defensive takeaways**  
   Prefer app-layer authz and input validation over edge-only safety; lock
   origin to CDN/WAF (mTLS, allowlisted edge egress, private origin); unify WAF
   profiles across hosts/APIs; strip untrusted hop headers at the edge; stage
   rules with `waf-rule-tuning-basics`; design cache keys with
   `cdn-cache-key-design`; implement fixes under `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| CDN/WAF skip / inconsistent edge posture awareness | **This skill** | — |
| Encoding/signature payload past WAF | `waf-bypass-techniques` | this for edge map |
| Operate/tune owned WAF rules | `waf-rule-tuning-basics` | this for residual skip notes |
| CDN key, Vary, purge hardening | `cdn-cache-key-design` | this for attack model |
| Path 401/403 ACL tricks | `401-403-bypass-techniques` | this if edge-enforced |
| Cache poison / Host+cache | poison skills above | this for CDN role |
| Bot/CAPTCHA or rate-limit gaps | captcha / rate-limit skills | this for edge inventory |
| Unknown injection class after reachability | `injection-checking` | this if blocks appear |
| Code/IaC origin lockdown and tests | `code-quality-standards` | always on fixes |

## Output Checklist

- [ ] Authorization: edge, origin, alternate hosts, volume limits stated
- [ ] Edge fingerprint (product, challenge vs hard block, cache hints)
- [ ] Control boundary map (what edge enforces, on which hosts/paths)
- [ ] Entrypoint matrix results (host, client, protocol, content-type, method)
- [ ] Origin reachability outcome (in-scope only) or explicit “not tested”
- [ ] Inspection/enforcement gap class labeled; handoffs to sibling skills
- [ ] Origin-processing proof (not status code alone)
- [ ] Residual risk and severity bound to impact
- [ ] Remediation: origin lockdown, unified profiles, app fixes, rule/cache design
- [ ] Secrets, origin details, and payloads redacted per policy
