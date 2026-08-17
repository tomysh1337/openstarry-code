---
name: command-injection-defenses
description: >
  Defend applications against OS command injection by avoiding shells, using
  argv arrays, allowlisting inputs and binaries, and preferring library APIs
  over exec. Use when hardening process spawning, subprocess/ProcessBuilder/
  child_process sinks, CLI wrappers (ping, convert, ffmpeg, git), shell=True
  or system()/exec() review, or remediating CMDi findings — authorized and
  org-owned systems only.
---

# Command Injection Defenses

Design and verify **defenses** that stop user-controlled data from becoming
shell syntax or unintended process arguments. Defensive hardening only; no
exploit payloads or bypass catalogs.

## Scope And Authorization

- **In scope:** Org-owned apps, workers, admin tools, CI helpers, and containers
  where code starts OS processes; authorized secure-code review; own-project labs.
- **Out of scope:** Offensive PoC catalogs; third-party systems; building injection payloads.
- Residual CMDi **testing** → `cmdi-command-injection`. This skill owns **defense
  design, code review, and fix verification**. Redact hosts, paths, secrets, output.

## When To Use

- Features wrap CLIs: diagnostics (`ping`, `traceroute`), media (`ffmpeg`,
  `convert`), documents, git, backup, mailers, or admin “run job”
- Code review finds `system`, `shell_exec`, `os.system`, `subprocess` with
  `shell=True`, `child_process.exec`, `Runtime.exec` string forms, or
  `bash -c` / `cmd /c` wrappers
- Remediating a CMDi finding or designing a new process-spawning path
- Mentions: command injection defense, safe subprocess, argv array, avoid shell,
  ProcessBuilder hardening, `shell=False`

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Authorized offensive CMDi detection / proof | `cmdi-command-injection` |
| Injection class unknown | `injection-checking` |
| General allowlists / schemas at HTTP edge | `input-validation-patterns` |
| Implementation quality baseline | `code-quality-standards` |
| SSRF / SQL / template RCE (not OS shell) | matching class skill |

## Workflow

### 1. Inventory process sinks

1. Search process APIs: PHP `system`/`exec`/`proc_open`; Python `os.system`/
   `subprocess`; Node `child_process.exec`/`spawn`; Java `Runtime`/`ProcessBuilder`;
   Go `exec.Command`; Ruby backticks/`system`; unquoted vars in shell scripts.
2. Per sink: user-influenced fields, fixed vs dynamic binary, whether a **shell**
   is interposed, and service privilege. Prefer removing the sink over escaping.

### 2. Prefer no shell, no exec

| Preference order | Approach |
| --- | --- |
| 1. Library / SDK | DNS, image, git, mail via language libs or official clients |
| 2. Structured service API | Internal job RPC with typed fields, not shell strings |
| 3. Fixed binary + argv array | No shell; args as discrete strings |
| 4. Last resort | Shell only with zero user data in the command string |

Never build command lines with string concat/interpolation of untrusted input.

### 3. Argv arrays and safe APIs

- **Python:** `subprocess.run(["tool", "--flag", value], shell=False)` — never
  `shell=True` for untrusted data.
- **Node:** `spawn` / `execFile` with `args[]`; avoid `exec` / `execSync` shell form.
- **Java:** `ProcessBuilder` with discrete tokens — not one shell line.
- **Go:** `exec.Command("tool", a, b)` — not `sh -c` with user strings.
- **PHP:** argv-style `proc_open` when no library exists; still allowlist binary/grammar.

Argv without a shell blocks `;|&$()` chains, but **not** option injection
(`--output=/evil`) — still allowlist flags and values.

### 4. Allowlists (not denylists)

1. **Binary:** fixed path/name from an internal map; never user-chosen executable.
2. **Flags:** closed set; map user intent → fixed flag strings.
3. **Values:** domain grammar (host/IP, job id, enum) via strict parser **before**
   argv assembly (`input-validation-patterns`).
4. Reject unknown chars, newlines, NULs, oversize lengths; fail closed.
5. Paths: resolve under an allowed root; reject `..` and absolute escapes.

Denylisting `;` or `&` alone is **not** a control.

### 5. Runtime and ops hardening

1. Low-privilege workers; no root for CLI wrappers.
2. Minimal containers; drop unused shells/tools; read-only FS where possible.
3. Timeouts; cap CPU/output size on every external process.
4. Separate user-driven CLI features from high-privilege admin shells.
5. Log binary + allowlisted args (redact secrets); alert on anomalies.

### 6. Verify defenses (authorized)

1. Code review: no shell-string paths for user-influenced fields.
2. Tests: allowlisted inputs succeed; rejected shapes never reach `exec` (mock process layer).
3. Staging residual retest → `cmdi-command-injection` under SOW only; no exploit catalogs here.
4. Apply `code-quality-standards` for errors, typing, and tests on code changes.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Defend / remediate OS command injection | **This skill** | — |
| Authorized CMDi testing / residual proof | `cmdi-command-injection` | this skill for fix design |
| Class unclear | `injection-checking` | this after shell sink confirmed for fixes |
| Boundary allowlists / schemas | `input-validation-patterns` | this for process-argv specifics |
| Implement or review spawn code | `code-quality-standards` | **always** with this skill |
| Path/file args to tools | `path-traversal-lfi` mindset | this for exec surface |
| Template or expression RCE, not shell | SSTI / EL skills | this if later OS handoff |

- **`cmdi-command-injection`:** find/prove CMDi. **This skill:** prevent and remediate without PoCs.
- **`input-validation-patterns`:** general allowlist/schema; this owns binary/flag/argv policy.
- **`code-quality-standards`:** always apply when changing process-spawning code.

## Output Checklist

- [ ] Process sinks inventoried (API, shell vs argv, privilege)
- [ ] Prefer library/API over exec; shell removed from user-influenced paths
- [ ] Fixed binary; argv array / ProcessBuilder / spawn-with-args used
- [ ] Allowlists for binary, flags, and value grammar; fail closed
- [ ] Path args confined to allowed roots; length/time/output caps set
- [ ] Worker least privilege; container/tooling minimized
- [ ] Tests reject hostile shapes without executing real shells in CI
- [ ] Residual authorized retest routed to `cmdi-command-injection`
- [ ] `code-quality-standards` applied; secrets/PII redacted in logs and reports
- [ ] No exploit PoCs or bypass catalogs produced under this skill

## Rules

- Avoid the shell; pass discrete argv; allowlist grammar; prefer libraries.
- Denylists and ad-hoc escaping are not sufficient controls.
- No exploit payloads, reverse shells, or evasion guides in this skill’s output.
- Defense and authorized hardening only; offensive work → `cmdi-command-injection`.
- Repo conventions and existing process helpers outrank generic examples here.
