# Code Change Standard

## Purpose

A reviewer must understand what a change does, why it works, and where it can fail.
The submission must also explain why the closest credible alternative was not selected.

This standard applies to human-written and agent-assisted changes. The contributor owns
the code, evidence, explanation, and decision to request review.

## Required submission record

Replace `.github/submission.md` with a completed copy of the pull request template for
each change. Commit that record with the code before requesting review. The pull request
description can mirror the record for convenience, but CI validates only the committed
file from the exact head revision.

The submission record must contain:

1. A claim that names an observable result and its important conditions.
2. Grounds from tests, code, measurements, logs, research, or accepted decisions.
3. A warrant that connects the grounds to the claim.
4. A qualifier that limits the claim to the evidence boundary.
5. The strongest relevant rebuttal or remaining uncertainty.
6. The selected design and its operating mechanism.
7. The closest credible alternative and the reason it loses under the stated conditions.
8. The accepted trade-off and the condition that should reopen the decision.
9. A comprehension path from the entry point through the decision owner to the result.
10. The smallest stable boundary for a future refactor.
11. Code ownership, failure behavior, recovery, and complexity effects.
12. Reproducible checks, including a reason for each check that did not run.

Select exactly one Green, Yellow, or Red lane in `Risk and scope`. Keep all seven
standard `Evidence` rows. Use Pass, Fail, Not run, or Not affected for each result.

The `Submission record v1` job checks the required sections, labels, risk lane, issue
reference, AI disclosure, and submitter attestation. The `Prose` CI job checks selected
language rules in repository files.

`Submission record v1` is a commit status, so its evidence must also belong to the commit.
The trusted workflow fetches `.github/submission.md` from the exact head as inert data
and requires its blob to differ from the head's first parent. The final head commit must
therefore update the record. Two pull requests at one head use the same record and
receive the same result, even when their bases differ. Human approval remains a
separate judgment because a cosmetic edit can satisfy the blob check.

The v1 context freezes its terminal validation predicate and target commit. Change the
context version before changing that result boundary. Migrate the protected-branch
rule, then retire the earlier context after active pull requests use the new policy.
Trigger coverage and intermediate-state safety corrections can retain the context when
the terminal predicate and target commit remain unchanged.

CI cannot decide whether the stated rationale is true or complete. The contributor and
human reviewer must compare the explanation with the implementation and evidence.

## Explain the why

Describe the causal mechanism. Name the component that owns the decision, the input it
receives, the action it takes, and the observable effect.

Weak explanation:

> This approach is better and cleaner.

Reviewable explanation:

> The route module owns path matching, so local hooks and CI select the same checks from
> one versioned policy.

The second explanation states ownership, mechanism, and consequence. A reviewer can
inspect the policy and exercise the classifier.

## Explain the why not

Compare the selected design with the closest credible alternative. Do not create a weak
alternative only to dismiss it.

State:

- the alternative.
- the condition where it would be preferable.
- the evidence or constraint that rejects it for this change.
- the condition that should reopen the choice.

Include “do nothing” when the current behavior is a credible option. A routine internal
change can use three or four direct sentences. A disputed or cross-system decision needs
a decision record.

## Code explanation rules

Apply the repository
[`write-self-explanatory-code`](../.agents/skills/write-self-explanatory-code/SKILL.md)
skill during implementation and refactoring. Self-explanatory code exposes enough
structural and semantic context for a human to trace and safely change its behavior.

The pull request must state the comprehension path and refactor boundary. The path
names the entry point, decision owner, and observable result. The boundary names the
smallest stable contract where behavior can change without unrelated edits.

Code should explain behavior through names, interfaces, types, and tests. Add a comment
only when those elements cannot expose an important reason or constraint.

A useful comment explains one of these properties:

- a non-obvious invariant.
- a policy or standards constraint.
- a compatibility boundary.
- a safety or privacy control.
- the reason an apparent simplification is unsafe.
- the failure or recovery behavior of a side effect.

Do not restate the next line of code. Do not preserve prompt history, author history, or
a temporary implementation narrative in comments.

Public interfaces need documentation when names and types do not state the contract.
Document accepted inputs, returned state, side effects, failure signals, and important
limits. Use one stable term for each concept.

## Code quality discussion

Address each quality property that the change affects:

| Property | Review question |
|---|---|
| Comprehension | Can a maintainer trace the entry point, decision owner, and result? |
| Refactor | Which stable boundary contains a future behavior change? |
| Boundary | Which module owns the rule, state, or side effect? |
| Contract | Which caller-visible behavior can change? |
| Data | Which validation, provenance, retention, or freshness rule applies? |
| Failure | How does the system signal and contain failure? |
| Recovery | Can a user, operator, or retry return the system to a supported state? |
| Complexity | Which branch, dependency, state transition, or duplicate path changes? |
| Testability | Which observation proves the mechanism rather than mirrors its code? |
| Operations | Which log, metric, alert, or runbook exposes failure after deployment? |
| Accessibility | Which keyboard, screen-reader, contrast, zoom, or motion behavior changes? |
| Security | Which trust boundary, permission, secret, or destructive action changes? |

Write “Not affected” with one reason when a property does not apply. Do not use “N/A”
without an explanation.

## Decision record threshold

Add a file under `docs/decisions/` when a decision:

- changes a public or cross-subsystem contract.
- adds durable state, a dependency, or an external service.
- affects security, privacy, migration, or recovery.
- rejects a credible alternative that future contributors are likely to propose again.
- cannot fit a fair explanation in the pull request.

Copy `docs/decisions/0000-template.md`. Replace `0000` with the next four-digit number.
The pull request remains the evidence record for the implemented change.

## Review standard

Use the repository
[`review-code-change`](../.agents/skills/review-code-change/SKILL.md) skill for an AI
or agent review. The managed GitHub reviewer consumes the applicable
`## Code Review Rules` sections from `AGENTS.md`. Its findings remain advisory.

The reviewer compares the claim, mechanism, diff, tests, and rejected alternative. The
reviewer should ask for revision when:

- the explanation describes intent but not the operating mechanism.
- the tests repeat implementation details without proving observable behavior.
- the alternative is not credible or receives no fair comparison.
- the qualifier omits a material boundary.
- the code moves ownership without documenting the new owner.
- the failure path has no signal, containment, or recovery account.
- the stated comprehension path or refactor boundary does not match the code.

Use the Toulmin structure and language guidance in the repository communication skill.
The human review owns technical accuracy, rhetorical fairness, and decision quality.
