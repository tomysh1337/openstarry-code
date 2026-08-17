---
name: registry-mirror-trust
description: >
  Design, assess, and harden trust in registry mirrors and pull-through caches
  for containers and packages (Harbor, Artifactory, Nexus, ECR/GHCR proxies,
  npm/PyPI/Maven mirrors). Use when clients resolve artifacts via a corporate
  mirror, when pull-through cache integrity is unclear, when TLS or signing at
  the mirror edge is weak, or when air-gapped/proxy registry policy must fail
  closed — hand namespace confusion to dependency-confusion; image Cosign/admission
  to container-image-signing; lockfile pins to dependency-pinning-strategies.
---

# Registry Mirror Trust

Make every install and image pull go through an **authorized mirror** whose
**upstream, integrity, and write path** you control. Internal hosting alone is
not trust: treat TLS, auth, cache poisoning, stale upstream, and who can **push**
or **overwrite** as first-class risks.

## When To Use

- Clients use a **pull-through cache**, proxy registry, or air-gapped sync
  (Harbor, Artifactory, Nexus, Verdaccio, cloud pull cache, package group repos)
- CI/dev points at a corporate registry, custom `GOPROXY`, Maven mirror, or
  `index-url` that is not the public origin
- Unclear whether the mirror verifies upstream TLS/signatures, rewrites digests,
  or allows anonymous/unscoped **push**
- Mentions: pull-through, registry mirror, proxy cache, Harbor, Nexus group,
  Artifactory remote, corporate npm/PyPI mirror, content trust at the edge

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Public vs private **name** confusion / dual index | `dependency-confusion` |
| Cosign/Sigstore sign + cluster admission | `container-image-signing` |
| Lockfiles, ranges, Renovate/Dependabot | `dependency-pinning-strategies` |
| Dockerfile layers / non-root | `dockerfile-best-practices` |
| CI graph, OIDC job perms | `ci-cd-pipeline-patterns` |
| Tokens, mirror admin creds, leak IR | `secrets-management-hygiene` |
| Config/policy code quality | `code-quality-standards` |

## Workflow

### 1. Inventory resolve path

1. List consumers: CI runners, dev machines, K8s nodes, offline promotion jobs.
2. Per ecosystem: configured registry/index host, auth, public fallback yes/no.
3. Table: ecosystem | client config | mirror host | mode | upstream | auth | notes.
4. Prefer **one authoritative mirror per ecosystem** in prod CI. Dual public +
   private without routing is a trust split (`dependency-confusion`).

### 2. Classify mirror mode

| Mode | Meaning | Trust focus |
| --- | --- | --- |
| **Pull-through / remote** | Cache on first pull | Upstream TLS, remote allowlist, cache immutability |
| **Hosted / local** | Org-owned only | Push rights, retention, overwrite policy |
| **Group / virtual** | Aggregates remotes + local | Resolve order; deny open public merge |
| **Air-gap sync** | Offline copy from blessed source | Sync identity, promotion, quarantine |

Note tag mutability and whether digests survive cache/sync end-to-end.

### 3. Transport and identity

1. TLS to the mirror in all prod clients; no insecure-registry shortcuts.
2. Enterprise-CA or pinned trust for the mirror hostname.
3. Anonymous pull only if policy allows; **push** via SSO/2FA or short-lived
   robot tokens, least privilege per pipeline.
4. Admin UI/API not world-reachable; MFA; audit config changes
   (`secrets-management-hygiene`).

### 4. Upstream and content integrity

1. **Allowlist** remotes (Hub, ghcr.io, Maven Central URL)—not open proxy.
2. Promote by **digest** (`@sha256:…`), not floating tags alone.
3. Preserve OCI referrers/signatures through cache; enforce verify/admission with
   `container-image-signing` where required.
4. Packages: lockfile integrity; fail if resolved host leaves mirror allowlist.
5. Cache controls: immutable-by-digest where possible; block tag overwrite on
   promoted repos; optional scan-before-serve quarantine.
6. Isolate upstream credentials; avoid shared Hub tokens across untrusted jobs.

### 5. Write path and fail-closed

1. Split **proxy-cache** (read-mostly) from **internal publish** projects.
2. Deny developer push to proxy namespaces; publish only via CI identity.
3. Air-gap: sync from verified bastion; promote by digest; log source + digest + job.
4. Missing auth or downed mirror must **not** silently fall back to public for
   internal-only names.

### 6. Verify

1. Capture resolve URL/host for a known package and image (verbose client/CI log).
2. Lab: non-allowlisted upstream pull → deny; unauthenticated push → deny.
3. Re-pull: same digest; signatures/referrers still present if expected.
4. Apply `code-quality-standards` to mirror IaC and client registry config.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Mirror/proxy/cache trust, pull-through, air-gap registry policy | **This skill** | — |
| Namespace / dual-index confusion | `dependency-confusion` | this for mirror routing |
| Cosign keyless sign/verify/admission | `container-image-signing` | this if mirror strips sigs |
| Lockfile pins / frozen install | `dependency-pinning-strategies` | mirror host in lock URLs |
| CI stages, robot OIDC to registry | `ci-cd-pipeline-patterns` | this for registry policy |
| Creds, robot tokens, admin secrets | `secrets-management-hygiene` | this |
| Dockerfile/image build hygiene | `dockerfile-best-practices` | this post-push |
| Implementation quality of configs | `code-quality-standards` | **always** on config |

**Hand-offs:** name confusion → `dependency-confusion`; image signature identity →
`container-image-signing`; pin/update bots → `dependency-pinning-strategies`.

## Output Checklist

- [ ] Consumer × ecosystem resolve path inventoried (host, auth, fallback)
- [ ] Mirror mode classified (proxy / hosted / group / air-gap)
- [ ] TLS + auth posture; push least-privilege
- [ ] Upstream allowlist; no open arbitrary-host proxy
- [ ] Digest-oriented promote; tag mutability policy stated
- [ ] Signature/referrer preservation or explicit gap → signing skill
- [ ] Fail-closed; no silent public fallback for internal names
- [ ] Lab verify: allowlist deny, digest stable, unauth push denied
- [ ] Hand-offs noted; secrets redacted; CQS on mirror/client config

## Scope And Authorization

- Owned orgs, labs, CTFs, or written SOW covering registry, CI, and client fleets.
- Do not reconfigure or probe third-party mirrors outside engagement scope.
- Prefer read-only inventory and lab dry-runs; gate purge, forced re-sync, or
  credential tests on explicit approval.
- Never use a corporate mirror as malware distribution in PoCs.
- Redact registry tokens, robot passwords, and unnecessary internal hostnames.
- Evidence over assumption: show resolve host, digest, and policy—not “internal
  therefore safe.”
