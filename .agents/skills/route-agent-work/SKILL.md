---
name: route-agent-work
description: Split agent-assisted development into bounded tasks and route each task to deterministic hooks, a lower-cost general agent, a high-reasoning integration agent, a specialist, or a human decision owner. Use when planning multi-agent work, delegating a subtask, reducing token or model cost, selecting an agent model, designing agent hooks, or deciding whether an AI agent should perform work at all.
---

# Route Agent Work

Choose the least costly reliable executor for each bounded task. Cost includes model
tokens, tool runtime, review effort, and the cost of correcting an error.

## Route in this order

1. Use a deterministic hook, script, compiler, linter, test, schema validator, or CI
   job when it can decide the result.
2. Use a repository skill or template when stable instructions can produce the result.
3. Use a lower-cost general agent for a bounded task with objective acceptance checks.
4. Use a high-reasoning agent for ambiguous integration, conflicting evidence, or
   cross-subsystem synthesis.
5. Use a relevant specialist for security, privacy, accessibility, data migration, or
   another expert boundary.
6. Send product intent, value judgments, risk acceptance, approval, and merge decisions
   to the accountable human.

Do not create a subordinate task when coordination costs more than the bounded work.
Do not send the same task to several agents unless independent comparison is necessary.

## Match executor to work

| Work type | Preferred executor | Examples |
|---|---|---|
| Exact mechanical decision | Hook or tool | Format, compile, lint, test, schema validation, secret scan |
| Repeated project method | Skill or template | Work-unit shaping, technical case, PR evidence |
| Narrow and reversible | Lower-cost agent | File inventory, focused test, small refactor, evidence table |
| Ambiguous and cross-cutting | High-reasoning agent | Architecture synthesis, conflict resolution, final integration |
| Specialized high-impact risk | Specialist plus human | Security boundary, privacy decision, migration, critical accessibility |
| Intent or accountability | Human | Priority, scope expansion, risk acceptance, approval, merge |

Use the lower-cost models that the active environment provides. A model such as Terra
is suitable when the task is bounded and its result has an objective check. Model names,
availability, and prices can change. Route by capability and evidence, not by name.

Read `references/delivery-routing.json` for the repository defaults. The defaults use
Luna for Green bounded work, Terra for Yellow bounded work, and Sol for integration.
The names are reviewed policy values. They are not permanent capability claims.

Inspect the selected route before delegation:

```bash
python3 -B .agents/skills/route-agent-work/scripts/route_work.py \
  recommend --task-type bounded --risk yellow
```

Use `mechanical` for an exact tool decision and `repeated_method` for a skill. Use
`integration`, `specialist`, or `intent` only when the task meets that boundary.
A Red lane keeps exact mechanical work on its tool and adds a pre-implementation human
checkpoint. Red judgment requires a specialist and the accountable human.

## Make a bounded delegation packet

Give a subordinate agent only the context it needs:

```markdown
Objective: <one result>
Inputs: <files, issue, or evidence>
Constraints: <scope, invariants, prohibited actions>
Output: <artifact or concise finding>
Validation: <command or acceptance test>
Stop and return when: <completion or escalation condition>
```

Use file paths and stable links instead of pasting entire repositories or long chat
histories. Fork full conversation context only when the task depends on that history.
Set an explicit output limit for inventories, research results, and reviews.

## Use deterministic hooks

Place repeatable decisions near the state transition that needs them:

- local formatting and focused tests during implementation.
- pull-request CI before human review and merge.
- protected-branch checks before the merge transition.
- deployment only after the exact commit passes its required checks.
- scheduled dependency checks outside the implementation conversation.

Keep policy in versioned skills, templates, and `AGENTS.md`. Keep executable assertions
in tests and workflows. Do not spend model tokens re-evaluating an exact rule that a
trusted tool can enforce.

The same policy selects local and CI checks. Classify an explicit file set with:

```bash
python3 -B .agents/skills/route-agent-work/scripts/route_work.py \
  classify client/src/App.tsx
```

Unknown paths run every application check. A routing policy or CI change also runs
every application check. This failure mode favors evidence over compute savings.

## Escalate deliberately

Escalate from a lower-cost agent when:

- evidence conflicts across subsystems.
- the task needs unstated product intent.
- the proposed action expands scope or has destructive effects.
- no objective validation can bound the error.
- the work enters a Red risk lane.

Return the smallest useful escalation packet. Include the unresolved claim, evidence,
failed validation, and required decision. Do not repeat completed exploration.

## Integrate and verify

The orchestrating agent owns the combined result. It must inspect subordinate evidence,
resolve conflicts, run applicable deterministic checks, and report remaining
uncertainty. A subordinate success message is not proof.
