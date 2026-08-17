---
name: jenkins-credential-hygiene
description: >
  Jenkins credential storage, scoping, pipeline binding, masking, rotation, and
  leak hygiene for owned controllers: Credentials plugin types, folder vs global
  scope, withCredentials / credentials() usage, JCasC secrets, agent and log
  exposure. Use when Jenkins credentials, credentials.xml, secret text/SSH/AWS
  creds in Jenkins, pipeline withCredentials, credential domain, JCasC
  credentials, or Jenkins secret rotation on authorized controllers.
---

# Jenkins Credential Hygiene

Store, scope, inject, mask, and rotate **Jenkins credentials** so secrets never
sit in `Jenkinsfile`s, console logs, or world-readable agent paths. **Owned or
explicitly authorized Jenkins controllers only.** Org secret lifecycle / git
leak IR → `secrets-management-hygiene`. Broader pipeline design →
`ci-cd-pipeline-patterns`.

## When To Use

- Creating or reviewing **Credentials** (secret text, username/password, SSH
  key, certificate, secret file, cloud/GitHub app plugin types)
- Choosing **global vs folder vs item** scope and credential domains
- Wiring pipelines: `withCredentials`, `credentials()`, env bindings — without
  echoing secrets
- Hardening **JCasC** credential definitions; rotation after leak/offboarding
- Mentions: Jenkins credentials, `credentials.xml`, `withCredentials`,
  `credentialsId`, secret masking, folder credentials

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Org inventory, git/.env scanners, general leak IR | `secrets-management-hygiene` |
| Multi-CI stages / OIDC beyond Jenkins | `ci-cd-pipeline-patterns` |
| Cloud SM rotation as system of record | cloud SM skill + secrets hygiene |
| Jenkinsfile / shared-lib code quality | `code-quality-standards` |

## Workflow

### 1. Inventory (no secret values)

Record controller/env, authorization, and who may **Manage Credentials**. List
credential **IDs/descriptions only**: type, scope (system/global/folder),
domains, consuming jobs/libs, owners, last rotation. Prefer non-prod first.
Never dump raw `credentials.xml` or `$JENKINS_HOME/secrets` into tickets/chat.

### 2. Type, scope, ownership

| Choice | Practice |
| --- | --- |
| **Type** | Match consumer (SSH for git-SSH; secret text for tokens; user/pass only if required) |
| **Scope** | Prefer **folder** over global “god” secrets used by every job |
| **IDs** | Stable, env-qualified (`deploy-staging-aws`); purpose in description |
| **Domains** | Hostname/path domains when they reduce misuse |
| **Owners** | Named team; one consumer principal per secret when practical |

### 3. Pipeline injection (IDs only)

```groovy
withCredentials([
  usernamePassword(credentialsId: 'deploy-user-staging',
    usernameVariable: 'DEPLOY_USER', passwordVariable: 'DEPLOY_PASS'),
  string(credentialsId: 'svc-api-token-staging', variable: 'API_TOKEN')
]) {
  sh './deploy.sh'
}
```

**Rules:** store secrets in Credentials, reference by **ID**; keep bindings to
the smallest stage; do not `echo`/printenv secrets; avoid `set -x` around
exports; do not archive credential files; shred temps. Masking is best-effort
(encoding/chunking can still leak). Untrusted multibranch/PR builds must not
reach production credential IDs (folder ACLs + trust model).

**Bad:** plaintext in `Jenkinsfile`/shared libs; secrets in parameter defaults;
writing keys into workspace artifacts.

### 4. Controller, agent, logs, JCasC

1. Protect `$JENKINS_HOME/credentials.xml` and `secrets/` (OS ACL, backups,
   disk encryption); treat as high-tier.
2. Shared agents widen exposure — use dedicated labels/ephemeral agents for
   high-value secrets.
3. Console: no wholesale `printenv`; redact plugins help but are not proof.
4. Minimize credential-capable plugins; patch Credentials/auth plugins; limit
   **Run Scripts** / credential-use rights.
5. JCasC: encrypted secrets or external vault at bootstrap — **no** plaintext
   credential YAML in git.

### 5. Access control, rotation, verify

1. Authorization strategy: not every developer manages global credentials;
   separate configure vs use where possible.
2. Rotate on schedule, offboarding, leak: new/updated secret → migrate jobs →
   verify → retire old ID.
3. On leak: **rotate external secret first** (cloud key, PAT, DB), then update
   Jenkins; audit jobs/agents; IR via `secrets-management-hygiene`.
4. Prefer short-lived/federated cloud creds over static long-lived keys when
   plugins support them.
5. Verify: secret-scan Jenkinsfiles/libs; masked console; folder scope enforced;
   post-rotation old value fails. Groovy changes → `code-quality-standards`.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Jenkins store, IDs, scope, withCredentials, masking, JCasC creds | **This skill** | — |
| Org leak IR, git history, scanners, vault policy | `secrets-management-hygiene` | this for Jenkins cutover |
| Multi-stage CI / non-Jenkins OIDC | `ci-cd-pipeline-patterns` | this for Jenkins binding |
| Shared library / pipeline Groovy quality | `code-quality-standards` | **always** on code |
| External SM rotation as SoR | cloud SM skill | this for consumer update |

**Ownership:** Jenkins-side types, scope, binding, controller/agent exposure,
and store rotation. Org secret policy/scanning → `secrets-management-hygiene`.

## Output Checklist

- [ ] Authorization and controller/env scope recorded (owned Jenkins only)
- [ ] IDs inventoried: type, scope, domain, consumers, owners (no values)
- [ ] Least scope (folder preferred); no unnecessary global shared secrets
- [ ] Pipelines reference IDs only; no plaintext in Jenkinsfile/libs
- [ ] Tight bindings; no archive/printenv of secrets; masking checked
- [ ] Agent isolation considered for high-value credentials
- [ ] RBAC for manage vs use is intentional
- [ ] JCasC/git free of plaintext credential material
- [ ] Rotation/revoke path documented; leak = external rotate-first
- [ ] Non-prod verify done; CQS on Groovy/shared-lib changes
- [ ] Hand-offs: IR → `secrets-management-hygiene`; CI topology → `ci-cd-pipeline-patterns`

## Scope And Authorization

- **In scope:** Controllers, agents, folders, and jobs you operate or are
  contracted to harden; create/update/rotate under change control; pipeline
  binding and log/agent exposure review; JCasC credential layout.
- **Out of scope:** Unauthorized Jenkins; dumping/exfiltrating stores; using
  recovered secrets outside engagement scope; disabling audit without approval.
- Prefer non-prod. Gate prod secret reads, mass rotation, and script console.
  Never paste live secrets into tickets, chat, or examples — IDs/placeholders
  only. On exposure: rotate externally, update Jenkins, document redacted.
