---
name: kubernetes-admission-webhooks
description: >
  Design, review, and harden Kubernetes admission webhooks: MutatingWebhookConfiguration,
  ValidatingWebhookConfiguration, AdmissionReview, failurePolicy, sideEffects, selectors,
  TLS/caBundle, and availability. Use when implementing or auditing validating/mutating
  admission controllers, debugging webhook timeouts or Fail-closed outages, choosing
  matchPolicy/namespaceSelector/matchConditions, or securing webhook endpoints on
  owned/lab/authorized clusters — not unauthorized cluster compromise.
---

# Kubernetes Admission Webhooks

Build and review **mutating** and **validating** admission webhooks so API writes
are enforced correctly, fail safely, and stay available. Platform hardening and
policy engineering only — owned, staging, lab, or ROE clusters.

## When To Use

- `MutatingWebhookConfiguration` / `ValidatingWebhookConfiguration` design or review
- `AdmissionReview` request/response, dry-run, and patch (`JSONPatch`) behavior
- `failurePolicy` (Fail vs Ignore), `timeoutSeconds`, `sideEffects`, `matchPolicy`
- `namespaceSelector` / `objectSelector` / `matchConditions` (CEL) scoping
- TLS for webhook Services: certs, `caBundle`, rotation, mTLS expectations
- Webhook outages: API create/update blocked, timeouts, mis-ordered chain
- Prefer external webhooks vs in-process **ValidatingAdmissionPolicy** (CEL)

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Pod PSS/PSA / securityContext | `kubernetes-pod-security` |
| NetworkPolicy / default-deny | `kubernetes-network-policy` |
| Cluster RBAC, secrets, API attack surface | `kubernetes-pentesting` |
| cert-manager Issuer/Certificate lifecycle | `cert-manager-basics` |
| Chart packaging / values security | `helm-chart-security` |
| Manifest quality, tests, CI gates | `code-quality-standards` |

## Scope And Authorization

- **In scope:** clusters/namespaces you own or may configure under ROE; GitOps/Helm
  review of webhook configs; staging dry-runs before enforce.
- **Out of scope:** unauthorized installs; malware via webhooks; weakening prod
  Fail-closed policy without a change window; DoS experiments on shared prod APIs.
- Prefer read-only inventory and `--dry-run=server` before changing failurePolicy
  or broad match rules. Redact tokens/certs/Secret dumps; treat webhook as **control-plane critical**.

## Workflow

### 1. Inventory admission path

1. Cluster version; list mutating then validating configs (rules, selectors, failurePolicy).
2. Map owners: Deploy/Service behind each `clientConfig.service`.
3. Note exemptions (kube-system, controllers) and break-glass paths.

```bash
kubectl get mutatingwebhookconfigurations,validatingwebhookconfigurations -o wide
kubectl get validatingadmissionpolicies,validatingadmissionpolicybindings 2>/dev/null
```

### 2. Choose mutating vs validating (and CEL)

| Mechanism | Role |
| --- | --- |
| **Mutating** | Defaults, inject labels/sidecars; runs before validating |
| **Validating** | Allow/deny only; must not rely on later mutation |
| **ValidatingAdmissionPolicy** | In-API CEL checks; no external Service latency |

Prefer validating for security gates. Keep mutations idempotent; use
`reinvocationPolicy: IfNeeded` only when re-entry is required and safe.

### 3. Rules and match scope

1. Constrain `rules`: apiGroups, resources, verbs, `scope`.
2. Prefer **Equivalent** `matchPolicy` so version aliases still match.
3. Use `namespaceSelector` / `objectSelector` to exclude system and break-glass ns.
4. Add `matchConditions` for fine CEL filters; avoid matching all objects.
5. Never leave Fail-closed webhooks matching every namespace without recovery.

### 4. clientConfig, TLS, and identity

1. Prefer in-cluster `service` (+ path/port) over raw `url` unless justified.
2. Pin API-server trust via correct **caBundle** (or cert-manager CA inject).
3. Webhook TLS 1.2+, valid SAN for Service DNS; rotate before expiry
   (`cert-manager-basics` for issuance).
4. Treat AdmissionReview as untrusted input; do not log full Secret objects.
5. NetworkPolicy: API server → webhook pods only (`kubernetes-network-policy`).

### 5. failurePolicy, timeouts, sideEffects

| Field | Guidance |
| --- | --- |
| `failurePolicy: Fail` | Default for security gates (fail closed) |
| `failurePolicy: Ignore` | Soft/best-effort only; document risk |
| `timeoutSeconds` | Keep low (e.g. 1–5s); avoid API-server hangs |
| `sideEffects` | Prefer `None` / `NoneOnDryRun`; honor dry-run |
| Availability | Multi-replica, PDBs, probes; watch queue depth |

A down or slow Fail webhook **blocks** matching API writes for those rules —
treat as SEV-class availability risk.

### 6. Implement, test, findings

1. Contract: AdmissionReview v1 → `allowed`, optional `patch`/`patchType`, clear deny messages.
2. Unit-test allow/deny/patch; fuzz malformed objects; server dry-run samples.
3. Confirm order (mutate → validate) and selector exclusions; lab-only scale-to-zero chaos.
4. Flag: Ignore on security rules; missing caBundle; `*` resource match; no ns exclusions;
   side effects on dry-run; single replica; Secrets in logs; mutations validators skip.
5. Fix via narrower rules, Fail + HA, cert rotation, dry-run-safe handlers — not by
   disabling all admission in production. Ship GitOps with documented break-glass.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Mutating/validating webhook design, review, outages | **This skill** | — |
| PSS/PSA / pod securityContext | `kubernetes-pod-security` | this skill if webhook enforces similar rules |
| East-west NetPol to webhook pods | `kubernetes-network-policy` | this skill for ports/selectors |
| Webhook TLS certs / CA inject | `cert-manager-basics` | this skill for caBundle wiring |
| Cluster RBAC / API assessment | `kubernetes-pentesting` | this skill for admission surface |
| Helm chart of webhook operator | `helm-chart-security` | this skill for config semantics |
| Handler code, tests, CI | `code-quality-standards` | this skill for admission contract |

Keep **this skill primary** for webhook config/behavior. Hand PSS defaults to
`kubernetes-pod-security`; secret process leaks to `secrets-management-hygiene`.

## Output Checklist

- [ ] Scope/authorization recorded (owned/lab/ROE only)
- [ ] Existing Mutating/Validating webhook configs inventoried
- [ ] Mutate vs validate (and CEL VAP) choice justified
- [ ] Rules narrowed: groups, resources, verbs, scope, selectors
- [ ] `matchPolicy`, `matchConditions`, exclusions documented
- [ ] `failurePolicy`, `timeoutSeconds`, `sideEffects` set deliberately
- [ ] `clientConfig` + caBundle/TLS SAN and rotation path verified
- [ ] Dry-run safe; no Secret payloads in logs
- [ ] HA/PDB/probes for Fail-closed webhooks; break-glass path written
- [ ] Server dry-run tests for allow/deny/patch paths passed
- [ ] Routed: PSS → `kubernetes-pod-security`; NetPol → `kubernetes-network-policy`;
      certs → `cert-manager-basics`; code → `code-quality-standards`
- [ ] Tokens/certs redacted; residual Ignore/wide-match exceptions have owner/expiry
