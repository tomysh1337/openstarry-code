---
name: xxe-billion-laughs-defenses
description: >
  Defensive guidance and authorized assessment for XML external entity (XXE)
  and billion-laughs / entity-expansion DoS: parser hardening, DTD policy,
  expansion limits, and safe stack configuration. Use when hardening or
  retesting XML/SOAP/SAML/SVG/Office parsers against XXE and entity bombs.
---

# XXE And Billion-Laughs Defenses

Defense-primary skill for **XXE** (external entity / SSRF / file read via DTD)
and **billion laughs** (entity expansion DoS). Offensive XXE chains →
`xxe-xml-external-entity`.

## Scope And Authorization

- Owned apps, libraries, labs, CTFs, or engagements that explicitly allow XML
  parser security testing or hardening review.
- No weaponized XXE/entity bombs against third parties; no unthrottled DoS on
  shared production parsers; no bulk metadata/internal scans without approval.
- Prefer canary proofs (tiny markers, lab OAST you control). Expansion tests:
  strict size/time budgets; stop at first reliable reject/timeout.
- Keep original configs immutable; redact secrets, internal hosts, OAST tokens.
- Do not infer authorization from “looks like a CTF.”

## Use When

- Task is harden / remediate / review parsers against XXE or entity bombs.
- Code uses `DocumentBuilderFactory`, `SAXParser`, `XmlReader`, `lxml`, SOAP,
  SAML, SVG, or OOXML processors on untrusted input.
- Need secure flags, expansion limits, or retest criteria after a fix.

## When To Use

- After an XXE finding when the ask is fix + verify.
- Import, SOAP, SAML, RSS/Atom, SVG upload, or Office convert pipelines.
- Symptoms: parser OOM, multi-second parse of tiny XML, unexpected egress on ingest.
- **Not primary:** pure LFI without XML (`path-traversal-lfi`); pure HTTP SSRF
  without entities (`ssrf-server-side-request-forgery`); MIME-only upload issues
  (`upload-insecure-files` / `file-upload-polyglot-detection`).

## Workflow

### 1. Inventory

List untrusted XML entrypoints (API, SOAP, SAML, upload, MQ). Record library,
version, privilege, egress, and timeouts.

### 2. Baseline

Parse benign schema-valid XML (no attacker DOCTYPE). Snapshot configs. Confirm
business feature still works.

### 3. Hardening (apply in order)

1. Prefer non-XML where product allows.
2. **Disable DTDs** when unused (`DISALLOW_DOCTYPE_DECL` / equivalent).
3. Else: disable external general/parameter entities; null/`NONET` resolver.
4. Enable secure-processing flags; block external DTD/schema access.
5. Cap entity expansion count/size, document size, depth; set parse timeouts
   and worker memory limits.
6. Least-privilege process + egress allowlist (or deny-all) for parse hosts.
7. SVG/Office: re-encode/strip; treat package XML as untrusted (upload stage →
   `upload-insecure-files`).

### 4. Stack direction

| Stack | Hardening |
| --- | --- |
| Java | Secure processing; disable DOCTYPE or external entities on factories |
| .NET | `DtdProcessing.Prohibit`/`Ignore`; `XmlResolver = null` |
| PHP | `LIBXML_NONET`; no external entity expand; size limits |
| Python | Prefer `defusedxml`; never raw `etree` on untrusted input |
| libxml2/lxml | No network; no external subset resolve |
| SAML/SOAP | Vendor secure flags; reject unsolicited DOCTYPE; patch |

Ship shared secure-parse helpers with `code-quality-standards`.

### 5. Authorized retest

- **XXE:** DOCTYPE + external entity to lab OAST or local canary → expect
  reject, no fetch, no file body. Confirm XInclude off if DOCTYPE blocked.
- **Expansion (budgeted):** small nested entities only — expect hard fail,
  timeout within budget, or capped expansion — not multi-GB OOM on shared hosts.

```xml
<!DOCTYPE lolz [
  <!ENTITY lol "lol">
  <!ENTITY lol2 "&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;&lol;">
]>
<root>&lol2;</root>
```

### 6. Regression

Tests: benign OK; DOCTYPE/external entity rejected; oversized expansion
rejected. Monitor parse latency, OOM, unexpected egress. Isolate any legacy
path that still requires DTD (network-off, strict schema).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| XXE + billion-laughs **defenses** | **This skill** | — |
| Offensive XXE (classic/blind/OOB/XInclude) | `xxe-xml-external-entity` | this skill for fix/retest |
| XML/SVG/Office via **upload** | `upload-insecure-files` | this skill + XXE skill |
| Polyglot dual-parse into XML | `file-upload-polyglot-detection` | this skill if entities expand |
| Secure parser helpers / tests | `code-quality-standards` | **always** when coding fix |
| XXE-caused HTTP SSRF framing | `ssrf-server-side-request-forgery` | after entity fetch proven |

**Required routes:** `xxe-xml-external-entity` for exploit-path discovery;
`upload-insecure-files` when files feed the parser; `code-quality-standards`
for shared factories, errors, timeouts, and regression tests.

## Checklist

- [ ] Authorization confirmed; expansion tests budgeted
- [ ] Untrusted XML entrypoints inventoried
- [ ] Benign baseline works without attacker DOCTYPE
- [ ] DTD off **or** external entities + network resolver blocked
- [ ] Secure flags + versions documented
- [ ] Expansion/depth/size limits and parse timeout set
- [ ] Least privilege + egress policy on parser workers
- [ ] Retest: no external fetch; no file leak; bomb rejected/capped
- [ ] XInclude / remote schema includes disabled if unused
- [ ] Upload path covered when files feed parser
- [ ] Fix uses `code-quality-standards` (helper + tests)
- [ ] Monitoring for parse OOM / latency / egress
- [ ] Report: before/after config, redacted evidence, residual DTD isolated

## Rules

- Defense and authorized assessment only.
- Prefer disable-DTD over brittle entity filters; WAF alone is not “safe.”
- Cap DoS proofs; one controlled reject/timeout suffices.
- Redact OAST URLs, file contents, and internal targets.
---

# Note

Own parser hardening for XXE and entity-expansion DoS. Pair with
`xxe-xml-external-entity` (offensive depth), `upload-insecure-files` (file
ingest), and `code-quality-standards` (shipping the fix).
