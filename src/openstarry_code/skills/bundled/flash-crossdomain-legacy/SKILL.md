---
name: flash-crossdomain-legacy
description: >-
  Historical and residual assessment of Adobe Flash crossdomain.xml and
  Microsoft Silverlight clientaccesspolicy.xml: over-permissive allow-access-from
  wildcards, socket policies, domain attributes, and leftover player surfaces.
  Use when legacy Flash/Silverlight assets, cross-domain policy files, or
  remove-or-restrict hardening of dead plugin trust roots is in scope.
---

# Flash / Silverlight Cross-Domain Policy (Legacy)

## When To Use

- Targets still serve `/crossdomain.xml`, path-scoped Flash policies, or `/clientaccesspolicy.xml`.
- Inventories mention `.swf`, Flash Player, AIR, Silverlight XAP, or old media/game hosts.
- Hardening asks whether residual plugin-era trust (`*`, `secure="false"`, open sockets) should be **removed or restricted**.
- Historical review, CTF/legacy app, or residual surface on authorized hosts.
- Not primary for modern browser CORS — use `cors-cross-origin-misconfiguration`. Not primary for `window.postMessage` — use `postmessage-security`. Combine when legacy policies sit beside modern CORS on the same origin.

## Scope And Authorization

- Authorized targets, labs, CTFs, owned apps, and in-scope production only.
- Treat as **legacy residual risk**: mainstream browsers dropped Flash/Silverlight; impact often needs outdated clients, kiosks, specialized players, or non-browser runtimes that still honor policy files.
- Prefer passive policy fetch and static SWF/XAP inventory. Do not deploy malicious SWF against real users.
- Lab clients or documented historical models only under engagement rules. Redact secrets; keep originals immutable.

## Workflow

### 1. Inventory policy and plugin surfaces

1. Fetch common locations (HTTP/HTTPS, apex and relevant subdomains):

   | Path | Runtime |
   | --- | --- |
   | `/crossdomain.xml` | Flash / some socket clients |
   | `/clientaccesspolicy.xml` | Silverlight |
   | Path-relative policies near SWF/content | Flash (site- or directory-scoped) |
   | Socket policy on TCP 843 (if in scope) | Flash XML/socket policy |

2. Search HTML, JS, and CDN manifests for `.swf`, Shockwave MIME types, `.xap`, `swfobject`, Ruffle shims, or old players.
3. Note CDN vs origin: policies on the **data host** (bucket, media domain) matter as much as the app origin.
4. Record status, `Content-Type`, cache headers, and host/path differences.

### 2. Parse crossdomain.xml risk factors

Illustrative high-risk shape:

```xml
<cross-domain-policy>
  <site-control permitted-cross-domain-policies="all"/>
  <allow-access-from domain="*" secure="false"/>
  <allow-http-request-headers-from domain="*" headers="*" secure="false"/>
</cross-domain-policy>
```

| Element / attribute | High risk when… |
| --- | --- |
| `allow-access-from domain="*"` | Any Flash origin may load data from this host |
| `secure="false"` on HTTPS hosts | HTTP SWF may access HTTPS data |
| Broad `to-ports` / socket ranges | Cross-domain sockets to many ports |
| `permitted-cross-domain-policies="all"` | Nested/meta policies widely allowed |
| `headers="*"` | Custom header abuse via plugin stack |
| Over-broad subdomain wildcards | `*.example.com` trusts every subdomain |

Also flag: upload buckets with private objects, conflicting multi-path policies, and loose XML accepted by old parsers.

### 3. Parse clientaccesspolicy.xml (Silverlight)

Treat as over-permissive when Silverlight grants look like:

- `domain uri="*"` (or equivalent open allow-from)
- `http-request-headers="*"`
- `resource path="/"` with `include-subpaths="true"`

Same residual-client caveats as Flash. Document exact `allow-from` / `grant-to` trees.

### 4. Contextual impact (do not overclaim)

1. No Flash/Silverlight consumer observed → often **informational residual** / trust-debt unless program scores leftover policies strictly.
2. Internal thin clients, kiosks, game launchers, AIR/desktop apps, or custom players still loading SWF raise real residual impact.
3. Wildcard `*` on public static assets → lower; on authenticated APIs, private media, admin hosts, or socket-to-sensitive ports → higher **if** a consumer exists.
4. Historical model: malicious SWF + ambient cookies on a victim plugin. Verify actual consumer before claiming live exploitability.

### 5. Remove-or-restrict checklist

**Prefer remove** when no legitimate plugin client remains:

1. Delete `crossdomain.xml` and `clientaccesspolicy.xml` from all origins/CDNs/path variants.
2. Remove unused `.swf`/`.xap` delivery, embeds, and socket policy listeners (e.g. port 843).
3. Purge CDN/cache; block re-publish via IaC, static templates, and default framework files.

**If a rare authorized client must stay:**

1. Exact partner domains only — no `domain="*"` / `uri="*"`.
2. Prefer `secure="true"` on HTTPS data hosts; document any `secure="false"`.
3. Least-privilege paths/ports/headers; avoid site-wide `/` + include-subpaths when possible.
4. Strictest workable `site-control`; monitor new buckets/subdomains for accidental open policies.

### 6. Verification

1. Re-fetch policies → 404 or tight allowlists only.
2. Spot-check sibling hosts and historical CDN URLs.
3. Grep deploy artifacts for residual policy XML and SWF references.
4. Track modern CORS separately — fixing CORS does not remove plugin policies and vice versa.

## Routing

| Need | Skill |
| --- | --- |
| Modern `Access-Control-*` / credentialed browser reads | `cors-cross-origin-misconfiguration` |
| Cross-window JS messaging | `postmessage-security` |
| Framing / UI redress (not policy XML) | `clickjacking` |
| Cookie flags on residual web sessions | `cookie-security-flags` |
| Host/API discovery for legacy files | `api-recon-and-docs` |
| Secure config change implementation | `code-quality-standards` |

## Output Checklist

- [ ] Hosts and exact policy URLs (HTTP/HTTPS) with status
- [ ] Classification: `*`, secure flags, ports, headers, site-control, Silverlight grant paths
- [ ] Residual consumers: SWF/XAP/embeds/sockets found or none observed
- [ ] Impact: residual/informational vs exploitable under current clients
- [ ] CDN/origin/path-scoped policy differences
- [ ] Remove-or-restrict recommendation (least privilege if keep)
- [ ] Post-fix verification and cache considerations
- [ ] Explicit non-overlap note vs modern CORS findings
- [ ] Redacted evidence; authorized scope stated

## Rules

- English findings only; label historical vs currently exploitable clearly.
- Wildcard `*` alone is not always critical on dead plugin stacks — require consumer context or program residual criteria.
- Do not claim Flash/Silverlight runs in modern browsers without a player or alternate runtime.
- Prefer removal of unused policies over complex allowlists.
- Authorized testing only; no malicious SWF distribution to third parties.
