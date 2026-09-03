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

## Setup and checks

Use locked dependencies. Do not claim a check passed unless you ran it.

```bash
# JavaScript and TypeScript workspaces
npm ci
npm run lint
npm run build

# Python ETL
cd etl
uv sync --locked --dev
uv run ruff check .
uv run ruff format --check .
uv run pytest
```

Run the smallest relevant check while iterating. Run every applicable check before opening or updating a pull request. CI is the merge evidence of record.

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
- Never call paid or rate-limited external APIs in the default test suite.
- Never commit API keys, credentials, local databases, or personally identifiable information. Never paste them into an AI prompt.

## Pull requests and review

Use `.github/pull_request_template.md`. Link the issue, state the risk lane, list checks that ran and did not run, and disclose substantial AI assistance. The disclosure is about review context, not authorship.

An AI review is advisory. It must cite a file, line, failing command, or reproducible behavior. It should return no finding when evidence does not support a finding. It must not approve or merge its own work.

A review finding must state its claim, grounds, warrant, qualifier, and relevant
rebuttal. Use the compact risk, mechanical action, and supported-state order when the
full structure would obscure a routine finding.

Human reviewers own intent, tradeoffs, and the merge decision. Resolve all review threads and keep the required CI checks green. Add durable lessons to this file, a subsystem README, or a decision record instead of leaving them only in chat.

See `docs/AI_DELIVERY_PLAYBOOK.md` for issue selection, mentoring checkpoints, and the complete delivery loop.
