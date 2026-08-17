---
name: argo-cd-rbac-basics
description: >
  Argo CD RBAC for owned or authorized GitOps control planes: global policy.csv
  in argocd-rbac-cm, Casbin p/g rules, SSO group scopes, AppProject roles, default
  policy, and least-privilege sync/delete/admin boundaries. Use when designing or
  reviewing Argo CD roles, mapping OIDC/LDAP groups to policies, debugging
  permission denied on applications/clusters/repos, tightening admin, or
  separating project-scoped access — not for third-party Argo CD abuse or generic
  Kubernetes cluster-admin outside Argo CD’s RBAC model.
---

# Argo CD RBAC Basics

Design and review **Argo CD RBAC** so users and groups get least privilege on
applications, projects, repos, clusters, and admin APIs. **Owned / contracted
GitOps platforms only.**

## When To Use

- Editing or reviewing `argocd-rbac-cm` (`policy.csv`, `policy.default`, `scopes`)
- Mapping SSO (OIDC, SAML, Dex, LDAP groups) subjects into Argo CD roles
- Custom roles: read-only, sync-only, project admin, no-delete, no-cluster-create
- `AppProject` roles, JWT tokens, project-scoped vs global policy
- UI/API permission denied on applications, logs, exec, certificates, accounts
- Keywords: Argo CD RBAC, policy.csv, casbin, `argocd-rbac-cm`, AppProject role

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Helm chart values / privileged pods packaging | `helm-chart-security` |
| Live cluster RBAC, secrets dump, can-i (broad K8s) | `kubernetes-pentesting` |
| Org secret storage, git secrets, rotation IR | `secrets-management-hygiene` |
| Controllers, CRDs, tests, IaC code quality | `code-quality-standards` |
| Generic CI/CD pipeline design (non-Argo RBAC) | `ci-cd-pipeline-patterns` |

## Workflow

### 1. Inventory identity and policy surfaces

1. Argo CD version, install method (Helm/manifests/Operator), HA vs single.
2. Auth: local accounts vs SSO; IdP group claim (often `groups`).
3. `argocd-rbac-cm`: `policy.csv`, `policy.default`, `scopes`; optional
   `policy.matchMode` (glob vs regex per version docs).
4. AppProjects, local users, admin bootstrap; who may edit the RBAC ConfigMap.

### 2. Model subjects, roles, and objects

Argo CD uses a **Casbin**-style CSV:

| Rule | Form | Meaning |
| --- | --- | --- |
| **p** | `p, <sub>, <res>, <act>, <obj>, <effect>` | Permission |
| **g** | `g, <user-or-group>, <role>` | Role assignment |

Common **resources**: `applications`, `applicationsets`, `clusters`,
`repositories`, `projects`, `accounts`, `certificates`, `gpgkeys`, `logs`,
`exec`, `extensions`. **Actions**: `get`, `create`, `update`, `delete`, `sync`,
`override`, `action`, `invoke` (version-dependent; verify your release).

Objects are often `proj/name` (apps) or `*` wildcards. Prefer **named projects**
and explicit app patterns over global `*/*` for writers.

### 3. Global policy.csv and defaults

1. Set `scopes: '[groups, email]'` (or org claim) so IdP groups match `g` rows.
2. Prefer `policy.default: role:readonly` or empty+explicit `g`. Never leave
   broad prod default as `role:admin`.
3. Built-ins: `role:admin` (full), `role:readonly` (get). Custom example:

```csv
p, role:dev-sync, applications, get, dev/*, allow
p, role:dev-sync, applications, sync, dev/*, allow
p, role:dev-sync, logs, get, dev/*, allow
g, my-org:team-dev, role:dev-sync
```

4. Deny-by-omission: separate `delete`/`override` from `sync`. Restrict
   `clusters`, `repositories`, `projects`, `accounts`, `exec`.
5. Local `admin`: disable after SSO, or break-glass with vaulted password and
   audit (`secrets-management-hygiene`).

### 4. AppProject-scoped RBAC

1. Each `AppProject` defines allowed source repos, destinations, and cluster
   resources — **orthogonal** to who may act.
2. Project `roles[]`: name, `policies` (p-lines), `groups`, optional JWT for CI.
3. Project roles for team isolation; global policy for platform admins and
   cross-project read.
4. CI bots: project-scoped JWT or dedicated SSO SA — not shared admin tokens.
   Token secrets → `secrets-management-hygiene`.

### 5. Validate and operate (authorized)

1. Map real IdP group strings (case/prefix) to `g` lines; test with a non-admin.
2. Confirm UI/API: sync allowed project; deny other project, cluster create,
   needless `exec`.
3. Non-prod first; protect GitOps-managed policy.csv like cluster-admin.
4. Audit `role:admin`, cluster wildcards, and `exec`. Code →
   `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Argo CD policy.csv, scopes, AppProject roles, SSO map | **This skill** | — |
| Helm packaging of Argo CD / values secrets | `helm-chart-security` | this skill |
| Live K8s RBAC / secret exposure beyond Argo policy | `kubernetes-pentesting` | this skill |
| Admin passwords, repo creds, project JWTs in git | `secrets-management-hygiene` | this skill |
| Pipeline layout without Argo RBAC detail | `ci-cd-pipeline-patterns` | this if Argo |
| Manifests, controllers, tests, policy generators | `code-quality-standards` | always on code |

**Ownership:** **Argo CD application/API RBAC** (global + AppProject). Cluster
K8s authorization outside Argo’s model → `kubernetes-pentesting` / platform IAM.

## Output Checklist

- [ ] Authorization recorded (owned Argo CD / cluster / projects only)
- [ ] Version, SSO/IdP, scopes, and policy ConfigMap inventoried
- [ ] policy.default is least privilege (not casual admin)
- [ ] p/g rules reviewed: resources, actions, object patterns, effects
- [ ] Groups/users mapped; IdP claim strings verified in non-prod
- [ ] AppProjects: destinations/sources + project roles/JWT scoped
- [ ] Writers lack needless delete/override/exec/cluster/repo admin
- [ ] Local admin break-glass justified or disabled; secrets redacted
- [ ] CI uses project-scoped identity, not shared cluster admin
- [ ] Hand-offs: Helm / K8s / secrets / code skills as above

## Scope And Authorization

- **In scope:** Argo CD you operate or are contracted to harden; review of
  `argocd-rbac-cm` and AppProjects; controlled policy changes in lab/non-prod;
  org SSO group mapping under change control.
- **Out of scope:** third-party Argo CD abuse; stolen-token elevation outside ROE;
  mass prod policy flips without a change window; substituting Argo RBAC for
  Kubernetes NetworkPolicy or cloud IAM.
- Prefer read-only export of policy.csv before edits. Redact SSO tokens, project
  JWTs, repo credentials, and local passwords from reports.
- Gate `exec`, cluster registration, and global admin. Secrets →
  `secrets-management-hygiene`; live cluster abuse only when authorized via
  `kubernetes-pentesting`.
