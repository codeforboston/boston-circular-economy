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
  Safe path: compare the live head and body with the triggering event before
  publication. Serialize status writers, do not cancel an active writer, and suppress
  publication from a manually canceled run.
