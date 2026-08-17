# Final Review

## Behavior

- Does the diff implement the requested behavior end to end?
- Are compatibility and failure behavior intentional?
- Are edge cases based on evidence rather than guesses?

## Design

- Does the change follow existing ownership and dependency boundaries?
- Is there one source of truth?
- Is every new abstraction justified by real complexity or repetition?

## Reliability

- Are errors contextual and observable?
- Are resources, tasks, timers, locks, and transactions cleaned up?
- Are timeout, cancellation, retry, ordering, and idempotency defined where relevant?

## Security And Data

- Are inputs validated at trust boundaries?
- Are queries, commands, paths, URLs, and serialized data handled with structured APIs?
- Are secrets and personal data absent from code, logs, fixtures, and snapshots?
- Are input sizes and memory growth bounded?

## Verification

- Are regression and boundary tests present at the right layer?
- Were formatter, linter, type checker, focused tests, broader tests, and build run as applicable?
- Does the final diff avoid unrelated formatting, generated output, and metadata churn?
- Are unrun checks and residual risks reported honestly?
