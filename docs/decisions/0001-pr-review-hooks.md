# Decision: Use Managed Codex for Pull Request Review

- Status: Proposed
- Date: 2026-09-04
- Owners: Circular Economy maintainers
- Related issue: Pull request #55 implements the pilot before a dedicated issue exists.

## Claim

Use managed Codex Code Review as the pull request review hook during this pilot. Keep
CI deterministic, keep AI findings advisory, and use repository `AGENTS.md` files to
apply the Code Change Standard.

Configure `Review all PRs` with the experimental `Smart detect` trigger when the
repository is team-enabled. Keep exhaustive review and personal credit overrun disabled
during the pilot. Request another review after a material change when smart detection
does not start one. Use `@codex review` when automatic review is unavailable. Use the
local runner for an earlier challenge.

## Grounds

- [Codex GitHub review documentation](https://developers.openai.com/codex/integrations/github)
  states that the managed reviewer reads applicable `AGENTS.md` files and posts a
  standard GitHub review.
- The managed reviewer supports automatic review and the `@codex review` command. It
  posts prioritized findings under the repository review rules.
- The local Codex reviewer compares a branch with its base without modifying the
  working tree.
- The repository already uses deterministic hooks and CI for prose, routing, lint,
  builds, and tests.
- A custom GitHub Action needs an API secret and a separate comment-publishing path.

## Warrant and backing

The managed service owns model execution and GitHub review delivery. The repository
owns durable review rules in `AGENTS.md`. This boundary avoids a privileged workflow
that must combine a secret with contributor-controlled input.

[GitHub security guidance](https://docs.github.com/en/actions/reference/security/secure-use)
warns that privileged workflows can expose secrets when they execute untrusted pull
request code. The selected design keeps repository CI read-only and deterministic.

The review skill compares the claim, mechanism, diff, tests, and evidence boundary.
The communication skill gives each finding Toulmin support and direct technical
language. Human review retains intent, risk acceptance, approval, and merge authority.

## Alternatives and why not

The closest alternative is a repository workflow that runs `openai/codex-action` on
each pull request. That design can select a model and produce custom structured output.
It also needs an API key, a spending boundary, fork handling, and output publication.
It must separate trusted workflow code from untrusted pull request content.

The custom action becomes preferable when the team needs machine-readable findings,
an organization-owned API budget, or a required automated gate. The pilot does not
have those requirements or the operational owner needed to maintain that boundary.

Human review without an automated challenge pass is the lower-cost alternative. It
remains valid for a repository without Codex access. It loses during this pilot because
the team asked for a reusable PR review hook and consistent review language.

## Limits and rebuttal

Repository files cannot enable the managed GitHub integration. A maintainer with the
required repository permission must connect the repository after this change merges.
Automatic review also requires a team-enabled Codex repository.

The repository cannot select Terra, Luna, or Sol for the managed reviewer. The local
runner applies those model routes. The managed service selects its review model.

Smart detection can miss a defect introduced by a later push. A maintainer should
request `@codex review` again after a material change when no review starts. Running on
every push would reduce this gap but would spend more review credits and create repeated
feedback. The team should select that trigger if missed changes prove more costly.

Managed GitHub review does not guarantee exhaustive coverage or a fixed severity
threshold. Local review, CI, and human review still own defects, maintainability,
decision quality, and product intent. Red changes also require a qualified specialist
and a human checkpoint.

## Consequences

- Root review rules apply the Code Change Standard to every changed area.
- The `.github/AGENTS.md` rules add security and deployment checks near workflow code.
- The review skill defines evidence thresholds, priority, wording, and stop conditions.
- The local runner executes from the trusted base and treats proposed code as data.
- The runner uses Luna for bounded Green review and Terra for bounded Yellow review.
  It uses Sol only for cross-subsystem review.
- AI review does not become a required status check or a substitute for approval.
- A failed or unavailable AI review does not block deterministic CI or human review.

## Validation

- Validate the review skill with the repository skill validator.
- Run the local review runner tests without invoking a model.
- Inspect a Green, Yellow, integration, and Red dry run.
- Confirm team-enabled access before automatic review. Otherwise, use `@codex review`.
- Request one managed review on a representative pull request.
- Review false positives, missed defects, review credits, and reviewer effort after
  the first three merged pilot work units.
