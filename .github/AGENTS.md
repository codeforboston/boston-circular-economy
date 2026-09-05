# GitHub Automation Guidance

This file adds review rules for workflows and repository automation. Apply the root
`AGENTS.md` and `docs/CODE_CHANGE_STANDARD.md` first.

## Code Review Rules

### Untrusted pull request code

- Flag any workflow that gives a secret or write-capable token to pull request code,
  artifacts, metadata, or text and then executes that input. Safe path: use a read-only
  `pull_request` job, or keep privileged execution on trusted default-branch code and
  treat contributor input only as data.

### Tested deployment identity

- Flag a deployment that rebuilds, refetches mutable source, or selects an artifact
  without binding it to the successful `main` CI run. Safe path: deploy the exact
  artifact from the successful workflow run and verify its expected entry point. Trace
  event triggers, route conditions, and upstream job results before reporting a missing
  artifact.
- Flag a deployment that can publish an older successful rerun after `main` advances.
  Safe path: treat the completion event as a reconciliation signal. Resolve current
  `main`, select the newest unexpired client artifact from a successful push-CI commit
  in its history, and compare the reconciled commit with live `main` before deployment.
  This carries tested client output across later commits that did not run the client
  job. Revalidate after publication so a detected race points to the next tested
  forward deployment. Put intentional rollback in a separate, human-approved path.

### Required check continuity

- Flag path or event routing that can leave a required check absent, pending, or green
  after its router fails. Safe path: create stable named jobs and fail closed when the
  router cannot classify a change.

### Pull request head status

- Flag a `pull_request_target` gate that relies on its base-commit job context. Safe
  path: run only trusted base code, treat pull request metadata as data, and publish a
  fixed status context on the pull request head. Limit the token to status writes and
  repository reads.
- Flag a status writer when an older run can overwrite a newer pull request result.
  Safe path: compare the live head with the triggering event before publication.
  Serialize status writers by head commit, do not cancel an active writer, and suppress
  publication from a manually canceled run. Publish only a terminal result after the
  final live-head check. A shared commit status must not be stranded at `pending` by a
  stale pull request run.
- Flag a commit status whose result depends on mutable pull request metadata. Two pull
  requests at one head commit share statuses but can have different titles, bodies, or
  labels. Safe path: validate a versioned record fetched from the exact head as inert
  data. Require the head commit to change that record from its first parent. This rule
  keeps the result intrinsic to the head and rejects inherited evidence.
- Flag a change to a versioned submission context's terminal validation predicate or
  target commit. A shared head can receive conflicting terminal results from two
  checker revisions. Safe path: create a new context version, migrate the
  protected-branch rule, and retire the old context after open pull requests move to
  the new policy. Trigger coverage and intermediate-state safety corrections can keep
  the context when they do not change the terminal predicate or target commit.
