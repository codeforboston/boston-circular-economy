## Claim

Contributors can submit explainable code changes through deterministic hooks and routed
CI checks. A cost-routed advisory review challenges the change before human review and
tested-artifact deployment.

Issue exception: This pilot implements the team process discussion before a dedicated
issue existed.

## Technical case

- Grounds: Pull requests had no CI checks, while pushes to `main` deployed the client. Contributors also asked how to request review and find bounded asynchronous work.
- Warrant and backing: Versioned checks expose repeatable failures before merge and give rotating volunteers one shared contract.
- Qualifier: The policy covers repository checks, committed submission records, agent routing, advisory review, and GitHub Pages deployment.
- Rebuttal: Passing checks and AI review cannot prove untested production, usability, accessibility, security, or decision quality.

## Decision explanation

- Why this design: One versioned path policy selects checks for local hooks and CI. A committed record makes the submission result a property of the reviewed commit.
- Why not the closest alternative: A mutable pull request body can differ between pull requests that share one commit status.
- Trade-off accepted: Each pull request must update one versioned record, and concurrent changes can conflict at that file.
- Revisit when: GitHub provides a trusted, PR-scoped required workflow on the repository's plan.

## Code quality

- Comprehension path: The committed record defines the observable claim. The implementation skill traces its decision owner and result before the review skill challenges the diff.
- Refactor boundary: The submission checker owns record structure. The trusted workflow owns head-file retrieval and status publication.
- Boundary and ownership: The routing skill owns path and model policy. CI owns merge evidence. Humans own intent and approval.
- Failure and recovery: Unknown paths run all checks. A missing, unchanged, or invalid committed record fails the submission status.
- Complexity added or removed: One versioned record removes mutable pull request identity from the commit-scoped status decision.

## Risk and scope

- Risk lane: Yellow
- In scope: hooks, routed CI, advisory review, tested-artifact deployment, submission standards, prose checks, skills, model routing, and ETL lint configuration.
- Out of scope: autonomous approval, autonomous merge, a secret-bearing custom review Action, backend deployment, and production monitoring.
- Important invariants: Pull requests cannot deploy. Models cannot determine check results. Humans retain accountable decisions.

## What changed

- Add `Prose`, `Frontend`, `Server`, and `ETL` checks with immutable action pins and fixed runtimes.
- Add a tested changed-file router that fails closed for unknown paths and policy changes.
- Add local commit and push hooks that consume the same routing policy.
- Add a committed submission record for rationale, alternatives, risk, evidence, and accountability.
- Add code-change standards for ownership, failure, recovery, and refactor boundaries.
- Add capability defaults for deterministic tools, Luna, Terra, Sol, specialists, and humans.
- Add self-explanatory implementation and independent review skills.
- Add the pinned ETL lint toolchain and format existing ETL code without changing its data contracts.
- Deploy the exact client artifact produced by successful main-branch CI.
- Import and extend the Library of Context communication layer with Toulmin and ASD-STE100-aligned guidance.

## Challenge cases

- A documentation-only diff skips application work while preserving named check results.
- An unknown path and a CI policy change select all application checks.
- A routing failure causes required application checks to fail rather than disappear.
- Pull-request CI cannot satisfy the deployment condition.
- A mutable pull request description cannot alter the committed submission result.
- Two pull requests at one head commit validate the same record and receive the same result.
- A missing or unchanged `.github/submission.md` fails before success is published.
- Module paths and workflow commands remain outside prose checks while reader-facing strings and comments remain inside.
- Action references remain outside prose checks while action names, nested values, and comments remain inside.
- JavaScript route paths remain outside prose checks while reader-facing strings remain inside.
- Python mapping keys remain outside prose checks while string values remain inside.
- Authentication and security workflow paths require Red review.
- Uncommitted review routing unions staged, unstaged, and untracked paths before applying the risk floor.
- Unrelated CI completions cannot cancel an active qualifying Pages deployment.
- Hosted frontend CI rejects generated client files that differ after the build.
- List-marker fences stay masked, including tilde fences and nested quotes.
- An unclosed list fence stops masking when visible prose leaves the list container.
- Red review stops for specialist and human escalation, including ETL credential and secret paths.

## Evidence

| Check | Result | Evidence or reason not run |
|---|---|---|
| Client lint and build | Pass | `npm run lint -w client` and `npm run build -w client` |
| Server lint and build | Pass | `npm run lint -w server` and `npm run build -w server` |
| ETL tests | Pass | Ruff checks pass and pytest reports 7 passed |
| Technical prose and editorial style | Pass | Full repository scan and 86 communication and submission tests |
| Routing policy | Pass | 32 routing and hook-context tests, policy validation, and model-route samples |
| Review policy and model routing | Pass | 22 local-runner tests and independent delivery challenges |
| Local hook configuration | Pass | Pre-commit validation plus commit-stage and push-stage runs |
| Workflow syntax | Pass | Actionlint 1.7.11 and YAML parsing |
| Hosted pull-request CI | Not run | Hosted CI starts after this record enters the commit |
| Manual user journey | Not affected | No application behavior changes |
| Accessibility / responsive | Not affected | No visible interface changes |
| Security / privacy / recovery | Pass | Restricted tokens, action pins, failed-route closure, and tested-artifact deployment |

## AI assistance

- [ ] No substantial AI assistance
- [x] AI assisted with exploration or planning
- [x] AI assisted with implementation or tests
- [x] AI assisted with review or challenge

I read and understand the submitted diff. I verified the evidence above and remain accountable for the change.

## Review focus and uncertainty

Review the committed-record boundary, path mapping, evidence threshold, model defaults,
and protected-branch activation steps.

The repository has not observed the submission workflow from `main`. A repository
administrator must configure the named required checks only after the hosted evidence
exists. Managed review also needs repository connection and team enablement.

## Documentation and learning

- [ ] No documentation change is needed
- [x] I updated the relevant README, `AGENTS.md`, decision record, or runbook
- [ ] I recorded a follow-up issue for remaining work

Updated contributor guidance, the code-change standard, architecture notes, decision
records, and the delivery playbook.
