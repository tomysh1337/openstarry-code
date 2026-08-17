---
name: threat-modeling-stride
description: >
  STRIDE threat modeling workshop workflow for authorized product and system
  reviews: scope and DFDs, per-element STRIDE analysis, risk ranking, mitigations,
  and living model updates. Use when threat model, STRIDE, 威胁建模, DFD, attack
  surface workshop, security design review, or pre-build architecture risk
  assessment in org-owned systems.
---

# STRIDE Threat Modeling (Workshop Workflow)

Run **structured threat modeling** for systems you own or are contracted to
assess. This skill is **design and process methodology** — identify threats,
document residual risk, and drive mitigations — not an exploit playbook.

## Scope And Authorization

- **In scope:** Org products, internal platforms, features under change control,
  design docs, and authorized security design reviews / red-team planning inputs.
- **Out of scope:** Using model outputs to attack third-party systems without
  written authorization; speculative “how to break X” without a system under review.
- Prefer **documented architecture** (designs, OpenAPI, deploy diagrams) over
  invasive discovery. If inventory is missing, hand host/API recon to
  `recon-and-methodology` first, then return here.
- Treat model artifacts as sensitive: do not paste real secrets, production
  connection strings, or unrestricted customer data into diagrams or tickets.
- Redact credentials, tokens, PII, and internal-only hostnames from shared reports.

## Use When

- Building or refreshing a **threat model** for a service, feature, or platform
- Facilitating a **STRIDE** workshop (design review, sprint zero, major change)
- Chinese/English teams: **威胁建模**, 安全设计评审, 攻击面分析 (design-time)
- Producing DFD + trust boundaries before implementation or release gate
- Ranking security work from architecture risk (not from a confirmed vuln class)
- Feeding a test plan: “what could go wrong?” before class-specific testing

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Estate recon / asset map / pentest kickoff inventory | `recon-and-methodology` |
| Confirmed injection / IDOR / JWT flaw testing | Matching web class skill |
| Secrets in code, vault, rotation policy | `secrets-management-hygiene` |
| Dependency / SBOM / supply-chain gates | `sbom-and-supply-chain` |
| Implementation hardening of code under review | `code-quality-standards` |
| Log redaction / structured log design | `logging-message-style` |

## STRIDE At A Glance

Apply **per trust-boundary-crossing element** (process, data store, data flow,
external entity, interactive UI) — not once for the whole system.

| Letter | Category | Design question |
| --- | --- | --- |
| **S** | Spoofing | Can an actor forge identity (user, service, device, message origin)? |
| **T** | Tampering | Can data or code be modified in transit or at rest without detection? |
| **R** | Repudiation | Can an actor deny an action because logs/audit are weak or mutable? |
| **I** | Information disclosure | Can unauthorized parties read sensitive data or metadata? |
| **D** | Denial of service | Can availability or capacity be degraded by abuse or failure? |
| **E** | Elevation of privilege | Can a lower-trust actor gain higher privileges or cross tenancy? |

**Variants:** Some orgs add **Privacy** (LINDDUN-style) or **Abuse** cases as
companion lanes; keep them labeled separately so security boundary issues stay
distinct from pure policy/safety findings.

## Workflow

### 1. Kickoff — lock scope and success criteria

1. Name the **system under model** (SUM): product, service, feature, or change.
2. Record **owners** (eng, product, security), review date, and model version.
3. Define **in-scope components** and explicit exclusions (third-party SaaS,
   sister products, future phases).
4. List **assumptions** (e.g., “IdP is trusted,” “CI is in separate model”).
5. Choose **depth**: whiteboard (2h), design-gate (half day), or full (multi-session).
6. Agree **outputs**: DFD set, threat register, prioritized mitigations, residual risk.

### 2. Gather inputs (passive / design artifacts)

Prefer existing artifacts before scanning:

| Input | Use |
| --- | --- |
| Architecture / sequence diagrams | Processes and flows |
| Deploy topology (k8s, regions, mesh) | Trust boundaries |
| Data classification / retention | What “sensitive” means |
| AuthN/Z matrix (roles, tenants) | Spoofing / EoP focus |
| OpenAPI / event schemas | Data flows and stores |
| Dependency and build path notes | Supply chain handoff |
| Prior incidents / findings | Recurring themes |

If hosts/APIs are unknown: run `recon-and-methodology` (authorized), then resume.

### 3. Draw the model (DFD + trust boundaries)

1. **External entities:** users, admins, partners, batch clients, attackers as
   external actors (label adversary assumptions; do not personate real people).
2. **Processes:** services, workers, serverless functions, agents, CLIs.
3. **Data stores:** DB, cache, object storage, queues, secrets stores, logs.
4. **Data flows:** sync/async, protocol class (HTTPS, gRPC, queue, WS).
5. **Trust boundaries:** internet ↔ edge, edge ↔ app, app ↔ data, tenant ↔
   tenant, admin plane ↔ user plane, CI ↔ runtime, third-party ↔ org.
6. Produce **at least two levels** if complex: context (L0) and one L1 for the
   change under review.
7. Mark **high-value assets**: credentials, PII, money movement, admin actions,
   signing keys, model weights, export pipelines.

Keep diagrams in version control next to the design doc; re-export when topology changes.

### 4. STRIDE analysis (workshop loop)

For **each** element that crosses or sits on a trust boundary:

1. Walk **S-T-R-I-D-E** with the table above; skip only with a written “N/A + why.”
2. For each plausible threat, capture a **threat entry**:

   | Field | Content |
   | --- | --- |
   | ID | Stable id (`TM-042`) |
   | Element | DFD node/edge |
   | STRIDE | One primary category (note secondaries) |
   | Description | Who does what to what asset |
   | Preconditions | Trust assumption that must fail or be weak |
   | Impact | Confidentiality / integrity / availability + business |
   | Likelihood | Org scale (H/M/L or numeric) |
   | Existing controls | AuthZ, crypto, validation, rate limit, audit… |
   | Proposed mitigation | Design or control change |
   | Status | Open / mitigated / accepted / transferred |
   | Owner + due | Named human, date |

3. Prefer **concrete scenarios** over category labels alone  
   (“attacker replays admin JWT from log leak” beats “spoofing”).
4. Avoid pure exploit recipes; stop at **abuse condition + control gap**.
5. Deduplicate: one root cause → one entry with multiple STRIDE tags if needed.

### 5. Risk rank and decide

1. Score with the **org’s** risk matrix (do not invent a second scale if one exists).
2. Bucket work: **block release**, **fix this quarter**, **backlog**, **accept with sign-off**.
3. For accepted risk: record approver, expiry/review date, and compensating detection.
4. Map mitigations to owners: architecture, app code, platform, process, vendor.

### 6. Link mitigations to delivery

| Mitigation type | Next skill / action |
| --- | --- |
| Secure implementation, validation, authZ | `code-quality-standards` |
| Secrets storage, injection at runtime, rotation | `secrets-management-hygiene` |
| Dependency trust, SBOM, provenance | `sbom-and-supply-chain` |
| Audit completeness, no secret-in-logs | `logging-message-style` |
| Authorized verification of residual risk | `recon-and-methodology` → class skills |
| CI gates for controls | `ci-cd-pipeline-patterns` (if present) |

Write mitigations as **testable requirements** (“admin export requires MFA +
audit event with actor id”), not slogans (“be secure”).

### 7. Close the workshop and maintain the model

1. Publish: diagrams + threat register + decision log in the team’s SSOT (wiki/repo).
2. Attach model version to the **release checklist** or ADR for the change.
3. **Triggers to reopen:** new trust boundary, new data class, new admin surface,
   auth change, third-party integration, public exposure, major dependency shift.
4. Retire threats that no longer apply; never leave stale “open” items without owners.

## Workshop Facilitation Tips

- Time-box STRIDE per element (e.g., 5–8 minutes); park deep dives in a parking lot.
- Require multi-role attendance: eng + product + (security or experienced reviewer).
- Challenge “the WAF/mesh will handle it” — name the control and residual cases.
- Separate **safety/abuse** debates from **authZ/data** threats when product is AI-heavy
  (`ai-ml-security` for ML-specific context).
- End with **top 5** risks visible to leadership; keep full register for builders.

## Example Threat Entries (illustrative)

| ID | STRIDE | Sketch |
| --- | --- | --- |
| TM-01 | S | Partner webhook accepts unsigned callbacks → spoofed events |
| TM-02 | T | Client-supplied `total` honored server-side → price tampering |
| TM-03 | R | Admin delete lacks immutable audit actor/time → repudiation |
| TM-04 | I | Debug endpoint returns full config including secrets path refs |
| TM-05 | D | Unbounded export job fan-out → resource exhaustion |
| TM-06 | E | Role claim from client JWT trusted without server session bind |

## Anti-Patterns

- One giant “system is spoofable” line with no element or mitigation
- Threat model after ship with no change control link (theater)
- Listing CVEs instead of **system-specific** abuse of *this* design
- Ignoring trust boundaries (everything inside VPC treated as trusted)
- Accepting Critical residual risk without named approver and review date
- Workshop without data classification (“everything is sensitive” or nothing is)
- Converting the session into live exploitation of production

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| STRIDE workshop, DFD, design-time threat register, 威胁建模 | **This skill** | — |
| Missing asset/API inventory before modeling | `recon-and-methodology` | this skill after map |
| Implementing mitigations in application code | `code-quality-standards` | this skill for requirements |
| Secrets, vault, .env, rotation controls from model | `secrets-management-hygiene` | this skill |
| Dependency / build / SBOM risks from model | `sbom-and-supply-chain` | this skill |
| Audit/repudiation/log leakage mitigations | `logging-message-style` | this skill |
| ML/LLM product-specific threats | `ai-ml-security` | this skill for STRIDE structure |
| Confirmed vuln class to test residual risk | Matching class skill | `recon-and-methodology` |

### Routing notes (required helpers)

- **`code-quality-standards`:** always apply when mitigations become code.
- **`logging-message-style`:** when threats involve disclosure via logs or weak audit (R/I).
- **`sbom-and-supply-chain`:** when threats involve dependency or build provenance.
- **`recon-and-methodology`:** when the workshop needs an authorized surface map first,
  or when residual risks enter structured security testing.

## Checklist

- [ ] Authorization / org ownership of the SUM confirmed
- [ ] Scope, exclusions, assumptions, owners, and model version recorded
- [ ] Inputs gathered (design, data class, auth matrix); recon completed if needed
- [ ] DFD L0/L1 with trust boundaries and high-value assets
- [ ] STRIDE applied per relevant element; N/A entries justified
- [ ] Threat register complete (id, impact, controls, mitigation, owner, status)
- [ ] Risks ranked with org matrix; acceptances signed with review date
- [ ] Mitigations written as testable requirements and routed (code / secrets / SBOM / logging / test)
- [ ] Artifacts published to SSOT; release or ADR link present
- [ ] Reopen triggers defined; no unowned open Critical/High items
- [ ] Reports redacted (no live secrets/PII); methodology not turned into off-scope attacks

## Rules

- Methodology and design risk first; authorized verification second.
- Evidence from architecture and controlled review beats generic threat lists.
- One primary category per entry; link related entries instead of mega-threats.
- Residual risk is a decision, not silence — record who accepted what until when.
- Keep diagrams and registers versioned next to the system they describe.
- Do not expand modeling into unauthorized offensive operations against third parties.
---

# Note

This skill is the **design-time front door** for structured STRIDE workshops.
When a threat becomes a concrete vulnerability test or implementation task,
switch primary skill and keep the threat id as the traceability key.
