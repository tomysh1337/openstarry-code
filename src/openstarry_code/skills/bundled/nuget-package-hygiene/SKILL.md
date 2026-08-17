---
name: nuget-package-hygiene
description: >
  Keep NuGet dependency graphs healthy: PackageReference, Central Package
  Management, packages.lock.json, nuget.config sources, Package Source Mapping,
  restore locked mode, and vulnerable/deprecated package cleanup. Use when
  csproj PackageReference, Directory.Packages.props, packages.lock.json,
  nuget.config, floating versions, private NuGet feeds, PackageSourceMapping,
  restore --locked-mode, or .NET package graph hygiene are in scope.
---

# NuGet Package Hygiene

Own **.NET package graph and restore correctness**: manifests, central versions,
lockfiles, feed config, and known-bad package cleanup. Prefer the repo’s TFMs,
SDK, and CI restore flags. Hand **C# source style** to `csharp-style-conventions`.

## When To Use

- Editing or reviewing **`PackageReference`**, `packages.config`, or package versions
- **Central Package Management** (`Directory.Packages.props`, `ManagePackageVersionsCentrally`)
- **`packages.lock.json`**, floating versions (`*`, `1.2.*`), restore drift
- **`nuget.config`**: package sources, credentials layout, clear-text warnings
- **Package Source Mapping** / multi-feed resolve order (internal + nuget.org)
- Cleaning **vulnerable, deprecated, or unused** packages; transitive version pins
- Keywords: NuGet hygiene, PackageReference, CPM, packages.lock.json, nuget.config,
  PackageSourceMapping, locked-mode restore, `dotnet list package`, NU190x

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| C# language/style | `csharp-style-conventions` |
| Multi-ecosystem pin/bot policy | `dependency-pinning-strategies` |
| Registry namespace confusion (NuGet IDs) | `dependency-confusion` |
| SBOM / SCA inventory / provenance | `sbom-and-supply-chain` |
| Pipeline layout / fork secrets | `ci-cd-pipeline-patterns` |
| Implementation quality/tests | `code-quality-standards` |

## Repo Config First

Repo and org NuGet policy **outrank** defaults below.

1. **Project system:** SDK-style `PackageReference` vs legacy `packages.config`
2. **CPM / props:** `Directory.Packages.props`, `Directory.Build.props`, solution filters
3. **Lockfiles:** `packages.lock.json` / `RestorePackagesWithLockFile`
4. **`nuget.config`:** hierarchy, enabled sources, mapping, credentials
5. **CI restore:** `dotnet restore --locked-mode`, cache keys, SDK/`global.json`
6. **Neighbors:** private feed auth, Dependabot/Renovate for NuGet, vuln gates

**Precedence:** Follow the repo. Flag machine-local feeds, committed clear-text
API keys, configs that leave internal IDs on public fallback, or lock drift.

## Workflow

### 1. Inventory

List solutions/projects, TFMs, and package style. Read `Directory.Packages.props`
if CPM is on. Collect hierarchical `nuget.config` (nearest wins): sources, mapping,
lockfiles, and SDK from `global.json`.

### 2. Manifest and version policy

| Kind | Version posture | Notes |
| --- | --- | --- |
| **App / service** | Pin directs (or CPM) + lockfile | Reproducible restore |
| **Library (published)** | Ranges only if intentional; lock CI | Consumer upgrade room |
| **Internal package** | Mapped private feed only | Pair with `dependency-confusion` |
| **Floating** (`*`, `1.*`) | Avoid on deployables | Non-reproducible restore |

Prefer **PackageReference** over `packages.config` for new work. Use **CPM** when
multi-project version drift hurts; keep one owner for bumps.

### 3. Lockfiles and restore

```bash
dotnet restore --force-evaluate   # regenerate lock when intentional
dotnet restore --locked-mode      # CI: fail on lock drift
dotnet list package --outdated
dotnet list package --vulnerable
dotnet list package --deprecated
```

Enable **`RestorePackagesWithLockFile`** for deployables; commit `packages.lock.json`.
CI uses **`--locked-mode`** (or fail-on-diff). Review lock diffs (IDs, hashes,
sources). Do not hand-edit lock JSON—regenerate via restore.

### 4. Feeds and Package Source Mapping

Prefer one authoritative strategy: private proxy **or** explicit mapping—not
accidental multi-source max-version. Map internal prefixes to private sources
only; map public packages to nuget.org/proxy. Disable unused sources; avoid
personal folder feeds that change team restore. Credentials via CI secret store /
credential provider—never clear-text keys in git. Confusion → `dependency-confusion`.

### 5. Graph cleanup

Remove unused PackageReferences after build/test proof. Fix **NU1901–NU1904** and
deprecated packages with upgrades or time-boxed waivers (`sbom-and-supply-chain`
for org SCA). Prefer upgrading a **direct**/CPM pin over forever overrides.
Align family majors (e.g. Microsoft.Extensions.*, EF Core) across the solution.
After edits: locked restore, build, test; commit props + lock together.

### 6. Verify

Fresh `--locked-mode` restore; expected hosts only. Outdated/vulnerable triaged.
No feed secrets in git. Style → `csharp-style-conventions`; quality →
`code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| PackageReference, CPM, lockfile, nuget.config, mapping, restore hygiene | **This skill** | — |
| Cross-ecosystem pin/bot strategy | `dependency-pinning-strategies` | this for NuGet lock/restore |
| NuGet ID / feed namespace confusion | `dependency-confusion` | this for mapping/config |
| SBOM, CVE program, provenance | `sbom-and-supply-chain` | this for restore graph |
| CI job graph / feed secret injection | `ci-cd-pipeline-patterns` | this for restore flags |
| C# source style | `csharp-style-conventions` | **hand off** after graph is sound |
| Implementation quality | `code-quality-standards` | **always** on shipped changes |

Keep **this skill primary** until manifests, lockfiles, and feed config are correct.

## Output Checklist

- [ ] Projects, TFMs, PackageReference vs packages.config, CPM inventoried
- [ ] Repo `nuget.config` hierarchy, sources, and mapping reviewed
- [ ] Version pins intentional; no floating `*` on deployable restore paths
- [ ] `packages.lock.json` committed where required; CI `--locked-mode`
- [ ] Internal IDs mapped; no silent public fallback for private names
- [ ] No clear-text feed credentials; CI uses secret/credential provider
- [ ] Vulnerable/deprecated/unused triaged; props + lock updated together
- [ ] Fresh locked restore + build/tests pass; lock diffs reviewed
- [ ] Routed: confusion → `dependency-confusion`; SBOM → `sbom-and-supply-chain`;
      style → `csharp-style-conventions`; quality → `code-quality-standards`
