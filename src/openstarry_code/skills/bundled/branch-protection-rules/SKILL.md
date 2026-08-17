---
name: branch-protection-rules
description: >
  Configure and audit GitHub/GitLab branch protection: required status checks,
  block force-push and deletion, linear history, admin/owner enforcement, and
  CODEOWNERS-required reviews. Use when branch protection, protected branch,
  required checks, force-push ban, require linear history, enforce admins,
  CODEOWNERS gate, merge request approval rules, 分支保护, or hardening main/master.
---

# Branch Protection Rules

Harden default and release branches so merges require review and CI, history
stays rewrite-safe, and admins cannot silently bypass policy. Prefer **org-level
rulesets** and existing repo settings over inventing a second policy layer.

## When To Use

- Defining or reviewing protection for `main` / `master` / `develop` / release trains
- Requiring status checks (CI job names), PR/MR reviews, or CODEOWNERS approval
- Blocking force-push, branch deletion, or non-linear merges on shared trunks
- Enforcing rules on administrators and maintainers (no owner bypass)
- GitLab approval rules, push rules, or “allowed to merge/push” vs GitHub rulesets
- Mentions: branch protection, protected branch, required checks, force-push,
  linear history, enforce admins, CODEOWNERS, 分支保护, merge train gates

Do **not** use as primary for:

| Need | Skill instead |
| --- | --- |
| Branch naming, trunk vs Git Flow, PR process hygiene | `git-workflow-conventions` |
| CI job design, secrets, caches, artifacts | `ci-cd-pipeline-patterns` |
| Commit / PR prose | `commit-message-conventions` / `pr-description-writing` |
| CONTRIBUTING docs for humans | `readme-and-contributing-docs` |
| App code quality inside CI | `code-quality-standards` |

## Repo Config First

Platform and org policy **outrank** the defaults below.

1. **Host model:** GitHub branch protection / **rulesets** (repo + org) vs GitLab
   protected branches + approval rules + push rules
2. **Existing gates:** required check names, review count, dismiss stale reviews,
   conversation resolution, signed commits, merge method (squash/rebase/merge)
3. **CODEOWNERS:** `.github/CODEOWNERS` or `CODEOWNERS` / GitLab path rules —
   owners must be valid teams/users with write access
4. **CI identity:** exact job/check names that appear in the status API (not
   display-only labels); required “gate” job if many matrix cells
5. **Who may push:** bots (Dependabot, release-please), deploy keys, service
   accounts — list explicit exceptions; never open force-push for humans
6. **Environments:** deployment protection (approvals) is separate from branch
   protection; align both for prod
7. **Org inheritance:** org rulesets may already require linear history or block
   force-push — inventory before duplicating or weakening

**Precedence:** Documented org rulesets and repo settings win. Flag policies that
exempt admins, omit required checks, or allow direct push to default branch.

## Workflow

1. **Inventory protected refs.** Default branch, long-lived integration
   (`develop`), and `release/*` / hotfix lines. Feature branches usually stay
   unprotected (or lightly restricted).

2. **Require a pull/merge request path.**
   - GitHub: require PR before merge; block direct pushes to the protected ref
   - GitLab: allowed to push = none (or maintainers only when policy demands);
     allowed to merge = roles that may complete an approved MR
   - Prefer **squash or rebase merge** when linear history is required

3. **Required status checks (strict).**
   - List only checks that must stay green; match **exact** context names from CI
   - Enable “require branches to be up to date” (strict) when flaky races are
     worse than rebase churn
   - Add a single aggregate **gate** job if protection allows few check slots
   - Do not require checks that never run on the PR event (fork/path filters)

4. **Reviews and CODEOWNERS.**
   - Minimum approving reviews (≥1; ≥2 for high-risk repos)
   - Dismiss stale approvals on new commits; require conversation resolution if
     the team uses review threads
   - **Require review from CODEOWNERS** for owned paths; keep CODEOWNERS
     complete for critical dirs (`/`, infra, auth, release)
   - GitLab: approval rules with code-owner approvals + prevent author approval

5. **History integrity.**
   - **Block force-push** and **block deletion** on protected branches
   - **Require linear history** when the team standardizes on squash/rebase
     (no merge commits onto the trunk)
   - Optional: require signed commits / verified commits per org crypto policy

6. **Admin and bypass enforcement.**
   - **Do not allow** administrators to bypass (GitHub: “Do not allow bypassing
     the above settings” / ruleset bypass actors empty or break-glass only)
   - GitLab: uncheck “Allow to force push”; avoid “Allowed to push” for Owner
     unless break-glass is documented
   - Break-glass: time-bounded ruleset bypass actors or emergency role with audit,
     not permanent admin exemptions

7. **Bots and exceptions.** Grant narrow merge/push rights to automation via
   ruleset bypass or allowed merge identities; never grant org-wide force-push.
   Verify Dependabot/renovate PRs still satisfy required checks and reviews.

8. **Verify.** Open a test PR that fails CI, lacks CODEOWNERS approval, and
   attempts a force-push to the protected branch; confirm each path is blocked.
   Record settings as code (Terraform/API/org ruleset JSON) when the org manages
   repos as fleet.

## Routing

| Situation | Primary | Helper |
| --- | --- | --- |
| Protected branch settings, required checks, force-push, linear history, admin enforce, CODEOWNERS gate | **This skill** | — |
| Branch naming, trunk/Git Flow, short-lived feature hygiene | `git-workflow-conventions` | this skill for platform gates |
| CI job names, gate job, PR trust levels | `ci-cd-pipeline-patterns` | this skill for which checks are required |
| PR/MR description text | `pr-description-writing` | — |
| Human CONTRIBUTING of protection policy | `readme-and-contributing-docs` | this skill for the policy content |
| Implement app fixes under protected CI | `code-quality-standards` | domain skill |

## Output Checklist

- [ ] Protected refs listed (default + release/integration lines)
- [ ] PR/MR required; direct push to trunk denied for humans
- [ ] Required status checks named exactly; strict up-to-date policy decided
- [ ] Review count, stale-review dismiss, conversation resolution set
- [ ] CODEOWNERS present, valid, and **required** for owned paths
- [ ] Force-push and branch deletion blocked on protected refs
- [ ] Linear history required when squash/rebase is team policy
- [ ] Admin/owner bypass disabled or break-glass only with audit
- [ ] Bot/service exceptions least-privilege and documented
- [ ] Settings verified with fail-CI / no-approval / force-push attempts
- [ ] Org rulesets inventory checked; no weaker repo-only override
- [ ] Paired with `git-workflow-conventions` / `ci-cd-pipeline-patterns` as needed
