---
name: static-asset-fingerprinting
description: >
  Design content-hashed static asset filenames, long-lived Cache-Control immutable
  headers, atomic deploy order, and safe HTML/manifest updates so browsers never
  pair new markup with missing or stale bundles. Use when bundler content hashes,
  fingerprinted assets, immutable cache headers, deploy race white screens, stale
  HTML referencing old JS/CSS, or versioned static CDN paths. Hand CDN key/Vary
  design to cdn-cache-key-design; hand integrity digests to subresource-integrity-sri.
---

# Static Asset Fingerprinting

Engineering design for **content-addressed static assets** (JS, CSS, fonts, images
from the build): hash in the URL, cache forever at the edge, and deploy so HTML
never references objects that are not yet public. Prefer the repo bundler and CDN
layout over ad-hoc `?v=` cache-busters.

## When To Use

- Configuring **content hashes in filenames** (`app.[contenthash].js`, Vite/webpack
  /Rollup/esbuild, hashed CSS/font URLs)
- Setting **`Cache-Control: public, max-age=…, immutable`** on fingerprinted paths
- Fixing **post-deploy white screens / chunk load errors** (stale HTML vs assets)
- Planning **atomic deploys**: upload new hashed files before flipping HTML/SSR
- Coordinating **SRI digests** with hash-in-filename rotation
- Mentions: contenthash, fingerprinted assets, immutable cache, chunk load error,
  stale shell, asset manifest, long-term caching, static CDN versioning

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| CDN key, Vary, query allowlist, purge tags | `cdn-cache-key-design` |
| `integrity=` / sha384 / crossorigin on tags | `subresource-integrity-sri` |
| App/Redis TTL, stampede, cache-aside | `caching-strategies` |
| CI stages that build/publish artifacts | `ci-cd-pipeline-patterns` |
| Implementation quality baseline | `code-quality-standards` |

## Repo Config First

Repo bundler, CDN path rules, and deploy scripts **outrank** defaults below.

1. **Bundler:** Vite, webpack, Rollup, esbuild, Parcel, Next/Nuxt — reuse existing
   `[contenthash]` / `assetsDir` conventions
2. **HTML/SSR entrypoints:** templates, shells, SW precache, manifest.json, import maps
3. **CDN / origin paths:** `/static/`, `/_next/static/`, bucket prefixes, asset host
4. **Edge headers:** `Cache-Control` rules for static vs HTML by path prefix
5. **Deploy pipeline:** upload order, HTML publish, purge, blue/green or dual-bucket
6. **SRI/CSP tooling:** if digests inject in CI, align with filename hashing
7. **Neighbors:** copy mature apps’ hash length, publicPath, retention policy

**Precedence:** Follow the repo. Flag non-hashed files with year-long TTL, HTML
with `immutable`, or HTML published before hashed objects exist.

## Workflow

1. **Fingerprint content, not deploy time.**
   - Put a **content hash** in the **filename or immutable path segment** so any
     byte change yields a new URL
   - Prefer path hash over `?v=timestamp` (query often stripped/weakly keyed —
     → `cdn-cache-key-design`)
   - Keep **HTML, SSR, and SW precache manifests** short-TTL / must-revalidate;
     never mark documents `immutable`

2. **Set cache headers by path class.**

   | Class | Example | Cache-Control sketch |
   | --- | --- | --- |
   | Fingerprinted static | `/assets/app.a1b2c3de.js` | `public, max-age=31536000, immutable` |
   | HTML / shell | `/`, `/index.html`, SSR | `no-cache` or short max-age + revalidate |
   | Unhashed “latest” | `/static/app.js` | Short TTL or avoid; no `immutable` |
   | SW / precache list | `sw.js`, workbox manifest | Short revalidation; coordinated updates |

   `immutable` is safe **only** when the URL changes whenever bytes change.

3. **Deploy atomically (order matters).**

   ```text
   build → upload NEW hashed objects → verify GET 200 → publish HTML/SSR/manifest
            that references those hashes → (optional) purge HTML only
   ```

   - Never delete/overwrite old hashed files until retention expires and traffic
     no longer references them (tabs, SW, emails, CDN POPs)
   - Blue/green: flip HTML only after assets are warm in all required regions

4. **Diagnose stale HTML ↔ asset skew.**

   | Symptom | Likely cause |
   | --- | --- |
   | ChunkLoadError / 404 on `*.[hash].js` | HTML new; assets missing or wrong publicPath |
   | Users stuck on old UI | HTML long-cached / SW precache not bumped |
   | Intermittent wrong bundle | Non-atomic flip; mixed old/new HTML at edge |
   | SRI failure after deploy | Digest not rotated — → `subresource-integrity-sri` |

5. **SRI interaction.** Hash-in-filename avoids reusing one URL for new bytes;
   **SRI** still pins exact digests. Recompute integrity on each emit; do not
   mutate a hashed URL’s body. Deep audit → `subresource-integrity-sri`.

6. **Retention.** Keep N prior generations; GC only URLs absent from current and
   recent manifests. Never empty-bucket-then-upload.

7. **Verify.** HTML → each script/link 200 + immutable headers; cold client OK;
   optional canary before global HTML switch.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Content hashes, immutable TTL, atomic static deploy, stale HTML | **This skill** | — |
| CDN key, Vary, query allowlist, edge purge tags | `cdn-cache-key-design` | this for hashed path policy |
| SRI `integrity` / crossorigin / digest rotation | `subresource-integrity-sri` | this for hash-in-filename pairing |
| App L1/L2 Redis keys and stampede | `caching-strategies` | this for browser/CDN static only |
| Build/publish pipeline stages | `ci-cd-pipeline-patterns` | this for asset/HTML order |
| Bundler/deploy quality and tests | `code-quality-standards` | **always** |

- **`cdn-cache-key-design`:** *what enters the edge key* (host, query, cookies,
  Vary). **This skill** owns content-addressed filenames, immutable headers, deploy order.
- **`subresource-integrity-sri`:** tag digests/CORS/mismatches; pair when HTML has
  hashed URLs and `integrity`.
- **`code-quality-standards`:** fail CI if manifest refs missing artifacts; no secrets
  in asset paths/deploy logs.

## Output Checklist

- [ ] Bundler emits content hashes for JS/CSS/static chunks
- [ ] Fingerprinted paths: long `max-age` + `immutable`; HTML revalidated
- [ ] No `immutable` / multi-year TTL on unhashed or document URLs
- [ ] Deploy order: new assets live → then HTML/SSR/manifest flip
- [ ] Old hashed objects retained; GC policy documented
- [ ] publicPath / CDN host matches runtime HTML references
- [ ] Stale-HTML symptoms classified (404 vs SW vs long HTML cache)
- [ ] SRI rotated with content if used → `subresource-integrity-sri` for deep work
- [ ] Edge key/Vary questions paired with `cdn-cache-key-design`
- [ ] Post-deploy: HTML → asset 200 + correct Cache-Control
- [ ] `code-quality-standards` on bundler config, deploy scripts, tests
