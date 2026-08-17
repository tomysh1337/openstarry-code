---
name: secure-sdlc-checklist
description: >
  Phase-by-phase secure software development lifecycle (SSDLC) checklist for
  org-owned products: requirements, design, implementation, verification,
  release, and operations. Use when secure SDLC, 安全开发生命周期, SSDLC,
  security release gate, security requirements, or embedding security into the
  delivery pipeline without turning the work into pure exploit hunting.
---

# Secure SDLC Checklist

Run a **security-aware delivery lifecycle** for systems your org owns or is
contracted to build. This skill is **process and gate methodology** — which
controls belong in which phase, who owns them, and what “done” looks like —
not a vulnerability-class exploit playbook.

## Scope And Authorization

- **In scope:** Org products, platforms, services, and features under change
  control; internal SDLC policy; authorized vendor/assurance reviews of *your*
  process maturity.
- **Out of scope:** Using this checklist to justify unauthorized testing of
  third-party systems; replacing a named bug-bounty or pentest engagement with
  “we have SDLC docs.”
- Prefer **documented policy and release gates** over ad-hoc heroics. If threat
  models or asset inventory are missing, hand design-time work to
  `threat-modeling-stride` and surface inventory to `recon-and-methodology`
  only when authorized.
- Treat process artifacts as sensitive when they list production hosts, admin
  paths, or residual risk acceptances. Redact credentials, tokens, PII, and
  customer data from checklists and tickets.
- Org security policy, compliance frameworks (e.g., internal SOC2 control map,
  PCI scope), and existing stage gates **outrank** generic examples here.

## Use When

- Standing up or auditing a **secure SDLC** for a product team
- Chinese/English teams: **安全开发生命周期**, SSDLC, 安全门禁, 发布安全检查
- Defining **phase gates** (requirements → design → code → test → release → ops)
- Mapping security work to sprint/release rituals without inventing a second process
- Preparing for audit questions: “where is security in the lifecycle?”
- Aligning AppSec, engineering, and product on ownership per phase

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| STRIDE workshop / DFD threat register | `threat-modeling-stride` |
| Running/triaging SAST or DAST scanners | `sast-dast-tooling-usage` |
| Implementation reliability/security/tests baseline | `code-quality-standards` |
| Unit test design / AAA / naming | `unit-testing-style` |
| Authorized external bounty process | `bug-bounty-methodology` |
| Secrets vault/rotation hygiene only | `secrets-management-hygiene` |
| SBOM / dependency provenance only | `sbom-and-supply-chain` |
| CI stage wiring only | `ci-cd-pipeline-patterns` |

## Core Idea

Secure SDLC = **shift-left design risk + in-pipeline verification + release
accountability + feedback from ops**.  
Each phase has **entry criteria**, **activities**, **exit criteria**, and a
**named owner**. Scanner findings and pen tests feed the loop; they do not
replace design-time controls or secure coding standards.

Typical phase map (adapt names to org: “Definition of Ready,” “Definition of
Done,” CAB, etc.):

| Phase | Security focus | Primary artifacts |
| --- | --- | --- |
| 0. Governance | Policy, roles, risk appetite | RACI, severity SLAs, tool allowlist |
| 1. Requirements | Abuse cases, data class, compliance | Security reqs, acceptance criteria |
| 2. Design | Trust boundaries, STRIDE | Threat model, ADRs, control design |
| 3. Implementation | Secure coding, secrets, deps | Code, reviews, unit tests |
| 4. Verification | SAST/DAST/SCA, tests, review | Scan reports, test evidence |
| 5. Release | Gate decisions, SBOM, signing | Release checklist, attestations |
| 6. Operations | Patch, IR, monitoring, backlog | Incidents, metrics, model updates |

## Workflow

### 0. Establish governance (once per product / org unit)

1. Name **security owners**: eng lead, product, AppSec liaison (or shared duty).
2. Publish **severity definitions** and fix SLAs (Critical/High/Med/Low) aligned
   with org risk matrix — do not invent a second scale if one exists.
3. Define **tooling allowlist**: SAST, SCA, secret scan, DAST, image scan
   (`sast-dast-tooling-usage`, `sbom-and-supply-chain`, `secrets-management-hygiene`).
4. Define **gate strength** by change type: hotfix vs major feature vs new
   public surface vs regulated data.
5. Record **exceptions process**: who may accept residual risk, max duration,
   review date required.
6. Link delivery tools: tickets → threat ids / finding ids → release notes.

### 1. Requirements phase

**Entry:** problem statement, rough users, data categories known or draft.

| Activity | Concrete technique |
| --- | --- |
| Data classification | Tag PII, payment, credentials, health, exportable bulk data |
| Security requirements | Write testable reqs: “admin export requires MFA + audit event with actor id” |
| Abuse / misuse cases | For each user story: “malicious user does X with Y privilege” |
| AuthN/Z expectations | Roles, tenants, service-to-service trust assumptions |
| Compliance hooks | Map to org controls (logging, retention, encryption, residency) |
| Non-goals | Explicitly out-of-scope features and third-party trust |

**Exit criteria:**

- [ ] Security acceptance criteria on high-risk stories (auth, money, admin, PII)
- [ ] Data classification recorded for new stores/fields
- [ ] Abuse cases listed or “N/A + why” for low-risk UI-only changes
- [ ] Product + eng agree residual risk appetite for this release

### 2. Design phase

**Entry:** requirements exit met; architecture sketch exists.

| Activity | Concrete technique |
| --- | --- |
| Trust boundaries | Internet ↔ edge ↔ app ↔ data; admin plane; tenant isolation |
| Threat model | Run `threat-modeling-stride` for new boundaries, data classes, or admin surfaces |
| Control selection | AuthZ server-side, crypto, rate limits, audit, input validation strategy |
| Secrets design | No secrets in client; vault/OIDC injection (`secrets-management-hygiene`) |
| Dependency posture | New package/registry risk; pin/lock policy (`sbom-and-supply-chain`) |
| Abuse-resistant APIs | IDOR-resistant object access, least privilege defaults |

**Exit criteria:**

- [ ] DFD or equivalent for the change; trust boundaries labeled
- [ ] Open Critical/High design threats have mitigations or signed acceptance
- [ ] Security-sensitive ADRs merged or linked
- [ ] Test plan seeds: what must be proven in verification (positive + abuse)

### 3. Implementation phase

**Entry:** design exit for the change; branch/PR workflow active.

| Activity | Concrete technique |
| --- | --- |
| Secure coding baseline | Apply `code-quality-standards` on every production change |
| Input/output handling | Validate at trust boundaries; encode at sinks; parameterized queries |
| AuthZ in depth | Server-side checks per object/action; never client-only role flags |
| Secrets | Load from platform store; `.env.example` placeholders only |
| Unit tests for security-relevant behavior | `unit-testing-style`: authz deny paths, parsing edges, crypto wrappers |
| Peer review | Checklist includes authZ, injection surfaces, secret leak, logging redaction |
| Pre-commit / IDE | Format, lint, optional secret pre-scan |

**Exit criteria:**

- [ ] PR description notes security-relevant behavior and test evidence
- [ ] Unit/integration tests cover deny paths and critical invariants
- [ ] No secrets in diff; secret scan clean on the branch
- [ ] Reviewer sign-off includes security checklist items for high-risk PRs

### 4. Verification phase

**Entry:** code merged or release candidate built; CI green on functional tests.

| Activity | Concrete technique |
| --- | --- |
| SAST + SCA + secrets + image | Run and **triage** via `sast-dast-tooling-usage` + `sbom-and-supply-chain` |
| DAST / authenticated scan | Staging or lab only; scoped targets; rate limits |
| Manual / focused tests | Authz matrix, IDOR dual-account, injection on new params |
| Security regression | Prior High/Critical still fixed; new abuse cases from design |
| External program (if any) | Scope-bound bounty or pentest handoff → `bug-bounty-methodology` / SOW |

**Exit criteria:**

- [ ] Policy-defined severity gates met (or exceptions with owner + expiry)
- [ ] False positives documented; true positives ticketed with owners
- [ ] Evidence retained: scan IDs, build SHA, environment under test
- [ ] No unowned open Critical on the release train without CAB/security sign-off

### 5. Release phase

**Entry:** verification exit; deploy artifact identified by digest/SHA.

| Activity | Concrete technique |
| --- | --- |
| Release checklist | Auth, crypto, logging, rollback, feature flags, config flags |
| Provenance | Image digest, SBOM attached, signatures if policy requires |
| Config & secrets | Prod secrets from env store; no debug flags; least privilege IAM |
| Change record | Link threat model version, open exceptions, scanner baseline |
| Comms | Security-relevant user/admin notes when behavior changes |
| Rollback | Documented; kill switch / flag for risky features (`feature-flag-patterns`) |

**Exit criteria:**

- [ ] Deploy from **build-once** artifact (digest), not “rebuild on prod”
- [ ] SBOM/attestations published per policy
- [ ] Exceptions listed in release record with review dates
- [ ] On-call knows new failure modes and dashboards

### 6. Operations and feedback

**Entry:** change live (or pilot cohort).

| Activity | Concrete technique |
| --- | --- |
| Monitor | Auth failures, 4xx/5xx spikes, WAF signals, dependency alerts |
| Patch cadence | OS/base image/lib CVEs within SLA; emergency path for KEV-class |
| Incident response | Contain → rotate secrets → fix → postmortem → SDLC update |
| Backlog hygiene | Security debt aged with same visibility as product debt |
| Model refresh | Reopen `threat-modeling-stride` on new trust boundary or data class |
| Metrics | MTTR for Critical, % PRs with security tests, scanner fix lag, exception count |

**Exit / continuous:**

- [ ] Production alerts cover new high-value paths
- [ ] Post-incident actions assigned to a lifecycle phase (not “be careful”)
- [ ] Quarterly (or org cadence) review of exceptions and tool false-positive rates

## Phase Gate Summary (printable)

| Gate | Must be true before advancing |
| --- | --- |
| Req → Design | Security acceptance criteria + data class on risky stories |
| Design → Build | Threat model (or justified skip) + control decisions recorded |
| Build → Verify | Secure review + unit/deny-path tests + no secrets in VCS |
| Verify → Release | Severity policy met; findings owned; evidence by SHA |
| Release → Ops | Digest deploy, secrets/config correct, rollback known |
| Ops → Next | Incidents and scanner debt feed requirements/design |

**Justified skip:** document who skipped which gate, why (e.g., pure docs change),
and automatic re-entry triggers.

## Org Context Patterns

| Org shape | Adaptation |
| --- | --- |
| Startup / small team | Collapse gates into PR template + staging DAST weekly; still keep threat notes for auth/PII |
| Regulated / enterprise | Formal RACI, CAB for High residual risk, mandatory SBOM and audit trail |
| Platform / multi-tenant | Extra design gate: tenant isolation and admin plane STRIDE every major API |
| Mobile + API | Separate client and API checklists; never put confidential secrets in clients |
| ML/LLM product | Add `ai-ml-security` + `llm-prompt-injection` under design/verify for model and tool surfaces |

## Anti-Patterns

- “Security = one annual pentest” with no design or CI gates
- Scanner greenwash: fail-open `continue-on-error` on Critical SAST/SCA
- Threat model after ship with no link to the change that needed it
- Infinite exception renewals without owners or expiry
- Treating bounty reports as the only requirements input
- Security checklist that is pure tool names with no exit criteria or RACI
- Blocking every Low informational finding equally with Critical (noise → bypass)

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Secure SDLC phases, gates, RACI, 安全开发生命周期 | **This skill** | — |
| Design-time STRIDE / DFD / 威胁建模 | `threat-modeling-stride` | this skill for phase placement |
| SAST/DAST when/how/triage | `sast-dast-tooling-usage` | this skill for verify/release gates |
| Secure implementation and code review baseline | `code-quality-standards` | **always** on code changes |
| Unit test design for security-relevant behavior | `unit-testing-style` | `code-quality-standards` |
| Authorized bug bounty / external hunter process | `bug-bounty-methodology` | this skill for intake into backlog |
| Secrets lifecycle | `secrets-management-hygiene` | this skill |
| SBOM / SCA / provenance | `sbom-and-supply-chain` | this skill |
| CI job wiring, OIDC, artifacts | `ci-cd-pipeline-patterns` | this + SAST/DAST skill for scan jobs |
| Estate recon before modeling (authorized) | `recon-and-methodology` | `threat-modeling-stride` |

### Routing notes (required helpers)

- **`code-quality-standards`:** baseline for every implementation and fix flowing from SDLC gates.
- **`threat-modeling-stride`:** design-phase primary when boundaries, data class, or admin surface change.
- **`unit-testing-style`:** shape deny-path and invariant tests in implementation/verification.
- **`bug-bounty-methodology`:** when external authorized hunters are part of verify/ops feedback — not a substitute for internal gates.
- **`sast-dast-tooling-usage`:** own scanner operation and triage; this skill only places them on the timeline.

## Checklist

### Governance
- [ ] Owners/RACI and severity SLAs published
- [ ] Tool allowlist and exception process defined
- [ ] Gate strength varies by change risk

### Requirements
- [ ] Security acceptance criteria on high-risk work
- [ ] Data classification and abuse cases captured

### Design
- [ ] Trust boundaries + threat model (or justified skip)
- [ ] Mitigations testable; secrets/deps posture decided

### Implementation
- [ ] `code-quality-standards` applied; peer security review for high-risk PRs
- [ ] Deny-path / invariant tests via `unit-testing-style`
- [ ] No secrets in source; samples are placeholders

### Verification
- [ ] SAST/SCA/secrets/(optional) DAST triaged (`sast-dast-tooling-usage`)
- [ ] Severity gates or signed exceptions with expiry
- [ ] Evidence tied to commit/image digest

### Release
- [ ] Digest-based deploy; SBOM/sign per policy
- [ ] Rollback/flags; release record links exceptions and model version

### Operations
- [ ] Monitoring and patch SLAs active
- [ ] Incidents feed requirements/design; models reopened on boundary change
- [ ] External findings (`bug-bounty-methodology`) enter the same backlog SLAs

### Hygiene
- [ ] Reports and checklists redacted; org policy precedence respected
- [ ] No unauthorized testing justified solely by “SSDLC activity”

## Rules

- Process evidence and owned gates beat tool logos on a slide.
- Every Critical/High finding or design threat has an owner and a due/review date.
- Justified skips are written decisions — silence is not a skip.
- Implementation always carries `code-quality-standards`; scanners never replace review.
- External bounty/pentest is an input to the lifecycle, not the lifecycle itself.
- Reopen design controls when trust boundaries or data classes change.
- Authorized org systems only; methodology is defensive and assurance-oriented.
---

# Note

This skill is the **lifecycle orchestrator** for secure delivery. Hand STRIDE
workshops to `threat-modeling-stride`, scanner operation to
`sast-dast-tooling-usage`, code quality to `code-quality-standards`, unit design
to `unit-testing-style`, and external programs to `bug-bounty-methodology`.
Keep phase exit criteria and RACI as the SSOT for “are we ready to ship?”
