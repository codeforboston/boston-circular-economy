# AGENTS.md

This repository builds a service that helps Greater Boston residents find circular-economy resources such as repair, reuse, and donation services. Human contributors own product decisions, submitted code, reviews, and merges. AI agents support that work by producing plans, changes, tests, and evidence.

## Repository map

- `client/`: React, TypeScript, Vite, and TanStack Router.
- `server/`: Express and TypeScript API.
- `etl/`: Python 3.14 data collection, normalization, matching, and persistence.
- `data-explorations/`: exploratory source research and samples. Do not treat samples as production contracts.
- `docs/`: durable product and engineering decisions.

Read the nearest README before changing a subsystem. Read the linked GitHub issue and any parent issue before implementation.

## Communication contract

Every agent must read and apply
[`make-evidence-based-technical-case`](.agents/skills/make-evidence-based-technical-case/SKILL.md)
before it creates, edits, reviews, or summarizes technical communication. This rule
applies to plans, issue comments, mentor guidance, pull requests, reviews, decision
records, documentation, status reports, and code comments.

Use Toulmin reasoning to connect each claim to grounds and a warrant. State applicable
backing, qualifiers, and rebuttals. Separate observed facts from inferences. Cite a
file, test, measurement, reproducible behavior, project decision, or authoritative
source for consequential claims.

Use ASD-STE100-aligned Simplified Technical English. Prefer active voice, compact
sentences, defined terms, and one stable term for each concept. Do not claim formal
ASD-STE100 compliance without qualified human review.

Write each artifact in one editorial present. Remove prompt narration, edit history,
empty transitions, promotional claims, and formulaic AI phrases. Use cadence to expose
the mechanism, evidence, condition, and consequence.

Run the repository prose checker before submitting reader-facing text:

```bash
python3 -B .agents/skills/make-evidence-based-technical-case/scripts/check_prose.py .
```

The checker applies sentence and paragraph rules to Markdown. It checks prose-bearing
source and configuration files for high-signal editorial violations. Human review
remains responsible for accuracy, active voice, term meaning, cadence, and rhetorical
fairness.

## Self-explanatory code contract

Every agent that writes or refactors production code must read and apply
[`write-self-explanatory-code`](.agents/skills/write-self-explanatory-code/SKILL.md).
Define the observable contract before implementation. Make purpose, ownership,
dependencies, failure behavior, and the safe refactor boundary visible in repository
evidence.

Do not use comments, documentation volume, test count, or an agent summary as a proxy
for comprehension. Names, types, interfaces, module boundaries, validation, and
behavior tests should expose ordinary behavior. Comments should preserve only the
non-obvious reason, invariant, or recovery rule.

## Agent routing and token cost

An agent that delegates work must read and apply
[`route-agent-work`](.agents/skills/route-agent-work/SKILL.md). Use deterministic hooks,
tests, and CI for exact decisions. Use a lower-cost agent, such as Terra, for a bounded
task with an objective check. Reserve high-reasoning agents for ambiguous integration,
conflicting evidence, or cross-subsystem decisions.

Give a subordinate agent one objective and only the required context. Define its output,
validation, and stop condition. Do not duplicate exploration across agents. A human
retains product intent, risk acceptance, approval, and merge authority.

Inspect the machine-readable route before delegating bounded work:

```bash
python3 -B .agents/skills/route-agent-work/scripts/route_work.py \
  recommend --task-type bounded --risk yellow
```

The routing file selects Luna for bounded Green work and Terra for bounded Yellow work.
Sol handles ambiguous integration. Exact Red work stays on deterministic tools and adds
a human checkpoint. Red judgment requires a specialist and the accountable human.

## Setup and checks

Use locked dependencies. Do not claim a check passed unless you ran it.

```bash
# JavaScript and TypeScript workspaces
npm ci --no-audit --no-fund
npm run lint
npm run build

# Python ETL
cd etl
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest

# Repository prose
cd ..
python3 -B .agents/skills/make-evidence-based-technical-case/scripts/check_prose.py .
```

Run the smallest relevant check while iterating. Run every applicable check before opening or updating a pull request. CI is the merge evidence of record.

Install the repository hooks once in each clone:

```bash
uv tool install pre-commit
pre-commit install --hook-type pre-commit --hook-type pre-push
```

The commit hook checks changed prose and tests routing policy changes. The push hook
uses the same file policy as CI to run applicable subsystem checks.

## Work-unit protocol

Start from one GitHub issue that has:

- one observable outcome.
- testable acceptance criteria.
- explicit in-scope and out-of-scope boundaries.
- known dependencies and unresolved decisions.
- a Green, Yellow, or Red risk lane.
- expected evidence.
- the requested mentor checkpoint.

If an issue cannot fit one pull request or roughly one to four focused sessions, propose a split before writing code. Do not silently decide unresolved product, data, accessibility, privacy, or architecture questions.

Before implementation, restate the claim in this form:

> After this change, [actor or system] can [observable result] under [important conditions].

Then identify the affected subsystem, invariants, failure cases, validation commands, and remaining uncertainty.
State why the available grounds support the claim. Name the strongest condition that
could defeat it.

Follow [`docs/CODE_CHANGE_STANDARD.md`](docs/CODE_CHANGE_STANDARD.md). Explain why the
selected mechanism supports the claim and why the closest credible alternative loses.
State ownership, failure, recovery, and complexity effects in the committed submission
record.

## Risk lanes

- **Green:** documentation, prototypes, isolated styling, and behavior-preserving refactors. Use focused checks and a quick human review.
- **Yellow:** user behavior, APIs, data transforms, routing, and business rules. Add behavior tests and request a human review of the important decision.
- **Red:** authentication, authorization, privacy, destructive operations, migrations, and critical accessibility. Stop for a mentor or maintainer design checkpoint before implementation. Require adversarial tests and a recovery or rollback plan.

Use Yellow when the lane is unclear. A file under `client/src/pages/dev/` may move faster, but it must still build and must not expose secrets or personal data.

## Implementation rules

- Keep one issue per pull request. Do not mix unrelated cleanup into the change.
- Preserve public contracts unless the issue explicitly changes them.
- Add or update tests for changed behavior. Never remove a test only to make CI pass.
- Exercise expected, boundary, dependency-failure, and historical regression cases that apply.
- Keep provider-specific data behind ETL source boundaries.
- Keep generated files generated. Do not hand-edit `client/src/routeTree.gen.ts` unless the router workflow requires it.
- Use names, types, interfaces, and tests to explain behavior. Add comments for
  non-obvious reasons, invariants, compatibility boundaries, or failure behavior.
- Keep each rule, state transition, and side effect under one identifiable owner.
- Expose a stable boundary where a future maintainer can change the behavior without
  unrelated edits.
- Do not add a comment that only restates the next line of code.
- Never call paid or rate-limited external APIs in the default test suite.
- Never commit API keys, credentials, local databases, or personally identifiable information. Never paste them into an AI prompt.

## Pull requests and review

Replace `.github/submission.md` with a completed copy of
`.github/pull_request_template.md` and commit it with the change. Link the issue, state
the risk lane, list checks that ran and did not run, and disclose substantial AI
assistance. The disclosure is about review context, not authorship. The pull request
description can mirror the committed record for reviewer convenience.

The final head commit must update `.github/submission.md` from its first parent. Amend
the record when a follow-up commit changes the evidence. This rule gives every pull
request at one head commit the same submission result.

Every agent that reviews a code change must read and apply
[`review-code-change`](.agents/skills/review-code-change/SKILL.md). Keep the review
independent from implementation. Route local reviews through the repository model
policy, and leave exact checks to hooks and CI.

An AI review is advisory. It must cite a file, line, failing command, or reproducible behavior. It should return no finding when evidence does not support a finding. It must not approve or merge its own work.

A review finding must state its claim, grounds, warrant, qualifier, and relevant
rebuttal. Use the compact risk, mechanical action, and supported-state order when the
full structure would obscure a routine finding.

Human reviewers own intent, tradeoffs, and the merge decision. Resolve all review threads and keep the required CI checks green. Add durable lessons to this file, a subsystem README, or a decision record instead of leaving them only in chat.

See `docs/AI_DELIVERY_PLAYBOOK.md` for issue selection, mentoring checkpoints, and the complete delivery loop.

## Code Review Rules

### Contract and claim

- Flag code that contradicts the committed submission claim, scope, qualifier, or a
  documented public contract. Cite the conflicting behavior and its shortest useful location.
  Also flag changed behavior that cannot be traced from its entry point through one
  decision owner to an observable result. Safe path: align the contract, ownership,
  implementation, and behavior test, or obtain a human-approved scope change.

### Failure and recovery

- Flag a changed dependency or side effect that can fail without a signal,
  containment, or supported recovery. State the realistic failure condition and user
  or operator effect. Safe path: make the failure observable and preserve a supported
  retry, rollback, or fallback.

### Behavioral evidence

- Flag a changed branch, parser, routing rule, or data rule that lacks a behavior test
  for a plausible boundary or failure case. Do not report formatting, lint, or another
  exact CI result. Safe path: add the smallest test that observes the contract.
