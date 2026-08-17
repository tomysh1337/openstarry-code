---
name: semgrep-rule-authoring
description: >
  Author, test, and tune Semgrep rules for org-owned codebases: YAML rule
  schema, pattern/pattern-either/pattern-not, metavariables, taint mode,
  message/severity/metadata, language packs, and rule tests. Use when writing
  custom Semgrep rules, fixing false positives/negatives in .semgrep.yml or
  rules/, Semgrep OSS/Pro patterns, taint-mode sinks/sources, or packaging
  org rule packs for CI.
---

# Semgrep Rule Authoring

Write **high-signal custom Semgrep rules** for repositories you own or are
authorized to scan. Prefer repo config and existing packs. Fix code under
`code-quality-standards`. Hand broad SAST ops/triage to
`sast-dast-tooling-usage`; CI wiring to `ci-cd-pipeline-patterns`.

## When To Use

- Authoring or editing **custom** Semgrep YAML (`rules/`, `.semgrep.yml`)
- Encoding org anti-patterns: forbidden APIs, raw SQL helpers, unsafe crypto
- Reducing **false positives/negatives** with tighter patterns or taint mode
- Adding **rule tests** (positive/negative fixtures) and packaging team packs
- Keywords: Semgrep rule, pattern-either, metavariable-regex, taint mode,
  `semgrep --validate`, custom SAST rule, p/ packs vs local rules

Do **not** use as primary for: run/triage scanners → `sast-dast-tooling-usage`;
SSDLC gates → `secure-sdlc-checklist`; secrets lifecycle →
`secrets-management-hygiene`; SCA/CVE → `sbom-and-supply-chain`; pipeline YAML
only → `ci-cd-pipeline-patterns`; secure fixes → `code-quality-standards`.

## Repo Config First

Repo and org policy **outrank** examples below.

1. **Configs:** `.semgrep.yml`, `.semgrep/`, `semgrep.yaml`, CI `--config` paths
2. **Layout:** pack dirs, ids (`lang.category.rule-id`), shared path includes/excludes
3. **Languages:** only languages in the monorepo; respect generated/vendor excludes
4. **Policy:** allowed `p/` rulesets; whether custom rules may block merge
5. **Engine pin:** Semgrep CLI version; Pro vs OSS features (taint depth, join)
6. **Neighbors:** CodeQL/Sonar, secret scanners, required checks, `nosemgrep` policy

Extend the real config tree; do not invent a second root.

## Workflow

### 1. Capture the bug pattern

1. Collect **≥2 true positives** and **≥1 near-miss** (must not match).
2. Name source, sink, and trust boundary in plain language.
3. Prefer **AST patterns** over brittle regex; constrain metavariables when needed.
4. Choose **search** (structural) vs **taint** (source → sink dataflow).

### 2. Draft the rule skeleton

```yaml
rules:
  - id: org.python.security.raw-cursor-execute
    languages: [python]
    severity: ERROR
    message: >
      Parameterize SQL; do not pass user-controlled strings to cursor.execute.
    metadata:
      category: security
      cwe: "CWE-89"
      confidence: MEDIUM
    patterns:
      - pattern: $CURSOR.execute($QUERY, ...)
      - pattern-not: $CURSOR.execute("...", ...)
```

Require stable **`id`**, correct **`languages`**, actionable **`message`**
(what/why/fix), honest **`severity`**, triage **`metadata`** (CWE, confidence).

### 3. Shape matchers (signal over breadth)

| Construct | Use |
| --- | --- |
| `pattern` / `patterns` / `pattern-either` | Single match; AND; OR |
| `pattern-not` / `pattern-not-inside` | Exclude known-safe shapes |
| `pattern-inside` | Require enclosing context |
| `metavariable-regex` / `-comparison` | Constrain captures |
| `focus-metavariable` | Point findings at the risky capture |
| `paths.include` / `exclude` | App code only; skip tests/vendor if policy allows |
| `mode: taint` | Sources, sinks, sanitizers for dataflow |

Start **narrow**, widen only after tests prove misses. Avoid bare `$X` sinks.

### 4. Taint mode (when search is too blunt)

1. `pattern-sources`: request fields, file/RPC inputs.
2. `pattern-sinks`: exec, raw SQL, HTML, SSRF URL builders.
3. `pattern-sanitizers`: only **proven** safe APIs (parameterized drivers, org helpers).
4. Re-test that sanitizers do not hide real bugs.

### 5. Test, validate, ship

```bash
semgrep --validate --config path/to/rule.yaml
semgrep --test path/to/rule-tests/
semgrep scan --config path/to/rule.yaml path/to/sample-src
```

1. Positive fixtures: `ruleid: <id>`; negatives: `ok: <id>`.
2. Sample-scan a real monorepo slice; review FP before merge-block.
3. Pin CLI to CI; do not land Pro-only syntax on OSS-only jobs.
4. Land rule + tests + short rationale; baseline new broad rules before hard-fail.
5. Prefer **rule fix** over mass `nosemgrep`; suppress with owner/reason; version
   packs (id renames break ignore fingerprints); demote high-FP/low-TP rules.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Custom Semgrep rules, tests, taint patterns | **This skill** | — |
| Run Semgrep/SAST, gates, triage noise | `sast-dast-tooling-usage` | this for new rules |
| SSDLC placement of scan gates | `secure-sdlc-checklist` | this for rule content |
| Workflow YAML, caches, required checks | `ci-cd-pipeline-patterns` | this for `--config` body |
| Secret policy / vault design | `secrets-management-hygiene` | this only for code patterns |
| Fixing code a rule flags | `code-quality-standards` | **always** |

Keep **this skill primary** until validate/tests pass and FP sample is acceptable.

## Output Checklist

- [ ] Repo Semgrep config, languages, excludes, and CI CLI pin read first
- [ ] Bug pattern stated; ≥2 TP and ≥1 negative example captured
- [ ] Stable `id`, languages, severity, actionable message, useful metadata
- [ ] AST-first matchers; `pattern-not` / paths cut obvious FP
- [ ] Taint used when dataflow matters; sanitizers justified
- [ ] `semgrep --validate` and `--test` green; real-code sample reviewed
- [ ] Pack wired to existing CI; baseline before hard-fail if new/broad
- [ ] `nosemgrep` policy respected; no secrets in fixtures or messages
- [ ] Hand-offs: `sast-dast-tooling-usage`, `ci-cd-pipeline-patterns`,
      `secure-sdlc-checklist`, `code-quality-standards` as needed
- [ ] Rules: repo-first; tests before merge-block; fix rules before mass suppress
