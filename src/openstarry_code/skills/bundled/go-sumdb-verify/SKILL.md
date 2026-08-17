---
name: go-sumdb-verify
description: >
  Verify Go module checksums against the public checksum database (sumdb):
  GOSUMDB, sum.golang.org, go.sum integrity, go mod verify, tiled hashes,
  and GONOSUMDB/GOPRIVATE exceptions. Use when sumdb, GOSUMDB, go.sum
  mismatch, SECURITY ERROR checksum, go mod verify, sum.golang.org,
  notary.google.com, GONOSUMDB, or module hash verification fail in CI.
---

# Go Sumdb Verify

Own **checksum-database (sumdb) verification** for Go modules: when the
toolchain consults `GOSUMDB`, how `go.sum` relates to sumdb tiles, diagnosing
hash mismatches, and safe private-module exceptions. Prefer the repo’s proxy
and CI env. Hand tidy/replace/MVS to `go-module-hygiene`; multi-ecosystem pins
to `dependency-pinning-strategies`.

## When To Use

- **`go.sum` SECURITY ERROR**, unexpected hash, or sumdb lookup failure
- Configuring or reviewing **`GOSUMDB`**, **`GONOSUMDB`**, **`GOPRIVATE`**
- CI fails on **`go mod verify`**, sumdb network errors, or offline builds
- Auditing whether checksums are **enforced** vs silently skipped (`off`)
- Keywords: sum.golang.org, notary, checksum database, module hash, h1:,
  tile, note key, sumdb protocol, go.sum drift, proxy vs sumdb

Do **not** use as primary for: tidy/replace/MVS → `go-module-hygiene`;
govulncheck → `go-govulncheck-workflow`; multi-lang locks →
`dependency-pinning-strategies`; SBOM → `sbom-and-supply-chain`; style →
`go-style-conventions`.

## Repo Config First

Repository and org module-fetch policy **outrank** defaults below.

1. **`go.mod` / `go.sum`:** committed together; no hand-edited hashes
2. **Env / CI:** `GOPROXY`, `GOSUMDB`, `GONOSUMDB`, `GOPRIVATE`
3. **Private path globs:** real VCS prefixes only (not over-broad `*`)
4. **Air-gapped / offline:** vendor, module cache mirrors, sumdb access
5. **Corporate proxy:** serves sumdb vs needs `direct`/org mirror
6. **Neighbors:** `go.work`, `-mod=readonly`/`vendor`, Makefile targets

**Precedence:** Follow the repo. Flag `GOSUMDB=off`, empty sumdb, or
`GONOSUMDB=*` that disables verification for public modules without a written
exception.

## Workflow

### 1. Mental model

| Piece | Role |
| --- | --- |
| **`go.sum`** | Local module version content hashes (`h1:…`) |
| **`GOSUMDB`** | Checksum DB + public key (default `sum.golang.org`) |
| **Sumdb** | Global notary; clients verify signed tiles |
| **`GOPROXY`** | Download path; **not** a substitute for sumdb |
| **`GONOSUMDB` / `GOPRIVATE`** | Path prefixes that skip sumdb (often proxy too) |

Proxy delivers modules; **sumdb authenticates** public-module hashes. Never
treat “downloaded successfully” as “hash verified.”

### 2. Inventory verification posture

```bash
go env GOSUMDB GOPROXY GONOSUMDB GOPRIVATE
go mod verify
```

1. Record default vs overridden `GOSUMDB` (name + key if custom).
2. Justify each `GONOSUMDB`/`GOPRIVATE` glob; keep public paths verified.
3. Align CI and developer machines on the same policy.
4. Offline/vendor builds must still match committed `go.sum`.

### 3. Local and CI verify

```bash
go mod download && go mod verify && go list -m all
```

1. **`go mod verify`** checks cache against `go.sum` (and sumdb when enabled).
   Fail closed in CI on any mismatch.
2. After upgrades: tidy / `go get`, re-verify; commit **`go.mod` + `go.sum`**
   together. Never hand-edit `h1:` lines.
3. Prefer `-mod=readonly` (or vendor) in release jobs so sums cannot rewrite
   silently during build.

### 4. Diagnose common failures

| Symptom | Likely cause | Action |
| --- | --- | --- |
| SECURITY ERROR / hash mismatch | Tamper, bad cache, sum drift | Diff `go.sum`; clear bad cache; re-download; do not delete sums blindly |
| Sumdb unreachable | Network, firewall, bad `GOSUMDB` | Fix path or org mirror; avoid default `off` |
| Private module sumdb miss | Path not in private globs | Precise `GOPRIVATE`/`GONOSUMDB` |
| Local OK, CI fails | Divergent env or dirty cache | Align `go env`; pin Go; full `go.sum` |
| Vendor drift | Stale `vendor/` | Refresh with repo step; re-verify |

If mismatch persists across clean cache + trusted proxy + sumdb, treat as a
**supply-chain incident**: stop the bad version, pin known-good, escalate.

### 5. Exceptions and evidence

1. **`GOSUMDB=off`:** break-glass/labs only; never default CI for public deps.
2. **`GONOSUMDB`:** private modules only; review globs in PR like code.
3. Custom sumdb: document endpoint, key, ownership; test key rotation.
4. Air-gap: cache or vendor + locked `go.sum`; still run `go mod verify`.
5. Record redacted `go env`, commands, failing module@version, sumdb consulted
   or not, and fix. Graph debt → `go-module-hygiene`; SBOM →
   `sbom-and-supply-chain`. Redact tokens from proxy/VCS debug logs.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| sumdb, GOSUMDB, go mod verify, hash SECURITY ERROR | **This skill** | — |
| tidy, replace, MVS, retract, private path layout | `go-module-hygiene` | this for sum policy |
| govulncheck / Go vulndb CI gate | `go-govulncheck-workflow` | after sums verify |
| Cross-lang lockfile pin strategy | `dependency-pinning-strategies` | this for Go sums |
| SBOM / provenance inventory | `sbom-and-supply-chain` | this for hash evidence |
| Registry namespace confusion | `dependency-confusion` | this for sumdb checks |
| CI job layout / caches | `ci-cd-pipeline-patterns` | this for verify step |
| Implementation quality | `code-quality-standards` | **always** on CI/scripts |

Keep **this skill primary** until verification env, `go.sum`, and CI verify
behavior are correct; then hand graph or vuln work to neighbors.

## Output Checklist

- [ ] Repo `go.mod`/`go.sum`, proxy, and sumdb env inventoried first
- [ ] `GOSUMDB` / `GONOSUMDB` / `GOPRIVATE` justified; no silent `off`/`*`
- [ ] `go mod verify` run (local and/or CI); command and result recorded
- [ ] Mismatches triaged without blind sum deletion; cache/proxy path clear
- [ ] CI uses readonly/vendor posture; `go.mod`+`go.sum` committed together
- [ ] Private globs precise; public modules still sumdb-verified
- [ ] Persistent sumdb disagreement escalated as supply-chain incident
- [ ] Hand-offs: `go-module-hygiene`, `go-govulncheck-workflow`,
      `dependency-pinning-strategies`, `sbom-and-supply-chain`,
      `code-quality-standards` as needed
- [ ] Secrets/tokens redacted from env dumps and logs
