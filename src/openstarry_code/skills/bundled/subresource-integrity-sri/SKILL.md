---
name: subresource-integrity-sri
description: >
  Assess and implement Subresource Integrity (SRI) for script and link tags:
  sha384 digests, crossorigin, CDN trust, hash rotation, integrity mismatches,
  and service-worker edge cases. Use when reviewing third-party CDN scripts,
  missing integrity attributes, broken SRI after deploys, or hardening static
  asset delivery on authorized applications.
---

# Subresource Integrity (SRI) — Scripts, Styles, And CDN Trust

Browser **Subresource Integrity** binds external `script`/`link` resources to
digests so a compromised CDN, cache poison, or silent swap cannot run under the origin.

## Scope And Authorization

- Authorized apps, owned codebases, labs, CTFs, and program-scoped targets only.
- Prefer HTML/config review and controlled browser checks; do not attack public CDNs.
- Model supply-chain risk from **your** inventory; redact secrets; keep hash evidence separate.

## When To Use

- Third-party or multi-origin JS/CSS loads without `integrity` (or partial coverage).
- Deploy breaks: console **Failed to find a valid digest** / resource blocked.
- Hash rotation after library upgrades; CDN supply-chain hardening reviews.
- Service workers or injectors rewrite asset URLs/bodies and SRI fails or vanishes.
- Keywords: SRI, `integrity=`, sha256/sha384/sha512, `crossorigin="anonymous"`, CDN pin.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Mixed content (HTTP on HTTPS page) | mixed-content notes + `nginx-security-headers` (HTTPS/HSTS) |
| CSP policy, nonces, CSP bypass | `content-security-policy-bypass` (+ XSS skills) |
| XSS / injected script tags | `xss-cross-site-scripting` / `injection-checking` |
| Package registry confusion | `dependency-confusion` |

## Core Model

```text
Fetch body → SHA-256/384/512 → base64 → integrity="algo-digest"
No match → browser blocks execute/apply
Cross-origin SRI needs CORS fetch → crossorigin on tag + ACAO on CDN
```

| Piece | Rule of thumb |
| --- | --- |
| **Elements** | `script[src]`, `link[rel=stylesheet]` (and other SRI-capable link fetches) |
| **Algorithm** | Prefer **sha384** (optionally multi: `sha384-… sha512-…`) |
| **crossorigin** | Required cross-origin (usually `anonymous`); same-origin often omits |
| **CDN trust** | Pins **content**, not publisher ID — still need HTTPS + pinned URL |
| **Rotation** | Any byte change invalidates digests; pin versions, not `latest` |

## Workflow

1. **Inventory** — Parse templates/bundlers for `script src` / `link href`. Classify
   first-party vs third-party; versioned paths vs floating tags.

2. **Audit markup**

   ```html
   <script src="https://cdn.example/lib.min.js"
           integrity="sha384-BASE64DIGEST" crossorigin="anonymous"></script>
   <link rel="stylesheet" href="https://cdn.example/lib.min.css"
         integrity="sha384-BASE64DIGEST" crossorigin="anonymous">
   ```

   Missing `integrity` on cross-origin script/style → supply-chain gap.
   `integrity` without `crossorigin` cross-origin → SRI often fails (opaque response).
   Space-separated digests: any match succeeds.

3. **Generate digests** from **exact bytes** the browser receives:

   ```bash
   openssl dgst -sha384 -binary lib.min.js | openssl base64 -A
   ```

   Format: `sha384-` + standard base64 (not hex). Re-hash after CDN transforms.

4. **CDN / CORS** — Public static needs ACAO compatible with `crossorigin="anonymous"`
   (often `*`). HTTPS only for production third-party assets. Prefer versioned URLs.

5. **Mismatch diagnosis**

   | Symptom | Likely cause |
   | --- | --- |
   | Integrity error; script blocked | Wrong hash/file; CDN mutated body |
   | Same-origin OK, cross-origin fail | Missing `crossorigin` or CDN CORS |
   | Intermittent | A/B asset, regional skew, partial deploy |
   | Fail after bump | Minify/content change — rotate hash, do not strip SRI |

   Capture URL, status, ACAO, local digest vs attribute, console text.

6. **Rotation** — Pin versions in lockfile/vendor path. CI: build/download →
   compute SRI → inject or fail on drift. Prefer new content-addressed/versioned
   URL + atomic HTML update over mutating immutable URLs in place.

7. **Service worker edge cases** — Cached bodies must match HTML digests; stale
   SW + new hashes → permanent block until SW updates. Precache the same bytes
   hashed into SRI. Avoid SW body rewrites of third-party responses unless digests
   are recomputed. Offline shells that inject scripts without integrity reintroduce
   CDN risk; SW-generated HTML must still emit correct attributes.

8. **Layered controls** — CSP `script-src`/`style-src` complements SRI → hand off
   policy/bypass to `content-security-policy-bypass`. Mixed content is separate
   from SRI → HTTPS/HSTS. XSS injecting tags bypasses SRI on attacker URLs → XSS skill.

9. **Remediate** (with `code-quality-standards`) — SRI + `crossorigin` on cross-origin
   script/style; self-host critical JS when feasible; automate digests in build;
   alert on SRI/CSP violation spikes if reporting exists.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| SRI tags, sha384, CDN pins, rotation, SW mismatch | **This skill** | — |
| CSP allowlists / nonces / bypass | `content-security-policy-bypass` | this for tag digests |
| Mixed content / HTTPS edge / HSTS | `nginx-security-headers` + mixed-content notes | this if SRI missing |
| XSS injecting scripts | `xss-cross-site-scripting` | this for static-tag defense |
| Implement build injectors / templates | `code-quality-standards` | always on code changes |

## Output Checklist

- [ ] Asset inventory (origin, version pin, purpose)
- [ ] Per asset: `integrity` algo, `crossorigin`, HTTPS
- [ ] Recomputed digest matches live bytes (method recorded)
- [ ] Cross-origin CORS / `crossorigin` correctness
- [ ] Mismatch root cause and fix (not removal of SRI)
- [ ] Rotation/CI process; no floating `latest` under SRI
- [ ] Service worker / precache interaction reviewed
- [ ] Hand-offs: CSP, mixed content, XSS residual risk
- [ ] Scope recorded; secrets/URLs redacted as required

## Rules

- Prefer **sha384**; verify response bodies, not only source trees.
- Cross-origin SRI needs **`crossorigin` + CDN CORS**.
- Never strip `integrity` to “fix” prod without a tracked hash update.
- SRI pins content — combine with HTTPS, version pins, and CSP.
- Authorized hardening and assessment only.
