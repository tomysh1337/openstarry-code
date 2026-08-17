---
name: go-module-hygiene
description: >
  Keep Go modules healthy: go.mod/go.sum hygiene, replace directives, Minimum
  Version Selection (MVS), go mod tidy, retract, and private modules via
  GOPRIVATE/GOPROXY/GONOSUMDB. Use when go.mod, go.sum, replace directives,
  go mod tidy, MVS, retract, GOPRIVATE, private Go modules, module graph
  cleanup, or dependency version selection are in scope.
---

# Go Module Hygiene

Own **module graph and `go.mod`/`go.sum` correctness**: versions, `replace`,
`retract`, tidy, and private-module fetch. Prefer the repo’s module path, Go
version, and CI flags. Hand **Go source style** to `go-style-conventions`.

## When To Use

- Editing or reviewing **`go.mod` / `go.sum`**, module path, or `go` version line
- **`replace`** (local path, fork pin) or cleaning stale replaces
- **MVS** surprises: unexpected selected versions, “why this version?”
- **`go mod tidy`**, missing/extra `require`, sum mismatches
- Publishing or consuming **`retract`** for bad releases
- **Private modules**: `GOPRIVATE`, `GOPROXY`, `GONOSUMDB`, VCS auth
- Keywords: go.mod hygiene, go.sum, replace, exclude, retract, MVS, module graph,
  private module, go.work, pseudo-version, go get / go list -m

Do **not** use as primary for: Go style → `go-style-conventions`; code quality/
tests → `code-quality-standards`; multi-ecosystem registry confusion →
`dependency-confusion`; SBOM/provenance → `sbom-and-supply-chain`; secret
tokens/leak IR → `secrets-management-hygiene`.

## Repo Config First

Repository and org module policy **outrank** defaults below.

1. **`go.mod` / `go.sum`:** path, `go`/`toolchain`, `require`/`replace`/`exclude`/`retract`
2. **`go.work`:** multi-module workspace; do not assume single-module layout
3. **CI / Makefile:** exact tidy/verify commands, `GOTOOLCHAIN`, proxy env
4. **Private fetch:** `GOPRIVATE` globs, corporate `GOPROXY`, netrc/SSH/CI keys
5. **Replace policy:** local-dev only vs allowed committed pins vs release-forbidden
6. **Neighbors:** tools deps, vendoring (`-mod=vendor`), monorepo scripts, contrib docs

**Precedence:** Follow the repo. Flag machine-local `replace` paths, one-machine-only
sums, or public-proxy fetches of private paths.

## Workflow

### 1. Inventory

Read `go.mod` (nested modules too): path, Go version, direct vs indirect requires.
List every `replace`/`exclude`/`retract` with **why**. Note `go.work` members and
env: `GOPROXY`, `GOPRIVATE`, `GONOSUMDB`, `GOSUMDB`, `GOFLAGS`, `GOTOOLCHAIN`.

### 2. MVS

Go selects the **minimum** version of each module that satisfies all constraints
(**MVS**): the maximum of required minima wins.

1. Explain surprises: `go list -m -versions`, `go mod graph`, `go mod why -m`.
2. Prefer upgrading a **direct** require (or fixing an intermediate) over permanent `replace`.
3. v2+ import paths need the `/vN` major suffix matching the module path.
4. Do not hand-edit `go.sum`; regenerate via tidy / `go get`.

### 3. `go mod tidy` and verify

```bash
go mod tidy && go mod verify && go list -m all
go build ./... && go test ./...
```

Run tidy after import or version changes. Commit **`go.mod` and `go.sum` together**.
Keep tools via a documented pattern (`tools.go` + build tag), not fake prod imports.
If vendoring, refresh `vendor/` with the repo’s step. Repo CI mode (e.g.
`-mod=readonly`) must pass without rewriting `go.mod`. Report commands actually run.

### 4. `replace` (temporary by default)

| Use | Prefer | Avoid |
| --- | --- | --- |
| Local multi-module | `go.work`; path replace only if needed | Absolute laptop paths in shared branches |
| Fork pin | `replace … => fork vX.Y.Z` + issue/exit plan | Silent forever-pins with no upgrade path |
| Broken tag | Documented replace + tracking issue | Stacked replaces hiding graph debt |
| Releases | Published versions consumers can fetch | Replaces that only work in one checkout |

Every committed `replace` needs an owner and exit criteria. Strip debug replaces
before public tags unless the private multi-module tree documents them.

### 5. `retract`

```text
retract v1.2.3 // reason: broken API; use v1.2.4
retract [v1.2.0, v1.2.3] // reason: …
```

Ship a fix, then `retract` the bad range so default `go get`/MVS avoid it. Reasons
human-readable, non-secret. Explicit pins of retracted versions may still work—
document consumer migration for major breaks.

### 6. Private modules (`GOPRIVATE`)

Set **`GOPRIVATE`** globs for private path prefixes (skip public sum DB/proxy as
policy requires). Align **`GONOSUMDB`** / **`GOPROXY`** (direct VCS, corporate
proxy, or `direct` for private globs). Authenticate CI/devs to VCS via platform
secrets—not tokens in `go.mod`. Path must match a fetchable VCS/vanity path.
Registry confusion assessments → `dependency-confusion`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| go.mod/go.sum, replace, MVS, tidy, retract, GOPRIVATE | **This skill** | — |
| Go formatting, errors, naming, godoc, idioms | `go-style-conventions` | **hand off** after graph is sound |
| Code quality, tests, security hygiene | `code-quality-standards` | **always** on implementation |
| Private git tokens / leak IR | `secrets-management-hygiene` | this for `GOPRIVATE` layout |
| Cross-ecosystem namespace confusion | `dependency-confusion` | this for Go path/proxy |
| SBOM / upgrade gates / provenance | `sbom-and-supply-chain` | this for tidy/MVS |

- **`go-style-conventions`:** **hand off** all `.go` style; this skill owns the module graph only.
- **`code-quality-standards`:** apply when module work ships with app/tooling code.
- Keep **this skill primary** until `go.mod`/`go.sum` and fetch config are correct.

## Output Checklist

- [ ] Module path, Go/`toolchain`, and `go.work` inventoried
- [ ] MVS surprises explained (`go mod why` / graph); requires reviewed
- [ ] Each `replace` justified with exit plan; no absolute local paths shared
- [ ] `go mod tidy` + `go mod verify` run; `go.mod`/`go.sum` in sync; vendor if used
- [ ] Bad releases: fixed version + `retract` when publishing
- [ ] `GOPRIVATE`/proxy policy set; CI auth without secrets in git
- [ ] Build/tests or CI `-mod` checks pass
- [ ] Style → `go-style-conventions`; implementation → `code-quality-standards`

## Rules

- **Repo config first**; **tidy after dependency edits**; keep sums reproducible.
- Prefer **MVS-friendly upgrades** and **`go.work`** over permanent/local replaces.
- Never commit private tokens or `.netrc`. Do not claim tidy/verify/build without running them.
- **Hand off** language style to `go-style-conventions`; this skill owns modules only.
