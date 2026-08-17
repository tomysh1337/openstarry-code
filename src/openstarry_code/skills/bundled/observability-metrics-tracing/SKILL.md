---
name: observability-metrics-tracing
description: >
  Design and review metrics, logs, and traces as one observability system:
  RED/USE at a high level, correlation IDs, cardinality control, and safe
  telemetry. Use when observability, metrics, tracing, OpenTelemetry, APM,
  可观测性, 指标, 链路追踪, Prometheus, span, SLI/SLO signals, or when reviews
  need request correlation across logs and traces. Complements
  logging-message-style (log copy/levels); does not own user-facing error copy.
---

# Observability: Metrics, Logs, Traces

Treat **metrics, logs, and traces** as complementary signals for operators and
SLOs—not three unrelated dumps. Prefer **repo-configured** OpenTelemetry (or
vendor SDK) conventions, controlled cardinality, and correlation IDs over ad-hoc
printf metrics and unlinked log lines.

## Use When

- Adding or reviewing **metrics** (counters, histograms, gauges), **distributed
  tracing** (spans, baggage, sampling), or the **join** between logs and traces
- Defining service SLIs with **RED** (Rate, Errors, Duration) or resource views
  with **USE** (Utilization, Saturation, Errors) at a practical high level
- Propagating **correlation IDs** (`traceId`, `spanId`, `requestId`) across
  HTTP/gRPC/queue workers
- Choosing what *not* to instrument (high-cardinality labels, full payload spans)
- User mentions: observability, metrics, tracing, OpenTelemetry, OTel, APM,
  Prometheus, Grafana, Jaeger, Zipkin, Datadog, New Relic, Honeycomb, Tempo,
  可观测性, 指标, 链路追踪, 监控, 埋点, SLI, SLO, RED, USE

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Log message templates, levels, PII redaction in log fields | `logging-message-style` |
| User-facing error copy / API `message` text | `error-message-ux-writing` |
| General reliability, retries, security, tests in app code | `code-quality-standards` |
| CI pipeline metrics jobs only | `ci-cd-pipeline-patterns` |
| PCAP / network capture forensics | `traffic-analysis-pcap` |

## Repo Config First

Repo and platform observability config **outrank** this skill’s defaults.

1. **Existing SDK & exporter:** OpenTelemetry setup, vendor agent (Datadog,
   New Relic, Elastic APM), Prometheus client, Micrometer, OpenCensus legacy
2. **Naming & resource attributes:** service name, env, version, deployment
   (`service.name`, `deployment.environment`) already used in dashboards
3. **Metric naming conventions:** Prometheus `snake_case` + unit suffixes
   (`_seconds`, `_bytes`, `_total`) vs vendor display names; existing metric
   catalogs / recording rules
4. **Trace context propagation:** W3C `traceparent` / `tracestate`, B3, AWS
   X-Ray header—match what gateways and sidecars already emit
5. **Correlation field names:** `traceId` vs `trace_id`, `requestId` vs
   `x-request-id`—align logs, traces, and API error envelopes
6. **Sampling & retention:** head/tail sampling configs, log retention, metric
   scrape intervals, exemplars policy
7. **Cardinality guards:** banned high-cardinality label lists in platform
   docs; existing relabel/drop rules
8. **Dashboards & alerts:** Grafana/folder ownership, alert severity, runbooks—
   extend existing boards; do not invent a parallel metric namespace

**Precedence:** Follow repo/org telemetry standards when they conflict with
examples below. Surface conflicts that disable tracing in prod without
replacement, log secrets into span attributes, or explode cardinality.

## Core Model (high level)

| Signal | Best for | Avoid using it as |
| --- | --- | --- |
| **Metrics** | Aggregates, SLOs, cheap alerts, capacity | Full forensic detail of one request |
| **Logs** | Discrete events, errors with context, audit | Per-request high-volume INFO spam as a substitute for metrics |
| **Traces** | Latency breakdown, dependency map, one-request path | Unbounded attributes or 100% sample forever without cost plan |

**RED (services / request paths)**

| Signal | Meaning | Typical metric shape |
| --- | --- | --- |
| Rate | Throughput of work | `http_server_requests_total` / QPS |
| Errors | Failed work fraction | `*_errors_total` or status class ratio |
| Duration | Latency distribution | Histogram of latency (`_seconds` bucket) |

**USE (resources: CPU, memory, disk, pool, queue)**

| Signal | Meaning | Typical view |
| --- | --- | --- |
| Utilization | Busy fraction of capacity | CPU %, connection pool in-use / max |
| Saturation | Queue depth / wait / pressure | Thread pool queue, GC pressure, disk wait |
| Errors | Resource-level failures | Disk errors, pool acquire timeouts |

Use RED on **APIs and workers**; USE on **instances, pools, brokers**. Do not
force every subsystem into both blindly—pick the questions on-call must answer.

## Workflow

1. **State the operational questions.** e.g. “Is checkout SLO burning?”, “Which
   dependency added 200ms?”, “Did deploy X raise 5xx?” Instrumentation without
   a question becomes noise.
2. **Inventory repo telemetry.** SDK, service name, existing metrics, trace
   sampling, log correlation fields, dashboards/alerts.
3. **Place correlation first.** Ensure inbound middleware extracts/creates
   `traceId` + `requestId`; bind both on logger context and active span; return
   `requestId` (and optionally `traceId`) on error responses per product policy.
4. **Add RED metrics for the boundary.** Golden signals on HTTP/gRPC/queue
   consumer: rate, error count/ratio, latency histogram. Prefer framework
   auto-instrumentation when the repo already uses it.
5. **Add spans at meaningful boundaries.** Inbound request, outbound client
   calls, DB/queue publish, and important domain steps—not every private
   function. Set span status on failures; record exception once with redaction.
6. **Control cardinality.** Labels/attributes: low-cardinality enums
   (`method`, `route template`, `status_code`, `error_code`, `peer_service`).
   Never use raw user id, email, full URL+query, or unbounded path params as
   metric labels.
7. **Align codes across layers.** Stable domain/API `code` in logs, span
   attributes, and user error payloads (`error-message-ux-writing`) so one
   incident search joins all three.
8. **Wire alerts to symptoms, not every metric.** Alert on SLO burn, error
   rate, saturation—not on every counter tick. Link runbooks.
9. **Verify.** Generate traffic; confirm one request shows the same id in log
   line, span, and (if exposed) client error body; confirm metric label set is
   finite; confirm no secrets in span attributes or log fields.

## Correlation IDs

| ID | Role | Typical source |
| --- | --- | --- |
| `traceId` | Joins all spans of a distributed request | Tracer / W3C `traceparent` |
| `spanId` | Current operation within the trace | Active span |
| `requestId` | Support-facing opaque id (may equal trace id or be separate) | Edge/gateway or app middleware |

**Rules**

- Propagate context across process boundaries (HTTP headers, gRPC metadata,
  queue message attributes). Reconstruct parent links on consumers.
- Bind IDs on the **logger/context** once (`logging-message-style`); do not
  retype them into every message string.
- Prefer **route templates** (`/users/{id}`) in span names and metric labels,
  not concrete ids.
- When APIs return errors, include `requestId` for support; keep user `message`
  free of internal hostnames (`error-message-ux-writing`).

## Instrumentation Practices

### Metrics

- Prefer **histograms** (or timed distributions) for latency; avoid only averages
- Counters for events (`_total`); gauges for levels (queue depth, connections)
- Include `service`, `env` as resource attributes—not necessarily as every label
- Document unit and type next to new metrics in code or metric catalog
- Exemplars (trace id on histogram buckets) when the stack supports them—great
  bridge from “p99 spike” to a concrete trace

### Traces

- **Auto-instrument** frameworks first (HTTP server/client, DB drivers) when stable
- Manual spans for business-critical sections auto-tools miss
- Span attributes: peer service, rpc method, db system, http route, error code
- **Sampling:** production default is rarely 100% forever; use head sample +
  tail sample on errors/slow if available
- Never put passwords, tokens, raw PII, or full bodies into span attributes

### Logs ↔ traces

- Inject `traceId`/`spanId` into structured logs automatically
- Log **once** at the failure boundary with stable event + `code`; let the span
  carry timing of child ops (`logging-message-style`)
- Prefer metrics for “how many”; traces for “why slow”; logs for “what exactly”

## Good / Bad Examples

### Correlation across the stack

**Good**

```text
# inbound middleware
requestId = header(X-Request-Id) or new_ulid()
context = extract_traceparent(headers) or new_trace()
logger = logger.with(requestId, traceId, spanId)
span.set_attributes({ "http.route": "/invoices/{id}", "request.id": requestId })

# error response (user-facing)
{ "code": "INVOICE_CREATE_FAILED", "message": "…", "requestId": "req_…" }

# log (operators)
event=invoice_create_failed code=INVOICE_CREATE_FAILED requestId=req_… traceId=… err=…
```

**Bad**

```text
# three unlinked worlds
log: "failed for user 55a1@example.com"
metric label: user_email=55a1@example.com   # cardinality + PII bomb
span attribute: authorization=Bearer eyJ…   # secret in APM
API body: message=String(exception)         # no requestId, leaks internals
```

### RED metrics on an HTTP API

**Good**

```text
http_server_request_duration_seconds{method="POST", route="/checkout", status_code="200"}
http_server_requests_total{method="POST", route="/checkout", status_code="500"}
# route is the template, not /checkout/user/55a1/cart/99
```

**Bad**

```text
http_server_request_duration_seconds{path="/checkout/user/55a1/cart/99", email="a@b.c"}
# unbounded series; expensive; often unqueryable; privacy risk
```

### Span boundaries

**Good**

```text
SERVER span: POST /checkout
  CLIENT span: payment-service/Charge
  CLIENT span: db/Exec (or auto DB span)
  status=ERROR on failure + attribute error.code=PAYMENT_CARD_DECLINED
```

**Bad**

```text
span for every getter/setter and JSON parse
span events dumping full request/response bodies
child spans without parent context on async handoff (broken traces)
```

### USE for a connection pool

**Good**

```text
db_pool_in_use / db_pool_max          # utilization
db_pool_wait_seconds (histogram)      # saturation signal
db_pool_acquire_errors_total          # errors
```

**Bad**

```text
Only log "got connection" at INFO per request
No metric → page only when users complain
```

### OpenTelemetry-style sketch (illustrative)

**Good**

```python
# pseudo — follow repo’s real OTel setup
with tracer.start_as_current_span("checkout.complete") as span:
    span.set_attribute("http.route", "/checkout")
    span.set_attribute("error.code", code)  # if failed; stable code
    logger.error("checkout_failed", code=code, err=err)  # ids from context
```

**Bad**

```python
print(f"checkout failed {user.email} token={jwt}")
metrics.incr(f"checkout.{user.id}.fail")  # per-user metric names
```

## Anti-Patterns

- Metrics with user ids, emails, or full URLs as labels
- 100% trace sampling of huge services with full body capture and no budget
- Logs without `traceId`/`requestId` while “we have APM” (or the reverse)
- Alerting on raw counters without rate/SLO context (page fatigue)
- Span names that include concrete ids (`GET /users/12345`)
- Double-counting: custom + auto-instrumentation exporting the same metric
  under different names with no deprecation plan
- Using ERROR logs for expected client validation; pollutes error rate if logs
  are scraped into “error” metrics carelessly
- Treating observability as post-incident only—add golden signals with the feature

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Metrics, traces, RED/USE, correlation architecture, 可观测性 | **This skill** | — |
| Log levels, structured fields, redaction, message templates | `logging-message-style` | this skill for trace field join |
| User-facing errors, stable API codes, support `requestId` copy | `error-message-ux-writing` | this skill so codes/ids match telemetry |
| Implementation hygiene, error handling, tests, security | `code-quality-standards` | always on production changes |
| CI wiring for probes/exporters only | `ci-cd-pipeline-patterns` | this skill for what to emit |

Always apply **`code-quality-standards`** when instrumentation lands in product
code. Use **`logging-message-style`** for every new log event. Use
**`error-message-ux-writing`** when the same failure is shown to users—keep UX
strings safe and codes aligned with metrics/span attributes.

## Checklist

- [ ] Repo SDK, service name, exporter, and existing metric/trace conventions identified
- [ ] Operational questions / SLIs listed before new instrumentation
- [ ] `traceId` / `spanId` / `requestId` propagated and bound on logger context
- [ ] RED (or equivalent) on key request/worker boundaries; USE on critical pools/resources
- [ ] Latency as histogram/distribution, not only average
- [ ] Metric labels and span attributes are low-cardinality; no raw PII/secrets
- [ ] Span names and metric routes use templates, not concrete resource ids
- [ ] Failures set span status + stable `error.code` / domain `code`
- [ ] Logs structured per `logging-message-style`; not a substitute for counters
- [ ] User errors per `error-message-ux-writing` include support id; no internal leaks
- [ ] Sampling, retention, and cardinality cost reviewed for prod
- [ ] Dashboards/alerts updated or explicitly deferred with owner; runbook linked for pages
- [ ] Verified one real request joins log ↔ trace ↔ (optional) client `requestId`

## Rules

- Prefer **questions → signals → instrumentation**, not “export everything.”
- Correlation without redaction is a breach waiting to happen—treat span
  attributes like logs.
- Golden signals and correlation IDs are part of the production contract, not polish.
- Repo and platform standards win; this skill fills gaps and review bar only.
- Metrics tell *how much*, traces *where time went*, logs *what happened*—use each for its strength.
