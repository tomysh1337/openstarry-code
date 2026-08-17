---
name: shell-script-style
description: >
  Write and review Bash/POSIX shell scripts with safe defaults: set -euo pipefail
  where appropriate, correct quoting, array-safe iteration, ShellCheck-clean patterns,
  and predictable error handling. Use when shell script style, bash style, shellcheck,
  quoting bugs, set -e pitfalls, CI install scripts, or hardening local automation.
---

# Shell Script Style

## Use When

- Writing or editing `.sh` / Bash scripts, install hooks, CI steps, or CLI wrappers.
- Reviewing scripts for unquoted expansions, word-splitting, or missing `set` flags.
- User mentions shell style, Bash style, ShellCheck, `set -euo pipefail`, or quoting.
- Hardening automation that runs under `bash`, `sh`, or mixed POSIX environments.

Do **not** use as primary for:

- Offensive command-injection testing → `cmdi-command-injection`
- General multi-language code quality → `code-quality-standards` (this skill is the shell specialist)
- PowerShell-only Windows automation (apply analogous safety ideas; do not force Bash idioms)

## Repo Config First

Repository conventions outrank generic preferences unless they create a correctness or security risk. Surface the conflict instead of silently introducing a second style.

1. Read `README`, `CONTRIBUTING`, `AGENTS.md` / `Agents.md`, and any `scripts/` README.
2. Detect shell dialect from shebang and CI: `#!/usr/bin/env bash`, `#!/bin/sh`, `shell: bash` in workflows.
3. Honor existing ShellCheck config: `.shellcheckrc`, `SHELLCHECK_OPTS`, Makefile/`pre-commit` hooks, CI job flags (`-x`, `-e` exclusions).
4. Match local layout: `set -euo pipefail` at top vs sourced library style; `lib.sh` helpers; `strict mode` wrappers already in tree.
5. Prefer project formatters/linters and existing helper functions (`die`, `log`, `require_cmd`) over inventing parallel utilities.
6. Keep scripts executable and line-ending policy consistent with the repo (LF on Unix targets; avoid accidental CRLF).

## Workflow

### 1. Choose dialect and strictness

| Context | Prefer | Notes |
| --- | --- | --- |
| New automation in this library / modern CI | `bash` + `set -euo pipefail` | Document Bash version floor if using arrays/`[[` |
| Portable install snippet for unknown `sh` | POSIX `sh` + careful `set -eu` | Avoid Bashisms; pipefail may be unavailable |
| Sourced library (`. ./lib.sh`) | Do **not** force `set -e` on callers | Guard with `if`; document expected caller options |
| One-liner CI step | Inline safety or extract to script | Prefer a file once logic exceeds ~10 lines |

Shebang pattern for new Bash scripts:

```bash
#!/usr/bin/env bash
set -euo pipefail
```

When `pipefail` is required under pure POSIX, document the limitation or invoke `bash` explicitly.

### 2. Quoting and expansion rules

- Double-quote every expansion: `"$var"`, `"$1"`, `"${array[@]}"`.
- Use `"$@"` to forward args; never unquoted `$@` or `$*` for argument lists.
- Prefer `"${var}"` when adjacent to other text: `"${prefix}_${name}.txt"`.
- Use `[[ ... ]]` in Bash for tests; quote RHS of `==`/`!=` unless intentional pattern match.
- For paths, store in variables already quoted on use; do not strip quotes “for readability.”
- Disable globbing only when intentional (`set -f`) and restore afterward.

### 3. Errors, exit codes, and traps

- Check commands that may fail when `set -e` is intentionally off for a block.
- Understand `set -e` pitfalls: failures in `if cmd;`, `cmd || true`, and some pipeline contexts (mitigate with `pipefail`).
- Use `cmd || die "message"` / explicit exit for user-facing errors.
- Prefer `trap 'cleanup' EXIT` (and `INT`/`TERM` when needed) for temp dirs and background jobs.
- Return meaningful exit codes: `0` success, non-zero failure; avoid silent `exit 0` after errors.

### 4. Safe iteration and files

- Iterate arrays with `"${items[@]}"`, not unquoted `$items`.
- Read lines with `while IFS= read -r line || [[ -n $line ]]; do ...; done < file` (Bash) or equivalent; avoid `for line in $(cat file)`.
- Use `mktemp` / `mktemp -d` for temporary paths; clean up in `trap`.
- Prefer `printf` over `echo` for anything with escapes or variable content.
- Avoid `eval` and unquoted `find ... | sh`; build arg arrays instead.

### 5. Commands, paths, and secrets

- Use `--` before path arguments when inputs may start with `-`.
- Prefer `command -v tool` over `which tool`.
- Set `PATH` deliberately in installers; do not assume interactive profile settings.
- Never log secrets; pass via env or files with restricted permissions, not CLI flags when avoidable.
- Quote SQL/shell interpolations at the boundary; do not compose trusted commands from untrusted strings (pair with `code-quality-standards` / injection skills for security review).

### 6. ShellCheck and verification

1. Run ShellCheck on touched scripts with the same flags as CI.
2. Fix findings; use directed directives only when justified:

   ```bash
   # shellcheck disable=SC2086  # intentional word split for $EXTRA_FLAGS array expansion alternative preferred
   ```

   Prefer refactoring over broad disables. Never disable without a one-line reason.

3. Smoke-test: `bash -n script.sh` (syntax), then a dry-run path or `--help` if available.
4. Exercise failure paths (missing arg, missing dependency) under `set -euo pipefail`.

## Good And Bad Examples

### Strict mode and shebang

```bash
# Good
#!/usr/bin/env bash
set -euo pipefail

main() {
  local target=${1:?usage: $0 <target>}
  printf 'ok %s\n' "$target"
}
main "$@"
```

```bash
# Bad — unquoted args, no strict mode, echo pitfalls
#!/bin/sh
target=$1
echo ok $target
```

### Quoting and arrays

```bash
# Good
files=( "src/a b.txt" "src/c.txt" )
for f in "${files[@]}"; do
  cp -- "$f" "$dest/"
done
printf 'count=%s\n' "$#"
forward() { other_cmd "$@"; }
```

```bash
# Bad — word-splitting and globbing
for f in $files; do cp $f $dest; done
other_cmd $@
```

### Pipelines and errors

```bash
# Good
set -euo pipefail
mapfile -t lines < <(grep -E '^[A-Z]' "$input" | sort -u)
if ! curl -fsS "$url" -o "$tmp"; then
  printf 'download failed: %s\n' "$url" >&2
  exit 1
fi
```

```bash
# Bad — left side failures ignored without pipefail; errors swallowed
grep pattern file | sort | uniq > out
curl "$url" -o "$tmp" || true
```

### Safe line reading

```bash
# Good
while IFS= read -r line || [[ -n ${line-} ]]; do
  [[ -z $line || $line == \#* ]] && continue
  process "$line"
done < "$config"
```

```bash
# Bad
for line in $(cat "$config"); do process $line; done
```

### Temp files and cleanup

```bash
# Good
workdir=$(mktemp -d)
trap 'rm -rf "$workdir"' EXIT
# ... use "$workdir"
```

```bash
# Bad
workdir=/tmp/myjob-$$
mkdir $workdir
# no trap; race-prone fixed path
```

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Bash/shell style, ShellCheck, quoting | `shell-script-style` (this) | — |
| Broader maintainability / tests / multi-language review | `code-quality-standards` | this for shell files |
| SQL script formatting / migrations | `sql-style-conventions` | — |
| Command injection vulnerability testing | `cmdi-command-injection` | this only for fix-side hardening |
| Privilege-escalation live scripts on lab hosts | matching privesc skill | this for script cleanliness |
| RE/network tooling wrappers | domain skill (`binary-re`, protocol, etc.) | this for wrapper hygiene |

## Checklist

- [ ] Shebang and dialect match the repo (Bash vs POSIX `sh`)
- [ ] `set -euo pipefail` (or documented POSIX equivalent) applied only where appropriate
- [ ] All expansions quoted; `"$@"` used for arg forwarding
- [ ] No unquoted `$(cat ...)`, `eval`, or unnecessary word-splitting
- [ ] Pipelines safe under `pipefail`; failures not silently ignored
- [ ] `trap` cleanup for temp dirs/files and background work
- [ ] Paths use `--` where needed; `command -v` for dependency checks
- [ ] ShellCheck clean under project config; disables are justified and minimal
- [ ] `bash -n` / smoke test run; failure paths verified
- [ ] Secrets not printed; scripts remain LF and executable as required by the repo
