---
name: security-champion-program
description: >
  Design and run an organizational security champion program: role definitions,
  selection, training paths, office hours, metrics, and escalation between
  product teams and AppSec. Use when security champions, AppSec champions,
  federated security program, champion RACI, security office hours, or building
  distributed security ownership inside engineering orgs.
---

# Security Champion Program

Design a **security champion program** that embeds practical security ownership
in product teams without making every engineer full-time AppSec. **Org process
design** (roles, enablement, rituals, metrics, escalation) — not exploit work.

## When To Use

- Standing up or refreshing a **security champion** / federated AppSec network
- Defining **champion roles**, time allocation, and RACI with central AppSec
- Building **training**, office hours, review habits, and first-pass triage
- Choosing **program metrics** and **escalation** paths to AppSec / IR
- Mentions: security champions, AppSec champions, federated security, security
  guild, office hours, 安全大使, 安全冠军

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| SSDLC phase gates / release policy | `secure-sdlc-checklist` |
| STRIDE workshop facilitation | `threat-modeling-stride` |
| SAST/DAST operation and triage | `sast-dast-tooling-usage` |
| Incident runbook / SEV operator steps | `incident-runbook-writing` |
| Implementation hardening / recon | `code-quality-standards` / `recon-and-methodology` |

## Scope And Principles

- **In scope:** Org-owned teams; champions; training; office hours; metrics;
  escalation SLAs; recognition and capacity protection.
- **Out of scope:** Unauthorized third-party testing; unpaid heroics replacing
  AppSec hiring; champion as default SEV-1 on-call.
- Org policy, risk matrix, and existing SDLC gates **outrank** generic templates.
- Champions **amplify** AppSec; they alone do not accept Critical residual risk.
- **Coverage:** one champion per squad/domain + backup; avoid multi-domain sprawl.

## Core Roles

| Role | Owns | Does not own |
| --- | --- | --- |
| **Champion** (per squad/domain) | Local questions, PR security habits, first-pass scanner triage, training relay, early risk tickets | Org policy, Critical risk accept, IR command |
| **AppSec** | Standards, tools, deep threat work, exceptions, severity SLAs, coaching | Day-to-day feature delivery for every squad |
| **Eng manager** | Time protection, gate adherence, security debt priority | Being the sole security expert |
| **Product / risk acceptor** | Written business risk accept + review date | Technical control design alone |

## Workflow

### 1. Charter and sponsorship

1. One-page **charter**: purpose, in/out of scope, time budget (e.g. 10–20% or
   fixed hours/sprint), success criteria for 2–3 quarters.
2. Secure a **sponsor** who protects time and credits champion work in reviews.
3. Align to `secure-sdlc-checklist` so champions enforce existing gates — not a
   parallel process.
4. Publish RACI: design review, scanner findings, exceptions, incidents, vendors.

### 2. Select and onboard

1. Prefer **influential volunteers** (senior IC/tech lead) with manager sign-off.
2. **Onboard kit:** severity model, lite threat-model checklist, secure PR
   checklist, tool access, escalation contacts, secrets/PII redaction norms.
3. Pair with AppSec 2–4 weeks (shadow office hours; co-review one high-risk PR).
4. Keep a **roster**: team, backup, start date, training stage.

### 3. Training path

| Stage | Focus | Outcome |
| --- | --- | --- |
| Foundations | Data class, authZ, secrets, log redaction, SSDLC gates | Spots high-risk changes |
| Domain track | Web/API, cloud, mobile, data/ML as relevant | Applies local checklists |
| Facilitation | Prep for `threat-modeling-stride` workshops | Escalates with DFDs |
| Continuous | Brown-bags, postmortem themes, FP clinics | Skills stay current |

Pair with `code-quality-standards` and `secrets-management-hygiene`; add class
skills only when the team surface requires them.

### 4. Rituals

1. **AppSec office hours** (weekly): designs, PR questions, exception drafts —
   not full IR bridges.
2. **Planning loop:** champion flags high-risk stories (auth, money, admin, PII,
   new trust boundaries).
3. **PR habit:** high-risk PRs get checklist review; deep issues escalate with
   evidence.
4. **Champion guild** (monthly): patterns, tool pain, top risks — action-logged.
5. Document office hours vs ticket vs SEV path.

### 5. Escalation

| Trigger | Path |
| --- | --- |
| Design uncertainty / new boundary | Champion prep → AppSec / `threat-modeling-stride` |
| Suspected Critical in owned system | Champion → AppSec triage → IR if active exploit |
| Scanner Critical/High | Champion first-pass → AppSec on dispute (org SLA) |
| Residual risk accept | Draft → product + AppSec + named acceptor + expiry |
| Third-party / no auth | **Stop** — vendor/legal process only |

### 6. Metrics and sustainability

| Metric | Why |
| --- | --- |
| Coverage (% squads with named + backup) | Blind spots |
| Time budget honored | Burnout prevention |
| High-risk changes with design/threat-model link | Shift-left quality |
| Median High → owned ticket with due date | Flow, not heroics |
| Office-hours unblock rate; exception age | Enablement + risk hygiene |

Avoid ranking teams by raw finding volume. Recognize wins; rotate/backfill with
handoff after 12–18 months; champions are not default SEV-1 page.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Champion program, roles, training, office hours, metrics | **This skill** | — |
| Lifecycle gates champions enforce | `secure-sdlc-checklist` | this skill (people model) |
| Deep STRIDE workshops | `threat-modeling-stride` | this skill (who prepares) |
| Scanner triage playbooks | `sast-dast-tooling-usage` | this skill (first-pass owner) |
| Incident operator procedures | `incident-runbook-writing` | this skill (champion vs IR) |
| Code fixes / secure review quality | `code-quality-standards` | always on code changes |

## Output Checklist

- [ ] Charter, sponsor, time budget, and success criteria documented
- [ ] RACI published (champion / AppSec / EM / risk acceptor)
- [ ] Roster with coverage and backups; selection criteria applied
- [ ] Onboard kit and staged training path defined
- [ ] Office hours + guild rituals scheduled and scoped
- [ ] Escalation table covers design, findings, accept risk, active incident
- [ ] Metrics set (coverage, capacity, flow, exceptions) — not vanity-only
- [ ] Recognition and burnout guards (rotation, no default SEV page)
- [ ] Linked to SSDLC/tool playbooks (no shadow process); owned systems only for active testing
