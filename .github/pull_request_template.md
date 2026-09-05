<!--
The required submission record is .github/submission.md. Replace that file with this
template's completed content. The final head commit must change the record from its
first parent. Amend it when later work changes the evidence. You may mirror the record
here for reviewer convenience. CI does not validate this pull request body.
-->

## Claim

After this change, <!-- actor or system --> can <!-- observable result --> under <!-- important conditions -->.

Closes #<!-- issue number -->

<!-- Use "Issue exception:" with a specific reason only when no issue exists. -->

## Technical case

- Grounds: <!-- Tests, code, observations, measurements, or accepted decisions. -->
- Warrant and backing: <!-- Why the grounds support the claim. Name the applicable invariant, standard, or decision. -->
- Qualifier: <!-- Conditions and boundaries where the claim holds. -->
- Rebuttal: <!-- Strongest counterexample, remaining uncertainty, or evidence that would change the decision. -->

## Decision explanation

- Why this design: <!-- Explain how the mechanism satisfies the claim. -->
- Why not the closest alternative: <!-- Name the best alternative and why it loses under the stated conditions. -->
- Trade-off accepted: <!-- State the cost or limitation that remains. -->
- Revisit when: <!-- Name the evidence or condition that should reopen this decision. -->

## Code quality

- Comprehension path: <!-- Name the entry point, decision owner, and observable result. -->
- Refactor boundary: <!-- Name the smallest stable contract for a future behavior change. -->
- Boundary and ownership: <!-- State which module owns the rule, state, or side effect. -->
- Failure and recovery: <!-- State the failure signal, containment, retry, rollback, or operator action. -->
- Complexity added or removed: <!-- Name new branches, dependencies, state, or duplication. State what became simpler. -->

## Risk and scope

- Risk lane: Green / Yellow / Red
- In scope:
- Out of scope:
- Important invariants:

## What changed

-

## Challenge cases

Describe how you tried to prove the change wrong. Include normal, boundary, failure, and regression cases that apply.

-

## Evidence

| Check | Result | Evidence or reason not run |
|---|---|---|
| Client lint and build | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| Server lint and build | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| ETL tests | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| Technical prose and editorial style | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| Manual user journey | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| Accessibility / responsive | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |
| Security / privacy / recovery | <!-- Pass, Fail, Not run, or Not affected --> | <!-- Command, result, or specific reason --> |

For UI changes, add before-and-after screenshots or a recording.

## AI assistance

- [ ] No substantial AI assistance
- [ ] AI assisted with exploration or planning
- [ ] AI assisted with implementation or tests
- [ ] AI assisted with review or challenge

I read and understand the submitted diff. I verified the evidence above and remain accountable for the change.

## Review focus and uncertainty

What should the human reviewer examine most closely? Which rebuttal or qualifier needs
human judgment? What is not yet proven?

-

## Documentation and learning

- [ ] No documentation change is needed
- [ ] I updated the relevant README, `AGENTS.md`, decision record, or runbook
- [ ] I recorded a follow-up issue for remaining work

Follow the
[`Code Change Standard`](https://github.com/codeforboston/boston-circular-economy/blob/main/docs/CODE_CHANGE_STANDARD.md)
for the submission and explanation rules.
