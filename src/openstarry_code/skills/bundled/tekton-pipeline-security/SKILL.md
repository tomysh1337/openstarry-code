---
name: tekton-pipeline-security
description: >
  Harden Tekton Pipelines on owned or authorized clusters: Task/Pipeline
  definitions, PipelineRun isolation, ServiceAccount RBAC, workspace and secret
  mounts, step image trust, Triggers EventListeners, and Chains provenance.
  Use when reviewing Tekton YAML, PipelineRun podTemplates, privileged steps,
  untrusted git resolvers, TriggerBindings, or CI that runs untrusted pull
  requests on Kubernetes — not third-party cluster abuse.
---

# Tekton Pipeline Security

Assess and harden **Tekton** so pipeline workloads run with least privilege,
trusted inputs and images, controlled secret access, and isolated runs. Prefer
static review of Tasks, Pipelines, Triggers, and RBAC before live changes.
**Org-owned, lab, or explicitly authorized clusters only.**

## Scope And Authorization

- **In scope:** Tekton CRs (`Task`, `ClusterTask`, `Pipeline`, `PipelineRun`,
  `TaskRun`, `Trigger*`, `EventListener`), run ServiceAccounts and Roles,
  workspaces, resolvers, podTemplates, Chains/signing policy, and related CI
  manifests you own or are contracted to review.
- **Out of scope:** foreign-cluster abuse; using leaked pipeline tokens outside
  ROE; unapproved prod runs that mutate shared systems; host breakout proofs on
  shared production nodes.
- Prefer `kubectl get/describe` and non-prod first. Gate live Triggers, privileged
  podTemplates, and secret-mount experiments. Redact tokens, kubeconfigs,
  git/registry credentials, and PII from logs, results, and reports.

## When To Use

- Authoring or reviewing Tekton `Task` / `Pipeline` / `PipelineRun` / `TaskRun`
- Step `image`, `script`, `command`, `env`, or mounts that may leak or escalate
- Pipeline ServiceAccounts, RoleBindings, default SA token automount
- Workspaces (PVC, secret, configMap) and param/result trust boundaries
- **Triggers**: EventListener, TriggerBinding/Template, interceptors, untrusted PR webhooks
- Resolvers (git, bundle, hub) and unsigned / floating task references
- **Tekton Chains** / SLSA provenance, signed runs, trusted resources
- Keywords: Tekton security, PipelineRun SA, privileged step, EventListener,
  workspace secret, Chains attestation, untrusted PR pipeline

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Generic GitHub Actions / GitLab CI patterns | `ci-cd-pipeline-patterns` |
| Live cluster RBAC / secret dump (lab) | `kubernetes-pentesting` |
| Org secret rotation, VCS leak IR | `secrets-management-hygiene` |
| Image non-root / layer secrets | `dockerfile-best-practices` |
| Lab container→host breakout | `container-escape-techniques` |
| Helm packaging of Tekton install | `helm-chart-security` |
| Task scripts and CR quality | `code-quality-standards` |

## Workflow

### 1. Inventory trust boundaries

1. Record cluster/namespace, Tekton version, who can create PipelineRuns, and
   whether Triggers accept external webhooks.
2. List Tasks/Pipelines (namespaced vs cluster), ClusterTasks, resolvers, run SAs.
3. Map **trusted** refs (main/tag) vs **untrusted** (fork PR, free-form git URL,
   unconstrained params).

```bash
# Owned/lab — metadata only
kubectl get task,pipeline,pipelinerun,taskrun,sa,eventlistener,trigger -n <ns>
```

### 2. ServiceAccount and RBAC least privilege

- Dedicated SA per pipeline class (build vs deploy); never default SA for runs.
- Limit Role verbs to what steps need (no casual `*` on secrets/pods/exec).
- Separate deploy SA/bindings from untrusted build/test runs.
- `automountServiceAccountToken: false` when steps do not call the API.
- Who may `create` PipelineRun/TaskRun is as important as step power.

### 3. Pod template, steps, and workspaces

| Control | Hardened default |
| --- | --- |
| Security context | non-root; `allowPrivilegeEscalation: false`; drop `ALL` |
| Privileged / hostPath / hostNetwork | Off for app CI; document exceptions |
| Step images | Pin digest or immutable tag; org-approved only |
| Secrets | Minimal workspace/CSI mounts; never echo into results/logs |
| Workspaces | Isolate RW build space from secret mounts; no shared RW PVC across trust levels |
| Params/results | Untrusted input; no `eval` of params in scripts |

Untrusted PR pipelines must not mount prod deploy credentials or cluster-admin
SAs. Fix Task contracts against param injection; do not run offensive payloads
against shared prod.

### 4. Triggers, resolvers, and supply chain

1. EventListener: authenticate webhooks (interceptors, shared secrets, CEL);
   restrict namespace and Trigger SA.
2. Bindings: allowlist branches/repos; do not pass arbitrary remote Task URLs
   from untrusted events into privileged runs.
3. Resolvers: pin bundle/git revisions; prefer signed/trusted resources; avoid
   floating public hub ClusterTasks in prod.
4. Chains: attest/sign release PipelineRuns; verify provenance per policy
   (pair `container-image-signing` for image sign/verify).
5. Dashboard/EL: authn/z; NetworkPolicy for listeners and SCM/registry egress.

### 5. Remediate and verify

Fix CRs and RBAC in GitOps; re-run non-prod PipelineRun; confirm SA cannot read
unrelated secrets and untrusted Triggers cannot deploy. Apply
`code-quality-standards` to Task scripts; live depth → `kubernetes-pentesting`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Tekton Tasks/Pipelines/Runs, SA, workspaces, Triggers, Chains | **This skill** | — |
| Generic multi-platform CI stages/OIDC/cache | `ci-cd-pipeline-patterns` | this for Tekton-on-K8s |
| Live cluster RBAC/secrets assessment | `kubernetes-pentesting` | this for pipeline root cause |
| Secret lifecycle, leak IR, rotation | `secrets-management-hygiene` | this for mount/log paths |
| Step images / provenance signing | `dockerfile-best-practices` / `container-image-signing` | this for step refs / Chains |
| Privileged step breakout (lab) | `container-escape-techniques` | this for podTemplate evidence |
| Helm install of Tekton/EL; scripts/GitOps quality | `helm-chart-security` / `code-quality-standards` | this for runtime CR policy |

Keep **this skill primary** for Tekton hardening; switch for generic SaaS CI, org secrets, or live cluster exploitation.

## Output Checklist

- [ ] Authorization and cluster/namespace scope recorded (owned/lab/ROE only)
- [ ] Tasks, Pipelines, Runs, Triggers, resolvers, and run SAs inventoried
- [ ] Trusted vs untrusted paths separated (fork PR / free git URL)
- [ ] Dedicated least-privilege SA; default SA avoided; automount minimized
- [ ] PodTemplate: non-privileged, non-root, dropped caps, no host ns/path
- [ ] Step images pinned/approved; no floating public tasks in prod
- [ ] Secrets out of params/logs/results; prod creds off untrusted runs
- [ ] Workspaces isolate trust levels; shared PVC risk owned or fixed
- [ ] EventListener authenticated/filtered; Trigger SA cannot over-deploy
- [ ] Chains/signing where release policy requires; EL/Dashboard exposure intentional
- [ ] Evidence redacted; route to `ci-cd-pipeline-patterns`, `kubernetes-pentesting`,
      `secrets-management-hygiene`, image/signing skills, `code-quality-standards` as needed
