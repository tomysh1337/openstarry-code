---
name: opa-gatekeeper-basics
description: >
  OPA Gatekeeper policy-as-code for owned Kubernetes clusters: ConstraintTemplates
  (Rego + CRD schema), Constraints (match, parameters, enforcementAction), and
  audit vs deny behavior. Use when authoring or reviewing Gatekeeper templates
  and constraints, rolling out dryrun/warn before deny, triaging constraint
  violations, or separating admission enforce from periodic audit — not for
  generic OPA outside Gatekeeper or unauthorized cluster policy attacks.
---

# OPA Gatekeeper Basics (ConstraintTemplates / Constraints)

Operate and review **OPA Gatekeeper**: reusable **ConstraintTemplates**,
**Constraints**, and **audit** vs **deny** on owned/authorized clusters only.

## When To Use

| Situation | Direction |
| --- | --- |
| Author/review `ConstraintTemplate` (CRD schema + Rego `violation`) | **This skill** |
| Instantiate `Constraint` kinds: match, params, labels, namespaces | **This skill** |
| Choose `enforcementAction`: deny vs dryrun vs warn; audit findings | **This skill** |
| Roll out policy: inventory → dryrun/audit → fix → enforce (deny) | **This skill** |
| Triage `Constraint` status / `violations` and admission rejections | **This skill** |
| Library policies (K8sPSP*, required labels, repo/image allowlists) | **This skill** |
| Pod securityContext / PSA labels only (no Gatekeeper CRDs) | `kubernetes-pod-security` |
| Cluster RBAC, secrets, broad K8s attack surface | `kubernetes-pentesting` |
| NetworkPolicy / CNI L3-L4 | `kubernetes-network-policy` |
| Manifest quality, tests, CI gates (not Gatekeeper semantics) | `code-quality-standards` |

Do **not** use as primary for standalone OPA (non-Gatekeeper), Kyverno-only
workflows, or live policy changes on clusters you do not own or control.

## Workflow

### 1. Confirm platform and inventory

1. Record Gatekeeper version, install method (Helm/manifests), and feature flags.
2. List ConstraintTemplates, Constraints, and Config (sync/exempt namespaces).
3. Note webhook failure policy and system namespaces that must stay exempt.
4. Prefer read-only inventory before changing enforce modes.

```bash
# Owned/lab cluster only
kubectl get constrainttemplates
kubectl get constraints -A
kubectl get config -n gatekeeper-system
kubectl get validatingwebhookconfiguration -l gatekeeper.sh/system=yes
```

### 2. ConstraintTemplate: schema + Rego

A **ConstraintTemplate** registers a Constraint CRD and Rego evaluated at
admission and during audit scans.

| Piece | Expectation |
| --- | --- |
| `crd.spec.names.kind` | Stable Constraint kind (e.g. `K8sRequiredLabels`) |
| `validation.openAPIV3Schema` | Parameters typed and documented |
| `targets[].rego` | Emits `violation[{"msg": ...}]` (or legacy form) |
| Input object | Correct `input.review.object` / `input.review.kind` use |
| Library Rego | Shared helpers; avoid silent no-op packages |

Keep templates **reusable**; put env-specific allowlists in Constraint
`parameters`, not hardcoded in template Rego.

### 3. Constraint: match and parameters

| Field | Guidance |
| --- | --- |
| `match.kinds` | API groups/kinds in scope (e.g. Pods, Deployments) |
| `match.namespaces` / `excludedNamespaces` | Explicit; protect kube-system carefully |
| `match.labelSelector` / `namespaceSelector` | Prefer narrow over cluster-wide |
| `parameters` | Least privilege; document exception owners |
| `enforcementAction` | See audit vs deny below |

Validate with server dry-run / staging apply before production deny.

### 4. Audit vs deny (enforcementAction)

| Mode | Admission effect | Operational use |
| --- | --- | --- |
| **deny** (default) | Rejects non-compliant creates/updates | Final enforce after audit is clean |
| **dryrun** | Admits; records violations in status/audit | Measure blast radius; GitOps feedback |
| **warn** | Admits; returns warning to client | Developer signal without hard block |

**Audit** (controller scan) surfaces drift on existing objects; **deny** only
affects admission of new/changed objects. Existing bad objects remain until
fixed or recreated — plan remediation, not surprise deny.

Rollout: (1) template + Constraint in **dryrun**/warn; (2) collect
`status.totalViolations`, fix controllers; (3) re-audit until exceptions are
time-boxed with owner; (4) flip **deny** non-prod → soak → prod with rollback
(revert action or exclude namespace).

### 5. Gaps, exemptions, and quality

Flag: cluster-wide match with no exclusions; empty Rego that never violates;
deny before dryrun on multi-tenant prod; sync Config missing kinds Rego needs;
webhook fail-open; secrets in parameters. Charts → `helm-chart-security`. PSA
only → `kubernetes-pod-security`. Code quality → `code-quality-standards`.

## Routing

| Need | Skill |
| --- | --- |
| Gatekeeper ConstraintTemplate, Constraint, audit vs deny | **This skill** |
| PSS/PSA / pod securityContext (no OPA CRDs) | `kubernetes-pod-security` |
| NetworkPolicy / default-deny CNI | `kubernetes-network-policy` |
| Cluster RBAC, secrets, authorized K8s assessment | `kubernetes-pentesting` |
| Helm install/values hardening | `helm-chart-security` |
| Policy YAML, tests, CI quality | `code-quality-standards` |
| Secrets in policy params or GitOps | `secrets-management-hygiene` |

Keep **this skill primary** for Gatekeeper CRDs/enforcement; switch for pure
PSA, NetworkPolicy, or cluster attack methodology.

## Output Checklist

- [ ] Scope/authorization recorded (owned/lab/ROE cluster and namespaces)
- [ ] Gatekeeper version, webhooks, Config/sync/exemptions inventoried
- [ ] ConstraintTemplates: kind, schema, Rego violation paths reviewed
- [ ] Constraints: match kinds/namespaces/selectors and parameters documented
- [ ] enforcementAction deliberate (dryrun/warn before deny)
- [ ] Audit findings reviewed; residual violations have owner + expiry
- [ ] Deny rollout staged (non-prod → soak → prod) with rollback
- [ ] System ns / break-glass exclusions justified (not permanent wildcards)
- [ ] No secrets in templates/params; evidence redacted
- [ ] Routed: PSA → `kubernetes-pod-security`; NetPol →
      `kubernetes-network-policy`; code → `code-quality-standards`

## Scope And Authorization

- **In scope:** org-owned, staging, lab, CTF, or ROE-named clusters where you
  may install Gatekeeper and change Constraints; GitOps/Helm review of templates.
- **Out of scope:** third-party clusters; cluster-wide **deny** without inventory
  and change window; disrupting workloads outside ROE.
- Prefer **dryrun/audit → remediate → deny**. Do not infer authorization from
  “looks like a lab.” Redact tokens, kubeconfigs, and PII. Gatekeeper is
  **admission + audit policy**, not a substitute for RBAC or NetworkPolicy.
