# Toulmin Technical Case Reference

Use this model to expose the reasoning behind a technical recommendation.

| Element | Engineering meaning | Review question |
|---|---|---|
| Claim | The proposed decision or supported system result | What must the reader accept or do? |
| Grounds | Tests, measurements, code, logs, observations, or accepted decisions | What observable facts support the claim? |
| Warrant | The reasoning that connects the grounds to the claim | Why do these facts justify this result? |
| Backing | An invariant, standard, research source, or project decision that supports the warrant | What supports the reasoning rule? |
| Qualifier | The scope, confidence, conditions, and boundary of the claim | Where does the claim hold? |
| Rebuttal | A counterexample, failure condition, alternative, or disconfirming result | What could weaken or defeat the claim? |

## Engineering example

**Claim:** Require the `Frontend`, `Server`, and `ETL` checks before a pull request can
merge into `main`.

**Grounds:** The repository deploys from `main`. The earlier workflow did not run tests
on pull requests. The three jobs test each deployable subsystem independently.

**Warrant:** A required pre-merge check blocks a known failing commit before that commit
enters the deployment branch.

**Backing:** The repository ruleset already requires human approval and resolved
threads. The CI jobs produce repeatable build and test evidence for that decision.

**Qualifier:** The rule covers failures detected by these three jobs. It does not prove
production behavior, usability, accessibility, or security beyond their tests.

**Rebuttal:** A passing job can miss an untested regression. Human review, challenge
cases, and production observation remain necessary.

## Review discipline

Reject these weak patterns:

- A claim with no evidence.
- A list of facts with no reasoning link.
- A general guarantee from one narrow test.
- A standard name used as proof without an applicable rule.
- A rebuttal that attacks an implausible alternative.
- A qualifier such as “probably” that does not state the uncertainty.

Prefer the strongest fair counterexample. State which evidence would change the
recommendation. Escalate value judgments and risk acceptance to the accountable human.

