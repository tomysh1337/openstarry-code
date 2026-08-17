---
name: incident-runbook-writing
description: >
  Author and review operational incident runbooks: clear scope, severity,
  symptoms, diagnostics, mitigation steps, escalation, and communications.
  Use when runbook, incident response doc, 故障手册, on-call playbook, SEV
  ladder, incident procedure, pager runbook, or post-alert operator steps.
---

# Incident Runbook Writing

Write **actionable incident runbooks** that an on-call engineer can execute under
stress: what is broken, how severe it is, how to confirm, what to do (and not
do), whom to call, and how to close out. Prefer the organization’s existing
incident severity model, ticket templates, and chat/bridge norms over inventing
a parallel IR process.

## Use When

- Authoring or revising an **incident runbook / on-call playbook** for a service
  or alert
- Defining **severity levels**, escalation paths, and decision points
- Turning tribal knowledge into **ordered diagnostic and mitigation steps**
- Linking **alerts, dashboards, and dashboards’ queries** to operator actions
- Preparing runbooks as part of launch readiness, SLO work, or post-incident
  follow-up
- User mentions: runbook, incident response doc, 故障手册, 应急预案, on-call
  playbook, SEV, severity matrix, pager runbook, incident procedure, 值班手册

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Designing metrics, traces, alert signals | `observability-metrics-tracing` |
| Log message templates and field redaction | `logging-message-style` |
| Secret leak containment / rotation procedure detail | `secrets-management-hygiene` |
| Application code fix quality | `code-quality-standards` |
| Env/config contract design (12-factor) | `env-config-12factor` |
| User-facing status page copy only | `error-message-ux-writing` (with comms lead) |
| Full security engagement planning | `recon-and-methodology` |

## Repo Config First

Org IR standards and in-repo ops docs **outrank** this skill’s defaults.

1. **Severity model:** existing SEV-0/1/2 or P1–P4 definitions, customer-impact
   tables, and executive notification rules — **reuse labels exactly**
2. **Incident process:** who declares incidents, bridge links, roles (IC,
   comms, scribe), handoff hours, status page owners
3. **Doc location:** `docs/runbooks/`, service catalog, Notion/Confluence,
   PagerDuty runbook URL field — put the canonical link where the alert points
4. **Alert ↔ runbook wiring:** alert rule annotations (`runbook_url`), Grafana
   panel links, error-budget policy — update the link when the doc moves
5. **Access & tools:** break-glass, cloud consoles, kubectl contexts, feature
   flag admin, deploy pipelines — document **named** tools the team already uses
6. **Secrets and credentials:** how operators obtain short-lived access; never
   paste long-lived keys into the runbook body (`secrets-management-hygiene`)
7. **Telemetry:** dashboards, log queries, trace views already marked golden
   for the service (`observability-metrics-tracing`)
8. **Neighboring runbooks:** copy structure from the best service runbook in the
   org; stay consistent so on-call can skim any service the same way

**Precedence:** Follow org IR and existing templates when they conflict with
sections below. Surface missing severity definitions, alerts without runbook
links, or runbooks that require prod secrets in plaintext.

## Runbook Goals

| Goal | Operator experience |
| --- | --- |
| **Fast orientation** | Within 1 minute: what this covers, severity, user impact |
| **Confirm before mutate** | Diagnostics prove the symptom before risky mitigation |
| **Ordered actions** | Numbered steps; explicit “stop and escalate if…” |
| **Safe defaults** | Prefer reversible mitigations; call out data-loss risks |
| **Complete handoff** | Escalation contacts, comms templates, next-update cadence |
| **Learning loop** | Link to post-incident process and known failure modes |

## Canonical Structure

Use this skeleton unless the org template already defines sections (then map
1:1 and fill gaps).

```markdown
# [Service / Symptom] Runbook

## Metadata
- Service / component:
- Owner team / Slack:
- Severity guidance: (link to org SEV table)
- Related alerts: (names + links)
- Dashboards / logs / traces: (links)
- Last reviewed: YYYY-MM-DD
- Reviewer:

## Summary
One short paragraph: what breaks, who feels it, what “healthy” looks like.

## Symptoms
- User-visible:
- Alert / metric:
- Error signatures (stable codes, not raw secrets):

## Impact And Severity
| SEV | Criteria (this service) | Response expectations |
| … | … | … |

## Before You Start
- Access required:
- Do NOT: (dangerous actions)
- Declare incident if: …

## Diagnostics (read-only first)
1. …
2. …

## Mitigation / Remediation
### Immediate (stop the bleeding)
1. …
### Durable (fix root cause)
1. …

## Escalation
| Condition | Contact / channel | Notes |
| … | … | … |

## Communications
- Internal update template
- External / status page (who approves)

## Rollback / Recovery Verification
- How to confirm green
- How long to watch

## Cleanup And Follow-Up
- Ticket fields, postmortem link, runbook gaps

## References
- Architecture, dependencies, feature flags, prior incidents
```

## Severity Writing

Define **service-specific criteria** that map to the **org-wide** SEV ladder.
Do not invent a private severity language.

| Element | Guidance |
| --- | --- |
| Impact axes | User-facing downtime, data loss/corruption, security exposure, revenue path, employee-critical internal tools |
| Scope | % users, regions, tenants, or critical accounts — use measurable thresholds when known |
| Urgency | Time-to-fix expectations, executive notification, 24/7 vs business hours |
| Examples | 2–4 concrete examples per SEV for *this* service |
| Non-examples | What looks scary in metrics but is SEV-low (expected batch lag, single-AZ test) |

**Good severity line:** “SEV-1: checkout 5xx > 5% for 10m **or** payment
provider hard-down affecting all cards.”  
**Bad severity line:** “SEV-1: anything important” (not decidable under stress).

## Workflow

### 1. Identify the runbook unit

1. Prefer **one primary user journey or alert family** per runbook (e.g.
   “checkout latency”, “auth login failures”), not an entire platform wiki.
2. List dependencies (DB, cache, payment, identity) and which team owns them.
3. Find existing alerts and dashboards; note gaps for
   `observability-metrics-tracing` follow-up rather than inventing fake panels.

### 2. Pull org standards

1. Copy severity names, IR roles, and comms cadence from org IR docs.
2. Locate the canonical doc store and alert annotation field for `runbook_url`.
3. Confirm secret/access patterns (`secrets-management-hygiene`) — link to vault
   or break-glass **procedures**, do not embed credentials.

### 3. Draft symptoms and diagnostics

1. Write **symptoms** as operators see them: alert name, graph shape, user
   reports, log `code=` / event names (`logging-message-style` stable events).
2. Diagnostics are **read-only first**: dashboards, traces, logs, status of
   dependencies, recent deploys/flags.
3. Each diagnostic step: **what to open**, **what good looks like**, **what bad
   looks like**, **next branch**.
4. Include correlation ids / request examples only as **redacted** patterns.

### 4. Draft mitigation with safety rails

1. Order by **blast radius**: feature flag off → traffic shed → rollback →
   scale → data repair (data repair last and dual-controlled when risky).
2. For each step: command or UI path, expected result, rollback of the
   mitigation itself, and **stop conditions**.
3. Mark steps that change prod state with **“changes production”**.
4. Link config/env changes to `env-config-12factor` contracts (which key, where
   set, restart needed?) without pasting secret values.
5. For code/config fixes, note that implementation must meet
   `code-quality-standards` — the runbook points to the PR process, not a
   pastebin of unreviewed scripts.

### 5. Escalation and communications

1. Table: condition → people/channel → what to hand them (dashboard, timeline).
2. Internal update template: impact, status, next check-in time, IC name.
3. External/status: who has authority; never freestyle legal commitments.
4. Security/privacy incidents: escalate per security IR; redact in public
   channels.

### 6. Verification and exit criteria

1. Explicit **definition of healthy** (SLI back within threshold for N minutes,
   error budget, queue depth, synthetic check).
2. Watch window after mitigation (e.g. 30–60m) before resolving the incident.
3. Cleanup: disable temporary overrides, re-enable probes, rotate credentials
   if exposed (`secrets-management-hygiene`).

### 7. Review and wire-up

1. Dry-run with another engineer (game day or tabletop).
2. Link from alert, service catalog, and README ops section.
3. Set **last reviewed** date; schedule review after major incidents or quarterly.
4. File gaps: missing metrics (`observability-metrics-tracing`), missing logs
   (`logging-message-style`), unsafe secret handling.

## Writing Quality Bar

| Do | Don't |
| --- | --- |
| Numbered steps, one action per step | Walls of narrative paragraphs only |
| Exact alert/dashboard names and links | “Check the metrics” with no link |
| Copy-pasteable commands with placeholders `<cluster>` | Unlabeled screenshots as the only truth |
| Explicit permissions / roles needed | Assume everyone is cluster-admin |
| Time bounds (“if not improved in 15m…”) | Open-ended “keep trying” |
| Redact secrets, tokens, personal data | Paste real connection strings or customer PII |
| Record **who** decides SEV and customer comms | Leave severity to pure guesswork |

Commands should use **placeholders** and point to org-approved tooling. Prefer:

```bash
kubectl --context <staging-or-prod-context> -n <namespace> get pods -l app=billing
```

over undocumented one-off binaries.

## Good / Bad Examples

### Severity criteria (service-local mapping)

**Good**

```markdown
## Impact And Severity

Maps to org SEV model: https://wiki.example/ir/severity

| SEV | This service (billing-api) | Expectation |
| --- | --- | --- |
| SEV-1 | Checkout/payment success rate < 95% for 10m, or complete API hard-down in any region | Immediate bridge; page primary + secondary; customer comms within 30m |
| SEV-2 | Elevated 5xx 1–5% or p99 > 2s for 15m with user reports | Page primary; update every 30m |
| SEV-3 | Single non-critical endpoint errors; no material conversion drop | Work in business hours; ticket |
| SEV-4 | Cosmetic / docs / non-prod only | Backlog |

Non-example: synthetic canary flake < 5m with no user reports → do not auto SEV-1.
```

**Bad**

```markdown
## Severity
- High if bad
- Low if not that bad
```

### Diagnostics before mutate

**Good**

```markdown
## Diagnostics
1. Open [billing RED dashboard](…). Confirm `http_server_requests` error ratio
   and latency. **Good:** error ratio < 1%, p99 < 300ms.
2. Check [deploy timeline](…). Note last prod deploy/flag change ±2h.
3. In logs, filter `event=payment_capture_failed` with `code=`  
   (`logging-message-style` stable codes). **Do not** log/export raw PANs.
4. Trace a failing `requestId` from support ticket in APM  
   (`observability-metrics-tracing`). Identify slow dependency span.
5. If dependency is payments-provider: open provider status page + our
   outbound error metric. If provider-down → jump to Mitigation B.
```

**Bad**

```markdown
## Fix
Restart all pods and hope. Also run random SQL until it works.
```

### Mitigation with stop conditions

**Good**

```markdown
## Mitigation

### A. Recent deploy suspected (changes production)
1. Confirm version on [release board](…) matches suspect SHA.
2. **Rollback** via standard pipeline to previous healthy tag  
   (see deploy runbook). Do not `kubectl replace` ad-hoc unless pipeline is down.
3. Watch error ratio 15m. If still high → leave rollback in place; go to B.
4. **Stop:** If rollback fails or version is unclear, escalate to @billing-lead
   before manual image overrides.

### B. Bad feature flag
1. Open flag console; disable `payments.new_router` for 100% (kill switch).
2. Verify flag eval metric shows off; recheck RED dashboard.
```

**Bad**

```markdown
Delete the database PVC if restarts do not help.
# no confirmation, no owner, no data-loss callout
```

### Communications template

**Good**

```markdown
## Communications

Internal (Slack #inc-billing), every 30m or on state change:
- **Impact:** …
- **Scope:** region/tenants/%
- **Status:** investigating | mitigating | monitoring
- **Cause (known/suspected):** …
- **Next update:** HH:MM UTC
- **IC:** @name

External: only Comms lead via status page template; no root-cause speculation.
```

**Bad**

```markdown
Tweet that we are hacked. Paste stack traces with tokens into public Slack.
```

### Metadata and links

**Good**

```markdown
## Metadata
- Service: billing-api
- Alerts: `BillingAPIHighErrorRate`, `BillingAPIP99High`
- Runbook URL (for alert annotation): https://…/runbooks/billing-api-errors
- Dashboard: https://…/d/billing-red
- Logs: https://…/explore?q=event%3Dpayment_*
- Last reviewed: 2026-06-01
```

**Bad**

```markdown
See #general for vibes. Dashboard is somewhere in Grafana.
```

## Anti-Patterns

- Runbook is a **design doc** with no steps
- Only **mitigation**, no diagnostics → wrong fix under pressure
- **Secret values**, private keys, or customer PII embedded in the page
- Steps that require **personal** cloud keys instead of SSO/break-glass roles
- Alert fires with **no link** to this runbook
- Severity criteria copied from another company and never mapped to org SEV
- Undated runbook last touched years ago; commands for decommissioned tooling
- “Restart everything” as step 1 for every symptom
- No **exit criteria** → incident never cleanly ends
- Blaming individuals in the runbook text; keep it systems-focused
- Mixing **security IR** covert steps into a public eng wiki without redaction

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Runbook structure, severity text, operator steps, 故障手册 | **This skill** | — |
| Which metrics/traces/alerts should exist for the symptoms | `observability-metrics-tracing` | this skill for operator narrative |
| Stable log events/fields used in diagnostic queries | `logging-message-style` | this skill for which queries to paste |
| Credential leak, vault, rotation during incident | `secrets-management-hygiene` | this skill for IR structure around the leak |
| Code/config change quality after mitigation | `code-quality-standards` | this skill for when to change vs roll back |
| Env/config keys involved in misconfig incidents | `env-config-12factor` | this skill for diagnosis/mitigation framing |
| Image/runtime packaging issues | `dockerfile-best-practices` | this skill if the incident response needs image rollback steps |
| Feature flag kill switch detail | `feature-flag-patterns` | this skill for ordering in the incident |

### Routing notes (required helpers)

- **`observability-metrics-tracing`:** runbooks depend on golden signals,
  dashboards, and correlation ids; fix missing telemetry as follow-up work, and
  link real panels from the runbook.
- **`logging-message-style`:** diagnostic steps should filter on stable `event`
  and `code` fields — not free-text that changes every deploy.
- **`secrets-management-hygiene`:** any runbook touching credentials must
  rotate/revoke safely and never store secret values in the doc.
- **`code-quality-standards`:** durable fixes land through normal review/test;
  emergency changes still need tracked follow-up and verification.
- **`dockerfile-best-practices`:** when mitigation is image rebuild/rollback or
  when the incident root cause is secrets/config baked into layers.

## Checklist

- [ ] Org SEV model, IR roles, doc home, and alert `runbook_url` field identified
- [ ] Title/scope matches one alert family or user journey (not the whole company)
- [ ] Metadata: service, owners, links, last reviewed date
- [ ] Summary states impact and healthy baseline in one short paragraph
- [ ] Symptoms listed for users, alerts, and log/trace signatures (redacted)
- [ ] Severity table maps **this service** to **org** SEV with examples/non-examples
- [ ] Before-you-start: access needs, declare-incident criteria, explicit “do not”
- [ ] Diagnostics are read-only first; each step has good/bad signals and branches
- [ ] Mitigations ordered by blast radius; production-changing steps labeled
- [ ] Stop/escalate conditions and time bounds on waiting
- [ ] Escalation table with channels and handoff contents
- [ ] Comms templates (internal cadence; external authority)
- [ ] Verification / exit criteria and post-mitigation watch window
- [ ] No secrets or PII in the runbook; secret actions link to hygiene procedures
- [ ] Alert, catalog, and dashboard link **to** this runbook
- [ ] Tabletop or second-engineer review done (or scheduled)
- [ ] Follow-ups filed: telemetry (`observability-metrics-tracing`), logs
      (`logging-message-style`), config (`env-config-12factor`), code
      (`code-quality-standards`) as needed

## Rules

- **Repo/org IR first** — same SEV words, same roles, same doc system.
- Write for **tired humans at 03:00**: short steps, links, stop conditions.
- **Diagnose before destructive fix**; prefer reversible mitigations.
- Never put **live secrets** or customer PII in runbooks; use placeholders and
  vault procedures (`secrets-management-hygiene`).
- Every paging alert deserves a **runbook URL**; every runbook needs a
  **review date**.
- Runbooks are **operations products** — update them as part of incident close
  and major releases, not only when something has already burned.
---

# Note

This skill owns **incident runbook structure and operator-facing procedure
writing**. Pair with `observability-metrics-tracing` for signals and dashboards,
`logging-message-style` for diagnostic field stability,
`secrets-management-hygiene` for credential incidents,
`env-config-12factor` for misconfig/env contracts,
`dockerfile-best-practices` when images/rollbacks are involved, and
`code-quality-standards` for durable code fixes after the fire is out.
