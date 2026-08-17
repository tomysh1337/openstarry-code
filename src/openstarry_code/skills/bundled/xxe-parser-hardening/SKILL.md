---
name: xxe-parser-hardening
description: >
  Hardening XML parsers against XXE by disabling external entities and DTDs
  with language-specific safe defaults (Java, Python, .NET, libxml/lxml, PHP).
  Use when configuring DocumentBuilderFactory, XmlReader, defusedxml, libxml,
  SOAP/SAML/SVG/Office parsers, or remediating XXE via secure parser flags —
  defense and authorized retest only; offensive chains → xxe-xml-external-entity.
---

# XXE Parser Hardening

Configure **XML parsers** so untrusted input cannot resolve external entities,
load remote DTDs, or open `file://` / internal URLs. Defense-primary: safe
defaults and shared factory helpers. Exploit methodology →
`xxe-xml-external-entity`. Entity-expansion DoS → `xxe-billion-laughs-defenses`.

## Scope And Authorization

- **In scope:** Owned apps, libraries, staging, labs, CTFs, or engagements that
  allow parser config review and hardening.
- **Out of scope:** Weaponized XXE on third parties; bulk internal/metadata
  probes without approval; unthrottled DoS on shared production parsers.
- Prefer canary proofs (tiny markers, lab OAST you control). Keep originals
  immutable; redact secrets, internal hosts, and OAST tokens.
- Do not infer authorization from “looks like a sandbox.”

## When To Use

- Task is **harden / remediate / review** XML parser flags (not hunt exploit paths).
- Code uses `DocumentBuilderFactory`, `SAXParserFactory`, `XMLInputFactory`,
  `XmlReader` / `XmlDocument`, `lxml`, `etree`, `libxml2`, SOAP/SAML, SVG, or
  OOXML processors on untrusted input.
- Need concrete **disable DTD / external entity** settings per stack, or retest
  after a fix.

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Classic / blind / OOB / XInclude XXE testing | `xxe-xml-external-entity` |
| Billion-laughs expansion limits and DoS budgets | `xxe-billion-laughs-defenses` |
| Pure path LFI without XML | `path-traversal-lfi` |
| Pure HTTP SSRF without entities | `ssrf-server-side-request-forgery` |
| Upload MIME / polyglot stage | `upload-insecure-files` / `file-upload-polyglot-detection` |

## Workflow

### 1. Inventory parsers

List every untrusted XML entrypoint (API body, SOAP, SAML, upload SVG/Office,
MQ). Record library, version, process privilege, network egress, and timeouts.

### 2. Safe default policy (apply in order)

1. Prefer non-XML (JSON) where the product allows.
2. **Disable DTD / DOCTYPE** entirely when the schema does not require it.
3. If DTD is required: disable **external** general and parameter entities;
   set resolver to null / `NONET`; never resolve remote schemas from untrusted docs.
4. Enable secure-processing / equivalent; turn off XInclude unless required.
5. Cap document size, depth, and parse time; least-privilege OS user + egress
   allowlist (or deny-all) for parse workers.
6. Centralize one **secure parse helper**; ban ad-hoc factories
   (`code-quality-standards`).

### 3. Language defaults

| Stack | Safe direction |
| --- | --- |
| **Java** | `FEATURE_SECURE_PROCESSING`; `disallow-doctype-decl` **or** disable external general/parameter entities on `DocumentBuilderFactory` / `SAXParserFactory` / `XMLInputFactory`; `setXIncludeAware(false)`. Shared factory only. |
| **Python** | Prefer **`defusedxml`**. Never parse untrusted input with raw `xml.etree.ElementTree`, default `lxml.etree`, or `minidom` without defused wrappers. |
| **.NET** | `XmlReaderSettings`: `DtdProcessing = Prohibit` (or reviewed `Ignore`); `XmlResolver = null`. Prefer `XmlReader` over default-resolver `XmlDocument`. |
| **libxml2 / lxml** | `XML_PARSE_NONET` / no network; no external subset resolve; no custom URL resolvers; pair with size limits. |
| **PHP** | `LIBXML_NONET`; no entity expansion for untrusted docs; size/time limits at boundary. |
| **SAML / SOAP** | Vendor secure flags; reject unsolicited DOCTYPE; patch libraries; same settings as host stack. |

Illustrative snippets (verify against current library docs):

```java
DocumentBuilderFactory dbf = DocumentBuilderFactory.newInstance();
dbf.setFeature(XMLConstants.FEATURE_SECURE_PROCESSING, true);
dbf.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
dbf.setXIncludeAware(false);
dbf.setExpandEntityReferences(false);
```

```csharp
var settings = new XmlReaderSettings {
    DtdProcessing = DtdProcessing.Prohibit, XmlResolver = null };
using var reader = XmlReader.Create(stream, settings);
```

```python
from defusedxml import ElementTree as ET
root = ET.parse(path)  # rejects hostile entity constructs
```

### 4. Authorized retest

With approval: DOCTYPE + external entity to **lab OAST** or a local canary.
Expect reject/ignore, **no** outbound fetch, **no** file body. If DOCTYPE is
blocked, confirm XInclude/remote schema are off. Residual exploit depth →
`xxe-xml-external-entity`.

### 5. Regression and ops

Tests: benign schema-valid XML OK; DOCTYPE/external entity rejected; oversized
input fails closed. Monitor parse latency, OOM, unexpected egress. Isolate any
legacy DTD path (network-off, internal-only, strict schema).

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Disable DTD/entities; language safe defaults | **This skill** | — |
| Offensive XXE (classic/blind/OOB/XInclude) | `xxe-xml-external-entity` | this skill for fix |
| Expansion DoS limits / billion laughs | `xxe-billion-laughs-defenses` | this skill for DTD off |
| SVG/Office upload feeding XML | `upload-insecure-files` | this skill + XXE skill |
| Shared helpers, tests, timeouts | `code-quality-standards` | **always** when coding |
| XXE-caused SSRF framing | `ssrf-server-side-request-forgery` | after entity fetch proven |

**Handoff:** PoC chains → `xxe-xml-external-entity`; entity bombs →
`xxe-billion-laughs-defenses`; implementation quality → `code-quality-standards`.

## Output Checklist

- [ ] Authorization/scope recorded; only owned or approved parsers exercised
- [ ] Untrusted XML entrypoints and libraries inventoried
- [ ] Policy: DTD off **or** external entities + resolver blocked
- [ ] Stack flags documented (Java / Python / .NET / libxml / PHP as used)
- [ ] Shared secure parse helper; no ad-hoc unsafe factories on path
- [ ] XInclude / remote schema includes disabled if unused
- [ ] Size/depth/timeout limits and least privilege / egress noted
- [ ] Retest: no external fetch; no file leak; benign XML still works
- [ ] Hostile DOCTYPE/entity tests; `code-quality-standards` applied
- [ ] Report: before/after config, redacted evidence, residual DTD isolated
- [ ] Offensive residual work routed to `xxe-xml-external-entity`

## Rules

- Defense and authorized assessment only.
- Prefer **disable DTD** over fragile entity blacklists; WAF alone is not “safe.”
- One controlled reject/timeout suffices for retest — no production DoS storms.
- Redact OAST URLs, file contents, and internal targets from tickets/samples.
- Do not claim “not vulnerable” without checking XInclude and content-type
  switch paths when only DOCTYPE controls were retested.
