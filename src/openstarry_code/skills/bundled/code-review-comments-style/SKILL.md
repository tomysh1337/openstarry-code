---
name: code-review-comments-style
description: >
  Write clear, kind, actionable code review comments with appropriate severity,
  and decide request-changes vs nit vs approve. Use when code review comments,
  PR review feedback, 评审意见写法, review tone, blocking vs non-blocking notes,
  or drafting GitHub/GitLab review summaries.
---

# Code Review Comments Style

Review comments should help the author ship a correct, maintainable change with
minimal friction. Be specific to the diff, proportional to risk, and explicit
about whether a note is blocking.

## Use When

- Drafting or rewriting PR/MR review comments (inline or summary)
- User asks for code review comments style, 评审意见写法, or review tone
- Deciding **Request changes** vs **Approve** vs **Comment** with nits
- Coaching on severity labels (`blocking`, `should`, `nit`, `question`, `praise`)
- Summarizing a multi-thread review into a single top-level response

Do **not** use this as the primary skill for implementing fixes
(`code-quality-standards` + domain skill) or for security exploitation methodology.
Use those to *judge* the code; use this skill to *phrase and prioritize* feedback.

## Repo Config First

1. **Review policy:** `CONTRIBUTING.md`, `PULL_REQUEST_TEMPLATE`, `CODEOWNERS`,
   team review guidelines, `SECURITY.md` severity definitions
2. **Bot / CI contract:** required checks, semantic PR titles, conventional
   comments bots, “reviewdog” / Danger / GitHub rulesets—do not contradict green
   required checks without explaining why
3. **Label vocabulary:** if the team uses `nit:`, `blocking:`, `suggestion:`,
   Conventional Comments (`praise:`, `issue:`, `todo:`, …), or Chinese severity
   tags, **match that vocabulary**
4. **Language of the project:** write comments in the language the team already
   uses on PRs unless asked otherwise
5. **Local bar:** recent merged PRs’ review threads—mirror brevity and strictness

**Precedence:** team policy and established comment grammar **outrank** defaults
below. Still escalate correctness, security, and data-loss issues even if the
team culture is informal.

## Workflow

1. **Understand the change.** Read the PR description, linked issue, and full
   diff (not only the lines you will comment on). Note intent and constraints.
2. **Classify findings by impact** before writing:
   - Correctness / security / data loss / authz
   - Contract or API break, migration risk
   - Reliability (lifecycle, concurrency, error paths)
   - Maintainability and tests
   - Style/naming pure preference
3. **Cluster.** Prefer one summary + a few high-value inline notes over dozens of
   micro-comments. Merge related nits into a single non-blocking list.
4. **Write each comment** with: location context (if not inline), observation,
   why it matters, and a concrete suggestion or question. Lead with the point.
5. **Mark severity explicitly** when mixed blocking and non-blocking notes appear
   in the same review (see severity model).
6. **Choose the review outcome** (Approve / Comment / Request changes) from the
   highest outstanding severity, not from nit count.
7. **Close the loop.** If prior threads are resolved, say so. Acknowledge good
   design where it reduces future review cost.

## Severity Model

| Level | Meaning | Typical outcome |
| --- | --- | --- |
| **blocking** | Must fix before merge: bug, security, broken contract, missing critical test for a risky path | Request changes |
| **should** | Important improvement; merge only with explicit follow-up or strong reason | Request changes *or* Approve with required follow-up issue—per team policy |
| **nit** | Preference, minor naming, optional clarity; author may ignore | Approve or Comment |
| **question** | Missing context; may become blocking once answered | Comment until clarified |
| **praise** | Call out a good pattern so it spreads | Any |

If the platform supports only one decision bit, **Request changes** only when at
least one **blocking** (or policy-defined **should**) item remains.

## How To Phrase Comments

### Principles

- **Kind, not vague.** Respect the author; critique the code and risk, not the person.
- **Specific.** Point at behavior, edge case, or invariant—not “this is messy.”
- **Actionable.** Prefer a suggested fix, alternative API, or test case over pure judgment.
- **Proportional.** Long essays for tiny nits waste trust; one sharp sentence often wins.
- **Evidence-backed.** For security or concurrency claims, state the scenario briefly.
- **Prefer questions when unsure.** “Does this path run under X?” beats a wrong command.

### Structure (inline)

```text
[severity] What you observed.
Why it matters (user/system impact).
Suggested direction (or question).
```

Optional: tiny code suggestion when the fix is local and unambiguous.

### Summary review structure

1. One-line overall take (intent understood / main risk).
2. Blocking items (numbered, linked to threads if useful).
3. Non-blocking / nits (bulleted, optional).
4. Explicit decision: Approve / Comment / Request changes and what would unlock merge.

## Request Changes vs Nit vs Approve

| Signal | Prefer |
| --- | --- |
| Broken behavior, vuln, secret leak, wrong migration, failing contract | **Request changes** (blocking) |
| Missing tests for a non-trivial bug fix or auth path | **Request changes** or **should** per team norm |
| Design disagreement with two valid options | **Comment** + question; escalate to blocking only if merge would paint the project into a corner |
| Naming, import order, comment typos, pure style already handled by formatter | **nit** — do not Request changes for formatter-only noise |
| Only nits remain | **Approve** (optionally with nit list) |
| CI red for reasons unrelated to this PR | Note it; do not bury real product issues |

**Do not** Request changes to enforce personal style that contradicts formatter,
linter, or documented project style. **Do** Request changes when the author
disabled safety checks or deleted tests to silence CI without justification.

## Examples

### Blocking (correctness)

**Good**

> **blocking:** `deleteUser` returns 204 even when the user id does not exist, so
> clients cannot tell a successful delete from a typo’d id. Consider 404 (or 204
> only when a row was deleted) and a test for the missing-id path.

**Bad**

> This delete handler is wrong. Please fix.

### Should (reliability)

**Good**

> **should:** If `putObject` succeeds and `db.save` fails, we leave an orphan
> blob. Can we write the DB row first with a pending state, or run a compensating
> delete in the error path?

**Bad**

> Error handling could be better.

### Nit

**Good**

> **nit:** Consider renaming `d` to `deadline` so the timeout unit is obvious at the call site. Non-blocking.

**Bad**

> Bad name. Change it. (Request changes)

### Question (missing context)

**Good**

> **question:** Does `syncAll` run while the provider webhook can still mutate the
> same rows? If yes, we may need a per-tenant lock; if it only runs offline, this is fine.

**Bad**

> This will race. (stated as fact without scenario)

### Praise

**Good**

> **praise:** The table-driven tests around expiry edge times make the invariant obvious—thanks.

**Bad**

> LGTM (only response while silent on two auth bugs)

### Summary decision

**Good**

> Thanks for the clear migration notes—intent makes sense.
>
> **Request changes** for:
> 1. **blocking:** webhook signature not verified (see inline).
> 2. **blocking:** migration is not idempotent on retry.
>
> Nits only after those: naming in `helper.go`. Happy to re-review quickly.

**Bad**

> Request changes.
> Also a bunch of style things.
> (no list, no severity, no path to merge)

### Chinese team phrasing (when the PR language is Chinese)

**Good**

> **blocking：** 这里在事务外先写了缓存，DB 回滚后会出现脏读。建议先提交 DB，再更新缓存，或写入失败时删除缓存键。  
> **nit：** 变量名 `tmp` 可改为 `retryCount`，非阻塞。

**Bad**

> 写得不行，再改改。

## Anti-Patterns

- Blocking on pure taste while ignoring a real bug elsewhere in the same PR
- Drive-by comments on files unrelated to the change without labeling them optional
- “LGTM” without reading tests or failure paths on risky diffs
- Weaponized vagueness (“clean this up”) with no target structure
- Sarcasm, personal judgments, or volume-as-authority (30 nits ≠ review quality)
- Secret values pasted into comments; describe the leak and redact

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| How to write review comments / severity / decide outcome | **This skill** | — |
| What “good code” means in the diff | `code-quality-standards` | domain skill for the feature area |
| Docs-only PR structure and Markdown form | `markdown-docs-style` | this skill for comment tone |
| Security finding on authorized assessment | domain security skill | this skill to report findings constructively |
| Implementing the requested fix | domain + `code-quality-standards` | not review-comment style |

## Checklist

- [ ] PR intent, issue link, and full diff understood
- [ ] Repo review vocabulary and language matched
- [ ] Findings sorted by impact before commenting
- [ ] Each blocking comment states observation, impact, and suggestion/question
- [ ] Severity labels clear when blocking and nits are mixed
- [ ] Nits clustered; not used as sole reason to block (unless team policy says otherwise)
- [ ] Review outcome matches highest open severity
- [ ] Questions used where context is missing instead of false certainty
- [ ] Praise or acknowledgment included when something is genuinely well done
- [ ] No secrets, blame, or unrelated drive-by rewrites without label
- [ ] Path to merge is explicit (“fix X and Y → approve”)
