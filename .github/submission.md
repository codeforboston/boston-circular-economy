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
- Boundary and ownership: The trusted local runner owns review-route selection. The routing skill owns delivery policy. CI owns merge evidence. The server workspace owns runtime dependencies. Humans own intent and approval.
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
- Execute local review logic and routing policy from one resolved trusted-base commit.
- Treat the proposed review tree as data before the read-only Codex sandbox starts.
- Keep review command-construction tests independent of the caller's working-tree risk.
- Align the managed-review decision record with the review severities observed during this validation.
- Route ACL and RBAC modules in every application subsystem to Red review.
- Route destructive utilities throughout each subsystem to Red review while excluding fixture data.
- Route `destroy` utility paths to Red review across all three application subsystems.
- Route `remove` utility paths to Red review across all three application subsystems.
- Route `wipe` and `truncate` utility paths to Red review across all three application subsystems.
- Declare the server's existing SQLite runtime and types, and use its emitted JavaScript import path.
- Refresh the locked Node dependency graph to include the native SQLite package.
- Add the pinned ETL lint toolchain and format existing ETL code without changing its data contracts.
- Deploy the newest unexpired client artifact from a successful CI commit in current `main` history.
- Confirm that the selected CI run contains an unexpired client artifact before deployment.
- Serialize qualifying Pages deployments so an artifact-free successor cannot cancel an active publisher.
- Carry tested client output across successful later commits that did not run the client job.
- Require successful CI for live `main` before selecting an ancestor client artifact.
- Import and extend the Library of Context communication layer with Toulmin and ASD-STE100-aligned guidance.
- Scan reader-facing assignment-manifest values while excluding machine-only JSON metadata.
- Scan reader-facing assignment step labels while retaining machine-only step metadata exclusions.
- Mask valid Markdown inline-code spans that cross a line break.
- Apply the same multiline inline-code boundary to committed submission validation.
- Keep Python environment keys outside prose checks and decode JavaScript reader strings before checking them.
- Track uniquely assigned Python path variables when classifying later path components.
- Recognize path-producing methods only on tracked Python path values.
- Use one Markdown inline-code parser that keeps escaped backticks visible to both prose and submission checks.
- Reject an unclosed visible HTML comment in a submission record while allowing comment syntax in code examples.
- Publish one terminal submission status after the final live-head check instead of publishing an intermediate pending status.
- Mask inline code before parsing submission headings, labels, checkboxes, issue references, evidence tables, and attestation text.
- Check contractions in visible Markdown headings without applying paragraph limits to those headings.
- Keep Markdown link labels and titles in prose checks while excluding destinations and bare URLs.
- Decode non-raw Python reader strings before editorial matching, including f-string literal segments.
- Recognize chained styled-components tags as machine-language templates.
- Decode Markdown entities before language checks so entity terminators do not look like prose semicolons.
- Validate every work-unit manifest against its schema in commit hooks, push hooks, and CI.
- Discover numbered work-unit manifests in one tested script so future units cannot bypass validation.
- Add an invalid manifest fixture that proves CI rejects missing required fields.
- Require accepted work units to name a reviewed revision and test the invalid terminal state in CI.
- Require accepted work units to name artifacts, a reviewer, and a review date.
- Bind each numbered manifest ID to its filename and reject duplicate IDs.
- Reject dependencies that do not identify a discovered work unit.
- Reject self-dependencies and cycles in the work-unit graph.
- Run the schema validator from a repository lock that fixes its full dependency graph.
- Start the built server with temporary SQLite and verify `/ping` in local push checks and CI.
- Route every GitHub Actions workflow change to Red review because any workflow can change permissions or authorization.
- Route every repo-local GitHub Action change to Red review because it executes with its caller's privileges.
- Route access-control modules in every application subsystem to Red review.
- Route verb-named authentication and authorization handlers to Red review.
- Route trusted submission-status helpers to Red review because they run with a status-writing token.
- Route `migrate` utility names to Red review in the ETL and server subsystems.
- Add authorization to the Red risk option in the work-unit issue form.
- Check contractions and semicolons in visible Markdown table cells while keeping inline code inert.
- Reject backticks in backtick-fence info strings so invalid fences cannot hide visible prose.
- Preserve indented paragraph continuations while masking real indented code blocks.
- Check visible Markdown image alt text while excluding the image destination.
- Scan visible HTML text and reader-facing attributes while excluding code and implementation-only values.
- Close the smoke-test SQLite connection before removing its temporary directory.
- Treat every matching backtick inside an open code span as a closing delimiter, even after a backslash.
- Scan values on visible HTML input types while excluding hidden and choice-control values.
- Exclude Python file and path arguments from reader prose while retaining ordinary messages.
- Exclude patterns passed to recognized Python regular-expression APIs from reader prose.
- Exclude SQL passed through recognizable Python database receivers from reader prose.
- Treat only inline-link labels as substantive submission content while preserving visible autolinks.
- Accept zero to three spaces before submission headings while masking four-space code blocks.
- Exclude quoted JavaScript property keys from prose while continuing to scan their values.
- Scan only reader-facing JSX attributes and visible native-input values.
- Classify raw HTML inside Markdown so visible text and alt text remain subject to prose checks.
- Keep Markdown reference labels and titles visible while masking resolved identifiers and definition labels.
- Scan `label` attributes only on HTML and JSX elements that render them.
- Require a reference destination before treating its identifier as hidden Markdown control text.
- Keep TypeScript generic arrows as code while retaining JSX parsing for JSX-capable source files.
- Decode YAML quoted-scalar escapes before checking reader-facing values.
- Decode TOML basic and multiline-basic strings while retaining literal-string semantics.
- Decode character references in direct JSX text and static reader-facing attributes.
- Exclude reusable-workflow `uses` targets while retaining reader-facing job names.
- End required submission sections at the next level-one or level-two heading.
- Keep the pre-commit prose filter synchronized with every scanned suffix, including HTML.
- Scan literal React `children` props while retaining machine-only JSX prop exclusions.
- Join escaped physical lines before editorial matching while retaining source line reports.
- Scan reader-facing static values in JSX object-literal spreads while excluding dynamic spreads and machine-only properties.
- Scan decoded CSS `content` strings while excluding selectors, URLs, custom properties, and other machine values.
- Parse static `dangerouslySetInnerHTML` values as HTML prose while leaving dynamic expressions inert.
- Scan human-readable `aria-valuetext` in HTML and JSX.
- Scan visible Markdown blockquotes and semicolons in headings.
- Join static JSX expression literals before checking rendered wording.
- Join ordinary JavaScript literal additions before checking rendered wording.
- Join implicit and added Python reader strings before checking rendered wording.
- Apply the semicolon rule to every masked reader-facing source format.
- Scan reader-facing text and accessible attributes in standalone SVG files.
- Scan visible HTML inside standalone SVG `foreignObject` elements.
- Preserve suppressed HTML element state across complete Markdown documents.
- Use the trusted-base local review command in contributor guidance.
- Keep JavaScript and TypeScript database operation strings outside prose checks.
- Scan an unclosed Markdown front-matter region as visible prose.
- Scan deliverable names in work-unit manifests as reader-facing assignment prose.
- Join adjacent inline HTML, SVG, and raw-Markdown text before wording checks.
- Preserve reader prose in multiline quoted YAML scalars.
- Join output from string-only JavaScript template interpolations.
- Route password and authentication-token handlers to Red review.
- Bind changed-file discovery and the review command to one resolved base commit.
- Keep programmatic CSS payload strings outside reader-prose checks.
- Resolve a shared review base and trusted-policy ref once.
- Keep static protocol-header arguments outside reader-prose checks.
- Scan `aria-roledescription` values in HTML and JSX.
- Enforce accepted prerequisites before a dependent work unit can start.
- Route client persistence migrations to Red review.
- Scan `aria-placeholder` values in HTML and JSX.

## Challenge cases

- A documentation-only diff skips application work while preserving named check results.
- An unknown path and a CI policy change select all application checks.
- A routing failure causes required application checks to fail rather than disappear.
- A pull request retargeted to `main` receives both required workflows without another push.
- Pull-request CI cannot satisfy the deployment condition.
- A successful documentation-only main run without a client artifact leaves Pages unchanged.
- An artifact-free successor waits for an active qualifying Pages publisher.
- A later non-client commit can publish the preceding tested client artifact.
- An incomplete or failed live `main` revision cannot start an ancestor-artifact deployment.
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
- Assignment step labels fail on prohibited wording while adjacent model and routing fields remain inert.
- Every workflow path requires Red review, including ordinary names such as `ci.yml` that can still change permissions.
- Trusted submission checkers require Red review before they can control a commit status.
- ETL and server utilities named with `migrate` require Red review.
- The work-unit issue form identifies authorization changes as Red.
- Documentation manifests retain the Green review route.
- Destructive utilities outside source directories require Red review, while fixture data remains Yellow.
- Destructive utilities named with `wipe` or `truncate` require Red review.
- Destructive utilities named with `remove` require Red review.
- Uncommitted review routing unions staged, unstaged, and untracked paths before applying the risk floor.
- Command construction retains uncommitted scope even while workflow edits raise the live tree to Red.
- A modified target routing script remains inert while trusted-base policy selects the review route.
- Unrelated CI completions cannot cancel an active qualifying Pages deployment.
- Hosted frontend CI rejects generated client files that differ after the build.
- List-marker fences stay masked, including tilde fences and nested quotes.
- Inline-code spans stay masked when matching backticks occur after a line break.
- Escaped Markdown backticks remain visible punctuation and cannot hide prose or raw HTML.
- A visible unclosed HTML comment fails submission validation, while the same syntax in a code span or fenced example remains inert.
- A stale run for one of two pull requests at the same head cannot leave the shared commit status pending.
- A required heading, label, checkbox, issue reference, or attestation inside inline code cannot satisfy the submission contract.
- A contraction in a visible Markdown heading fails even though the heading is outside paragraph-length checks.
- A prohibited term in an external Markdown destination or bare URL remains inert, while the same term in a visible label or title fails.
- Hexadecimal and Unicode escapes in non-raw Python reader strings are checked as rendered text, while raw strings retain literal backslashes.
- A Markdown entity does not create a false semicolon finding, and an encoded prohibited term remains visible to editorial checks.
- Five valid work-unit manifests pass schema validation, while the incomplete fixture fails on its missing fields.
- An otherwise valid accepted work unit fails when its completion record omits the reviewed revision.
- An accepted work unit fails when its artifact list, reviewer, or review date is empty.
- An accepted work unit fails when its review metadata contains only whitespace.
- A numbered manifest fails when its ID differs from its filename or duplicates another manifest ID.
- A manifest fails when its dependency does not identify a discovered work unit.
- A manifest fails when its dependencies include itself or form a cycle.
- Server smoke testing imports the native SQLite binding, uses a temporary database, binds an available port, and requires a successful `pong` response.
- An unclosed list fence stops masking when visible prose leaves the list container.
- An unclosed quote fence stops masking when the quote depth decreases.
- A clean server install initializes temporary SQLite and returns `pong` from `/ping`.
- An unavailable SQLite directory stops server startup with a visible error.
- Contractions and semicolons in visible table cells fail prose checks, while table-cell inline code remains inert.
- An invalid backtick fence cannot mask the prose before the next valid fence.
- A four-space-indented line after live paragraph text remains subject to prose checks.
- A contraction or semicolon in image alt text fails while its image destination remains inert.
- HTML text and alt text fail editorial checks, while script content and image source paths remain inert.
- The server smoke test closes SQLite before deleting its database directory on every platform.
- A backslash before a closing code-span backtick cannot hide the prose that follows it.
- Submit and text-input values fail editorial checks, while hidden-input values remain machine data.
- Python path constructors, file calls, path joins, and path composition remain outside prose checks.
- Python regular-expression patterns remain machine input while ordinary messages remain visible.
- Python database operations remain machine input while unrelated `execute` calls and messages remain visible.
- An empty Markdown link cannot satisfy a rationale field, while a visible autolink can.
- A submission heading with three leading spaces passes, while a four-space heading remains code.
- A quoted JavaScript object key remains inert, while a reader-facing value still fails.
- JSX test IDs and class names remain inert, while accessible labels and visible input values fail.
- A raw Markdown image source remains inert, while its alt text remains visible to the checker.
- An empty reference link cannot satisfy a rationale field, even when its definition supplies an identifier and destination.
- Resolved Markdown reference identifiers remain inert. Unresolved syntax, visible link labels, and optional titles remain subject to prose checks.
- Labels on `optgroup`, `option`, and `track` remain visible, while unrelated element labels remain machine data.
- A blank reference definition leaves its unresolved identifier visible to submission checks.
- TypeScript generic arrows remain inert at top level and inside template expressions.
- YAML double-quoted Unicode escapes and doubled single quotes are checked as rendered text.
- TOML basic and multiline-basic Unicode escapes are checked as rendered text, while literal strings retain their backslashes.
- JSX character references decode in direct text and static attributes, but not inside JavaScript expression strings.
- A reusable-workflow path remains machine input, while its job name remains subject to prose checks.
- A level-one heading ends the preceding required section, so later labels cannot fill it.
- An HTML-only change selects the commit-stage prose hook.
- Static and expression `children` text remains visible, while `data-children` remains machine metadata.
- JavaScript, Python, and TOML reader strings preserve word adjacency across escaped physical line endings.
- Literal JSX spreads expose reader-facing `children` and accessibility labels without exposing dynamic spreads or machine-only keys.
- CSS generated text decodes string escapes, while custom properties and resource URLs remain inert.
- Static JSX HTML injection exposes visible text and attributes but excludes scripts and dynamic HTML.
- Human-readable ARIA value text remains subject to the prose policy.
- Visible blockquote text and heading semicolons remain subject to the prose policy.
- Static JSX string addition cannot split a prohibited contraction across literals.
- Static JavaScript and Python string expressions cannot split prohibited wording.
- SVG titles, descriptions, text, and accessible attributes remain visible while metadata and scripts remain inert.
- HTML inside an SVG `foreignObject` remains visible while drawing paths remain inert.
- Language syntax stays inert while semicolons in reader-facing source values fail.
- Multiline Markdown `pre` and `script` elements keep their content outside prose checks.
- SQL statement separators remain machine syntax while adjacent reader text is checked.
- An unclosed front-matter marker cannot hide the Markdown content that follows it.
- A prohibited contraction split by inline markup or a comment remains visible, while
  separate rendered blocks remain distinct.
- A work-unit deliverable name cannot carry prohibited assignment wording.
- A multiline quoted YAML value cannot hide reader-facing wording on a continuation line.
- A static template interpolation cannot split a prohibited contraction.
- Password and authentication-token handlers require Red review, while design-token
  files retain the normal application route.
- Verb-named authentication and authorization handlers require Red review in each application subsystem.
- A mutable base ref can move after resolution without changing the classified diff or
  the base passed to the review command.
- CSSOM payload assignments and calls remain machine syntax, while adjacent reader text
  remains subject to wording checks.
- One mutable ref used for both the base and trusted policy cannot advance between two
  resolutions because the runner resolves it once.
- CSP, Link, and content-type values remain machine syntax, while nearby messages remain
  subject to wording checks.
- Author-defined ARIA role descriptions remain visible to wording checks.
- A dependent unit cannot enter a started, review, revision, or accepted state while a
  prerequisite remains unaccepted. The waiting state remains valid.
- Client, server, and ETL migration paths all require Red review.
- Custom textbox placeholders exposed through ARIA remain visible to wording checks.
- Generic UI header calls remain visible while known protocol response headers remain masked.
- Protocol-specific header methods remain masked when a response object uses a local alias.
- Literal-only Python f-string fields render as reader text without executing expressions.
- Child-process shell commands remain machine syntax while adjacent user messages remain visible.
- Python process commands follow standard import aliases and remain machine syntax.
- Components appended to a uniquely assigned Python path variable remain machine syntax.
- Path-method components remain machine syntax only when the receiver is a tracked path.
- Destructive `drop` utilities in each application subsystem require Red review.
- Destructive `destroy` utilities in each application subsystem require Red review.
- Destructive `remove` utilities in each application subsystem require Red review.
- ACL and RBAC modules in each application subsystem require Red review.
- Known CSS, SQL, and GraphQL template tags remain machine syntax while reader templates remain visible.
- Chained styled-components tags remain machine syntax while unrelated tagged templates remain visible.
- Red review stops for specialist and human escalation, including ETL credential and secret paths.

## Evidence

| Check | Result | Evidence or reason not run |
|---|---|---|
| Client lint and build | Pass | `npm run lint -w client` and `npm run build -w client` |
| Server lint and build | Pass | Lint and build pass. Startup creates and closes a temporary SQLite database, and `/ping` returns `pong` |
| ETL tests | Pass | Ruff checks pass and pytest reports 7 passed |
| Technical prose and editorial style | Pass | Full repository scan and 168 communication and submission tests |
| Routing policy | Pass | 44 routing, hook-context, manifest-integrity, and model-route tests |
| Review policy and model routing | Pass | 34 local-runner tests and independent delivery challenges |
| Local hook configuration | Pass | Pre-commit validation, schema validation, and commit-stage and push-stage runs |
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

Review the versioned first-parent record boundary and terminal-only status publication.
Examine Markdown fence, paragraph, table, image-alt, and code-span boundaries. Examine
link-label, reference-link, and heading boundaries. Examine YAML escape handling,
TOML basic-string escape handling, assignment step labels, TypeScript generic
classification, escaped-line source mapping, JSX character references, and static
object-literal spreads. Examine CSS generated content and static HTML injection. Examine
human-readable ARIA value text, visible blockquotes, heading semicolons, and work-unit
dependency integrity. Examine static JSX string addition and source semicolon handling.
Examine ordinary JavaScript additions and adjacent Python reader strings. Examine
element-specific HTML and JSX attributes, React children, and JavaScript property keys.
Examine trusted-base local review execution and standalone SVG reader-text boundaries,
including visible HTML inside `foreignObject` elements.
Examine semicolon coverage and multiline HTML suppression in Markdown.
Examine database-operation string classification and front-matter closure detection.
Examine deliverable-name classification and adjacent rendered-text source mapping.
Examine multiline YAML quoted scalars, static template interpolation, and the
password and authentication-token risk floor.
Examine resolved-base reuse and programmatic CSS payload classification.
Examine shared-ref resolution, protocol-header classification, and ARIA role descriptions.
Examine prerequisite-state enforcement for dependent work units.
Examine client migration routing and ARIA placeholder coverage.
Examine repo-local GitHub Action routing.
Examine access-control routing and generic header-call text visibility.
Examine protocol-header recognition on aliased response objects.
Examine literal-only Python f-string output and child-process command classification.
Examine Python process-command aliases and destructive `drop` routing.
Examine tagged and chained styled machine templates, reader-template boundaries, and
ACL and RBAC risk routing.
Examine Python path-variable and path-method propagation.
Examine destructive `destroy` and `remove` routing.
Examine Python resource identifiers, heading termination, hook suffix coverage, and the
Red workflow risk floor. Examine Python regular-expression pattern classification and
Python database-operation classification. Examine verb-named authentication and
authorization routing.

Confirm the deployment reconcile step verifies the selected
run has an unexpired client artifact before it marks the deployment ready. Confirm
the Pages concurrency group serializes qualifying runs without cancellation. Confirm
artifact selection carries tested client output through non-client commits. Confirm
live `main` has successful CI before an ancestor artifact is selected.

Confirm accepted work units identify substantive review metadata and destructive utility synonyms
retain the Red checkpoint. Confirm accepted records contain complete review metadata,
manifest IDs match unique filenames, and schema validation uses the committed lock.
Confirm submission-status helpers and `migrate` utilities retain the Red checkpoint.
Check SQLite shutdown order, native lockfile changes, path mapping, evidence threshold,
model defaults, and protected-branch activation steps.

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
