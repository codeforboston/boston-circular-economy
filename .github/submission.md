## Claim

Contributors can submit explainable code changes through deterministic hooks and routed
CI checks. A cost-routed advisory review challenges the change before human review and
tested-artifact deployment.

The server also declares its existing SQLite runtime. A clean install can initialize
the local database and start.

Issue exception: This pilot implements the team process discussion before a dedicated
issue existed.

## Technical case

- Grounds: Pull requests had no CI checks, while pushes to `main` deployed the client. Contributors also asked how to request review and find bounded asynchronous work. The server imported `better-sqlite3` without declaring that runtime package.
- Warrant and backing: Versioned checks expose repeatable failures before merge and give rotating volunteers one shared contract. Declaring direct runtime imports makes clean installs reproducible.
- Qualifier: The policy covers repository checks, committed submission records, agent routing, advisory review, and GitHub Pages deployment. Server evidence covers temporary local SQLite and `/ping` only.
- Rebuttal: Passing checks and AI review cannot prove untested production, usability, accessibility, security, or decision quality. The smoke test does not prove deployed persistence or migrations.

## Decision explanation

- Why this design: One versioned path policy selects checks for local hooks and CI. A committed record and immutable terminal-result boundary make submission results commit-bound. The workflow publishes that result only after its final live-head check. The server workspace declares the dependency owned by its database module.
- Why not the closest alternative: A mutable pull request body can differ between pull requests that share one status. Reusing a status context across checker revisions can also conflict. Omitting SQLite leaves the server's clean-install contract incomplete.
- Trade-off accepted: The final head commit must update one versioned record. A validation-result change requires a new status context and branch-rule migration. Native SQLite adds a platform dependency.
- Revisit when: Use a PR-scoped check when the repository plan supports one. Revisit SQLite when the server selects its production persistence design.

## Code quality

- Comprehension path: The committed record defines the observable claim. The implementation skill traces its owner and result before independent review. Server startup imports the database module, which initializes SQLite.
- Refactor boundary: The freshness checker owns first-parent comparison. The trusted workflow owns status publication. The server database module owns SQLite initialization.
- Boundary and ownership: The routing skill owns path and model policy. CI owns merge evidence. The server workspace owns runtime dependencies. Humans own intent and approval.
- Failure and recovery: Unknown paths run all checks. An invalid or inherited record fails submission. An inaccessible SQLite path stops startup. Correct the path and restart.
- Complexity added or removed: One record removes mutable pull request identity from the status decision. One native dependency completes an existing database import.

## Risk and scope

- Risk lane: Red
- Maintainer checkpoint: The fork owner approved the CI/CD policy and authorized its implementation on the fork before the branch was pushed.
- Adversarial evidence: Tests exercise untrusted pull-request data, status races, permission-bearing workflows, credential paths, destructive paths, and failed routing.
- Recovery and rollback: Before merge, close the pull request. After merge, revert the change, remove its required status before retiring the workflow, and redeploy the last successful Pages artifact.
- In scope: hooks, routed CI, advisory review, tested-artifact deployment, submission standards, prose checks, skills, model routing, ETL lint configuration, and local SQLite server startup.
- Out of scope: autonomous approval, autonomous merge, a secret-bearing custom review Action, backend deployment, production monitoring, database schema design, and migrations.
- Important invariants: Pull requests cannot deploy. Models cannot determine check results. One head commit has one terminal submission result. A stale pull request run cannot leave that shared status pending. Database initialization fails visibly when its file is unavailable.

## What changed

- Add `Prose`, `Frontend`, `Server`, and `ETL` checks with immutable action pins and fixed runtimes.
- Add a tested changed-file router that fails closed for unknown paths and policy changes.
- Add local commit and push hooks that consume the same routing policy.
- Add a committed submission record for rationale, alternatives, risk, evidence, and accountability.
- Version the trusted submission status and bind helper checkout to the exact workflow revision.
- Run required workflows when a pull request is edited so retargeting to `main` cannot omit their contexts.
- Add code-change standards for ownership, failure, recovery, and refactor boundaries.
- Add capability defaults for deterministic tools, Luna, Terra, Sol, specialists, and humans.
- Add self-explanatory implementation and independent review skills.
- Align the managed-review decision record with the review severities observed during this validation.
- Route destructive utilities throughout each subsystem to Red review while excluding fixture data.
- Declare the server's existing SQLite runtime and types, and use its emitted JavaScript import path.
- Refresh the locked Node dependency graph to include the native SQLite package.
- Add the pinned ETL lint toolchain and format existing ETL code without changing its data contracts.
- Deploy the exact client artifact produced by successful main-branch CI.
- Import and extend the Library of Context communication layer with Toulmin and ASD-STE100-aligned guidance.
- Scan reader-facing assignment-manifest values while excluding machine-only JSON metadata.
- Mask valid Markdown inline-code spans that cross a line break.
- Apply the same multiline inline-code boundary to committed submission validation.
- Keep Python environment keys outside prose checks and decode JavaScript reader strings before checking them.
- Use one Markdown inline-code parser that keeps escaped backticks visible to both prose and submission checks.
- Reject an unclosed visible HTML comment in a submission record while allowing comment syntax in code examples.
- Publish one terminal submission status after the final live-head check instead of publishing an intermediate pending status.

## Challenge cases

- A documentation-only diff skips application work while preserving named check results.
- An unknown path and a CI policy change select all application checks.
- A routing failure causes required application checks to fail rather than disappear.
- A pull request retargeted to `main` receives both required workflows without another push.
- Pull-request CI cannot satisfy the deployment condition.
- A mutable pull request description cannot alter the committed submission result.
- Two pull requests at one head commit receive the same result, even when their bases differ.
- Different trusted checker revisions cannot publish to the same versioned submission context.
- A missing record or one inherited from the head's first parent fails before success is published.
- Module paths and workflow commands remain outside prose checks while reader-facing strings and comments remain inside.
- Action references remain outside prose checks while action names, nested values, and comments remain inside.
- JavaScript route paths remain outside prose checks while reader-facing strings remain inside.
- JavaScript reader strings decode apostrophe and Unicode escapes before editorial checks.
- Python mapping keys remain outside prose checks while string values remain inside.
- Python environment-variable names remain outside prose checks while reader-facing values remain inside.
- Incomplete Python keeps plain, formatted, byte, and nested mapping keys outside prose checks.
- Assignment JSON decodes and checks reader-facing values while paths, identifiers, and status values remain outside the scan.
- Authentication, credential, and security workflow or utility paths require Red review across subsystem directories.
- Documentation manifests retain the Green review route.
- Destructive utilities outside source directories require Red review, while fixture data remains Yellow.
- Uncommitted review routing unions staged, unstaged, and untracked paths before applying the risk floor.
- Unrelated CI completions cannot cancel an active qualifying Pages deployment.
- Hosted frontend CI rejects generated client files that differ after the build.
- List-marker fences stay masked, including tilde fences and nested quotes.
- Inline-code spans stay masked when matching backticks occur after a line break.
- Escaped Markdown backticks remain visible punctuation and cannot hide prose or raw HTML.
- A visible unclosed HTML comment fails submission validation, while the same syntax in a code span or fenced example remains inert.
- A stale run for one of two pull requests at the same head cannot leave the shared commit status pending.
- An unclosed list fence stops masking when visible prose leaves the list container.
- An unclosed quote fence stops masking when the quote depth decreases.
- A clean server install initializes temporary SQLite and returns `pong` from `/ping`.
- An unavailable SQLite directory stops server startup with a visible error.
- Red review stops for specialist and human escalation, including ETL credential and secret paths.

## Evidence

| Check | Result | Evidence or reason not run |
|---|---|---|
| Client lint and build | Pass | `npm run lint -w client` and `npm run build -w client` |
| Server lint and build | Pass | Lint and build pass; startup creates temporary SQLite and `/ping` returns `pong` |
| ETL tests | Pass | Ruff checks pass and pytest reports 7 passed |
| Technical prose and editorial style | Pass | Full repository scan and 106 communication and submission tests |
| Routing policy | Pass | 34 routing and hook-context tests, policy validation, and model-route samples |
| Review policy and model routing | Pass | 25 local-runner tests and independent delivery challenges |
| Local hook configuration | Pass | Pre-commit validation plus commit-stage and push-stage runs |
| Workflow syntax | Pass | Actionlint 1.7.11 and YAML parsing |
| Hosted pull-request CI | Not run | Hosted CI starts after this record enters the commit |
| Manual user journey | Pass | Server starts with temporary SQLite and `GET /ping` returns `pong` |
| Accessibility / responsive | Not affected | No visible interface changes |
| Security / privacy / recovery | Pass | Maintainer checkpoint, restricted tokens, action pins, adversarial path and status tests, failed-route closure, and a revert and redeploy plan |

## AI assistance

- [ ] No substantial AI assistance
- [x] AI assisted with exploration or planning
- [x] AI assisted with implementation or tests
- [x] AI assisted with review or challenge

I read and understand the submitted diff. I verified the evidence above and remain accountable for the change.

## Review focus and uncertainty

Review the versioned first-parent record boundary, terminal-only status publication,
native SQLite lockfile changes, path mapping, evidence threshold, model defaults, and
protected-branch activation steps.

The repository has not observed the submission workflow from `main`. A repository
administrator must configure the named required checks only after the hosted evidence
exists. Managed review also needs repository connection and team enablement.
The server smoke test does not cover production persistence, schema, or migrations.

## Documentation and learning

- [ ] No documentation change is needed
- [x] I updated the relevant README, `AGENTS.md`, decision record, or runbook
- [ ] I recorded a follow-up issue for remaining work

Updated contributor guidance, the code-change standard, architecture notes, decision
records, and the delivery playbook.
