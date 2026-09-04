---
name: write-self-explanatory-code
description: Write or refactor production code so a human maintainer can trace its purpose, contracts, ownership, failure behavior, and safe refactor boundary from repository evidence. Use for implementation, refactoring, or generated-code cleanup. Do not use comment volume or documentation volume as a proxy for comprehension.
---

# Write Self-Explanatory Code

Make the codebase carry the context needed to understand and change it. A passing test
suite is necessary, but it does not prove human comprehension.

## Establish the contract before implementation

Read the issue, nearest `AGENTS.md`, subsystem README, public interfaces, and relevant
tests. State the observable result before generating or changing code.

Identify these properties at the smallest useful boundary:

- the component purpose and the user or system behavior it supports.
- the owner of each rule, state transition, and side effect.
- accepted inputs, returned state, invariants, units, and null behavior.
- direct dependencies and caller-visible dependents.
- failure signals, containment, retry or idempotency rules, and recovery.
- non-goals, compatibility limits, and evidence that will test the contract.

Use the issue or pull request for a routine change. Add durable documentation only when
the contract spans modules, outlives the change, or cannot be expressed through code.

## Put structural context in the codebase

Give each module one coherent responsibility. Keep the rule near the state or side
effect that it governs. Make dependency direction visible through imports, parameters,
constructors, or interfaces.

Use domain names that expose purpose. Avoid names that describe only a temporary
implementation technique. Separate pure decisions from external input, storage,
network, clock, randomness, and user-interface effects.

Do not add an abstraction only to make the code look organized. Add a boundary when it
creates a stable contract, isolates a side effect, removes duplicate policy, or gives a
future change one safe location.

## Put semantic context in contracts

Use types, interfaces, schemas, validation, and exhaustive branches to expose ordinary
behavior. Make important limits visible at the call boundary.

Document a public interface when names and types cannot state:

- side effects or state ownership.
- error and empty-result meaning.
- ordering, freshness, retention, or provenance constraints.
- timeout, retry, idempotency, or partial-success behavior.
- security, privacy, accessibility, or compatibility limits.

Use comments for non-obvious reasons, rejected simplifications, invariants, and recovery
rules. Do not restate syntax. Do not preserve prompt, agent, or author history in code.

## Make tests executable explanations

Test observable contracts rather than private implementation steps. Cover the normal
path and each plausible boundary, dependency failure, and regression introduced by the
change. Give tests behavioral names that identify the condition and result.

Prefer one focused example that proves a rule over many assertions that mirror the
implementation. Keep fixtures small enough for a reviewer to understand their role.

## Pass the comprehension gate

Trace the change without relying on its generation transcript:

1. Start at the caller or external entry point.
2. Follow the input to the module that owns the decision.
3. Identify the state change or side effect.
4. Follow the result or failure signal back to the caller.
5. Locate the test that proves the contract.
6. Name the smallest safe refactor boundary.

Restructure the change when this trace requires guessing, duplicated rules, hidden
state, unexplained coupling, or a comment that compensates for an opaque design.

Record two concise fields in the pull request:

- **Comprehension path:** entry point, decision owner, and observable result.
- **Refactor boundary:** the smallest stable contract where future behavior can change.

Do not claim that code is self-explanatory because an agent can summarize it. A human
reviewer must confirm the trace, the stated boundary, and the important tradeoffs.
