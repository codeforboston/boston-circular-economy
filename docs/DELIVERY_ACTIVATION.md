# Activate the Delivery Pilot

Status: Awaiting maintainer review, merge, and hosted activation evidence.

## Observed baseline

Inspection on September 4, 2026, used
[PR #55](https://github.com/codeforboston/boston-circular-economy/pull/55)
at `32a4650af13f927fad78bc89206a738796807277`.

| Requirement | Observed evidence | Remaining proof |
|---|---|---|
| Repository and coordination | `codeforboston/boston-circular-economy` and [#circular-economy](https://cfb-public.slack.com/archives/C0AFA66CE2W) | Recheck claims before assigning work |
| Code checks | [CI run 33932942639](https://github.com/codeforboston/boston-circular-economy/actions/runs/33932942639) passed routing, prose, frontend, server, and ETL jobs | Successful CI on the merged main commit |
| Submission status | Versioned workflow and local validator | A subsequent PR must emit `Submission record v1` from the main-branch policy |
| Required checks | [Ruleset 12887631](https://github.com/codeforboston/boston-circular-economy/rules/12887631) requires human approval but has no required-status rule | Admin adds and reads back the five required contexts |
| Deployment | Main contains the earlier Pages workflow | The tested main artifact reaches Pages through the replacement workflow |
| Agent review | Local runner and managed-review instructions exist | Observe a completed review on a representative PR |
| Mentoring | Playbook and candidate work units exist | Contributors and available mentors confirm the first units |

Passing draft-PR CI does not prove deployment or adoption. Local submission tests do
not prove GitHub event delivery or status permissions.

## Launch sequence

1. A human reviewer accepts PR #55's scope, evidence, and pilot policies.
2. A maintainer merges through the existing ruleset after its required approval.
3. Confirm the merged commit passes `CI` on `main`.
4. Confirm `Deploy to GitHub Pages` downloads that CI run's `github-pages-client` artifact.
5. Check the published page and record the CI run, deployment run, commit, and artifact identifiers.
6. Open the first agreed work unit as a draft PR from the merged `main`.
7. Update `.github/submission.md` in the final head commit, then confirm `Submission record v1` succeeds.
8. An administrator adds the five contexts to `Protect Main Branch` and reads back the rule.
9. Require branches to be up to date, then verify the merge box requires those contexts and the existing human approval.
10. Configure managed review and observe one completed review before declaring that integration active.

`Submission` responds to pull request events, not main pushes. Do not wait for
`Submission record v1` on the pilot's main-branch CI run. It first becomes available
on a subsequent PR after the trusted policy enters `main`.

Require these exact context names:

- `Submission record v1`
- `Prose`
- `Frontend`
- `Server`
- `ETL`

Retain the designated-team approval, stale-review dismissal, last-push approval,
resolved-thread, squash-merge, deletion, and force-push protections. Require branches
to be up to date. Keep merge queues disabled while the submission policy lacks
merge-group support.

Use GitHub Actions as the expected check source when GitHub offers the observed
producer. Record the producer and rule settings. Repository write access alone does
not grant ruleset administration. See [GitHub ruleset guidance](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

For managed review, follow the [selected settings](AI_DELIVERY_PLAYBOOK.md#maintainer-activation-step)
and [official Codex setup](https://learn.chatgpt.com/docs/third-party/github).
Confirm the upstream repository, team enablement, trigger, and usage owner.
Observe a review for the submitted revision. A settings toggle alone is insufficient evidence.

## Exercise the gates

Use a disposable draft PR or the agreed first work unit. Record results before
requiring each gate. Restore the complete submission and remove any deliberate
defect before human review.

| Exercise | Expected observation |
|---|---|
| Remove one required field from `.github/submission.md`, commit, then restore it in another commit | `Submission record v1` fails and later succeeds on the respective revisions |
| Edit only the PR description | No submission or application result changes because the record belongs to the commit |
| Open two pull requests at the same head commit | Both use the same committed record and receive the same submission result |
| Give those pull requests different base commits | Both retain the same head-bound submission result |
| Leave `.github/submission.md` unchanged from the head's first parent | `Submission record v1` fails before publishing success |
| Push a documented lint violation, then repair it | The affected application job fails and succeeds on the respective revisions |
| Open a docs-only PR after the pilot merges | Named application jobs skip successfully and prose still runs |
| Inspect a PR CI run | It publishes no Pages artifact or deployment |
| Inspect successful main CI and deployment | Download identifies the originating main CI run and deploys its artifact |

Inspect actual logs and the merge box. Do not treat a locally simulated event as
proof that GitHub enforced the corresponding gate.

## Failure and recovery

If main CI fails, stop the rollout and repair through a reviewed PR. The replacement
workflow must not deploy a failed CI run. If deployment fails, inspect its artifact
lookup and current-main guards before rerunning anything.

A bad release needs a human-reviewed revert PR. Test the resulting main commit and
deploy its artifact. The current-main guards intentionally reject an older run as a
rollback mechanism. Record the failed and recovered deployment identifiers.

Backend hosting and scheduled data ingestion remain part of
[#54](https://github.com/codeforboston/boston-circular-economy/issues/54)
and the API/ETL work. Main still has an Express scaffold while the backlog proposes
FastAPI. Select the runtime, hosting, data refresh, and operational owner before
adding backend or ingestion deployment jobs.

## Launch record

Record this evidence in the activation PR or issue:

```text
Pilot acceptance and human reviewer:
Merged main commit and CI run:
Pages artifact, deployment run, and observed page:
Submission validation PR and status results:
Required contexts, producer, and ruleset readback:
Representative agent review and reviewed revision:
First work units, contributors, and available mentors:
Remaining decisions and accountable owners:
```
