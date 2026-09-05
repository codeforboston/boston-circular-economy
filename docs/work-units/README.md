# Frontend AI Assignments

These assignments prepare UI specifications, research, wireframes, visual design, and
backend-call proposals. They do not assign production implementation.

Hubert owns frontend work selection, engineering acceptance, and the proposed backend
calls. Product and design retain their decisions. The backend lead confirms the shared
API contract before either side implements it.

## First slice

Use the [textile MVP](https://docs.google.com/document/d/1eI7OL8zppM01br13fuhXvWKAKnKWhRBOJ45NMYenpHU/edit),
specifically M2.1 and M2.2: clinic results and filters. It specifies two prototype
clinics, a 390-pixel mobile viewport, and Boston Fleet patterns.

This gives volunteers a common, bounded example. A prototype can test comprehension
and interaction without waiting for live clinic data. It cannot prove that a service
or backend capability exists.

| Assignment | Timebox | Deliverable | Start condition |
|---|---|---|---|
| [UI-001: Research](ui-001.json) | 60 minutes | Evidence note and pattern references | Available for research after checking existing claims |
| [UI-002: UI specification](ui-002.json) | 90 minutes | Screen manifest and state/action table | Reviewed UI-001 |
| [UI-003: Wireframes](ui-003.json) | 90 minutes | Two editable alternatives and a selected flow | Accepted UI-002 |
| [UI-004: Visual design](ui-004.json) | 90 minutes | One polished mobile screen and visual manifest | Selected UI-003 |
| [UI-005: Backend call](ui-005.json) | 90 minutes | Call manifest and three JSON examples | Accepted UI-002 |

UI-003 and UI-005 can proceed independently after the screen specification is accepted.
UI-004 follows the selected wireframe. Each timebox covers one focused session,
excluding the wait for human review. Stop with a decision request when the work does
not fit.

## What the manifest means

Each JSON file is an assignment packet. It names the outcome, inputs, constraints,
AI prompts, deliverables, checks, reviewer, and handoff. The
[schema](manifest.schema.json) validates that structure. Schema validity does not
prove that a design is correct or complete.

The commit hook and CI validate each `ui-NNN.json` file against the schema. IDs must be
unique and match their filenames. Dependencies must identify existing units and cannot
form a cycle. A unit can leave `waiting_for_reviewed_input` only after each prerequisite
has an `accepted` status. CI also proves that the validator rejects the invalid files in
`fixtures`.

The [screen template](screen-manifest.template.yaml) describes the resulting UI
contract: components, visible states, actions, data needs, and acceptance cases.
It is a draft template. Empty fields require decisions before implementation.

Keep product research and design originals in the project Drive or approved Figma
file. Keep assignment manifests and engineering decisions in GitHub. For an accepted
unit, record at least one nonblank artifact link. Record the reviewer, review date, and
accepted revision in the issue and completion record. Each value must contain
substantive text.

## Contributor instructions

1. Claim one issue and name your next check-in.
2. Read its manifest, source links, and prerequisite decisions.
3. Run the first AI prompt and check the sources yourself.
4. Compare the suggestions before asking the AI to generate an artifact.
5. Use the challenge prompt to find missing evidence or ambiguous behavior.
6. Inspect the deliverables and demonstrate them to the named reviewer.
7. Record one AI suggestion you changed or rejected and why.

An agent's output is a proposal until a person checks it. Do not fabricate user
research, service availability, approved design choices, or measurements.
If a source or tool is unavailable, report the exact gap and preserve completed work.

## Definition of done

Every assignment needs the named artifacts, checked acceptance criteria, contributor
explanation, and human decision. Record the artifact revision that received review.
A screenshot alone cannot establish keyboard behavior or accessibility.

Return one of these decisions:

- Accept the artifact and name the next unit.
- Request a specific revision supported by evidence.
- Stop and record the product, design, or backend decision that is missing.

Implementation work uses accepted designs and any relevant call contract. Hubert then
creates a small issue with the approved references, component boundaries, mock data,
and tests. The existing Frontend CI job checks lint and build. UI interaction,
contract, and accessibility checks need explicit implementation tasks and evidence.

## Source boundaries

- The August 25 textile MVP defines this prototype slice.
- [Fleet](https://patterns.boston.gov/) supplies Boston's component guidance.
- [Team norms](https://docs.google.com/document/d/1v_cuc_hEcx9GzcsoE8GJv83o_qlVc3QX-LhdtlUGqHA/edit) govern scoped work and durable records.
- [#38](https://github.com/codeforboston/boston-circular-economy/issues/38) contains client MVP work.
- [#46](https://github.com/codeforboston/boston-circular-economy/issues/46) and [#53](https://github.com/codeforboston/boston-circular-economy/issues/53) anchor the API handoff.

The repository currently demonstrates an Express `/ping` route. Its backlog proposes
FastAPI. These assignments specify the client's needs without choosing that migration
or claiming that clinic endpoints are implemented.
