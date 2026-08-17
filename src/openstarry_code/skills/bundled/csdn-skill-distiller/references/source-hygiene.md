# Source Hygiene for Chinese Technical Blogs

Use this reference when turning CSDN, devpress, cnblogs, juejin, Zhihu columns, or similar Chinese technical posts into Codex skill material.

## Evidence Capture

For each source that materially changes the skill, record:

- URL
- Title
- Publication or update date when visible
- Software, framework, language, operating system, or challenge context
- The specific claim used, paraphrased in your own words
- How the claim was verified or why it remains a weak lead

Do not store copied article text unless a tiny quote is necessary and allowed. Prefer a one-line paraphrase plus link.

## Verification Checks

Before encoding commands or procedures:

- Check whether the article targets Windows, Linux, macOS, container, browser, or cloud runtime.
- Check version anchors such as JDK, Gradle, Node, Python, package manager, kernel, framework, or browser version.
- Re-run commands in a disposable or challenge-local environment when possible.
- Compare against official docs for flags, deprecated APIs, security defaults, and breaking changes.
- Prefer current local configuration over article assumptions.

## Common Failure Modes

Watch for:

- Copied posts with stale commands or missing original context
- Commands that depend on a different shell, encoding, locale, or path layout
- Registry mirror, package source, or certificate fixes that mask the real root cause
- Security or CTF steps that omit preconditions, scope, offsets, mitigations, or cleanup
- Blog snippets that work only because global state already existed on the author's machine

## Distillation Pattern

Convert source material into this shape:

1. Problem signature: what the user sees, including key error lines or symptoms.
2. Decision checks: minimal observations that choose the right branch.
3. Action: commands or edits, scoped to the smallest reversible change.
4. Verification: exact output, test, request, or artifact proving success.
5. Rollback or cleanup: how to undo temporary changes.

If several sources disagree, follow reproduced behavior first and keep the disagreement as a note only when it affects future decisions.
