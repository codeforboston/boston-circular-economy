---
name: make-evidence-based-technical-case
description: Build, edit, or review technical proposals, documentation, interface text, code comments, issue comments, plans, pull request summaries, review notes, decision records, mentor guidance, and status reports. Use Toulmin argument structure, ASD-STE100-aligned Simplified Technical English, direct editorial cadence, and non-promotional language. Apply when an agent must make a case, explain why evidence supports a claim, challenge a recommendation, communicate risk, or remove formulaic AI wording from technical prose.
---

# Make an Evidence-Based Technical Case

Use Toulmin reasoning to test the case before you compress it. Use Simplified
Technical English to make the result direct and reviewable.

## Select the communication mode

- Use the **full case** for a proposal, architecture choice, disputed review finding,
  risk decision, or mentor checkpoint.
- Use the **compact case** for a pull request summary, status report, or routine issue
  comment.
- Use the **plain-English translation** when a reader asks what dense technical text
  means.

Read [toulmin-technical-case.md](references/toulmin-technical-case.md) for a full case.
Read [asd-ste100-software.yaml](references/asd-ste100-software.yaml) before drafting any
mode. Read [github-technical-communication.yaml](references/github-technical-communication.yaml)
for GitHub text.

Read [editorial-voice.md](references/editorial-voice.md) before creating or reviewing
documentation, interface text, comments, docstrings, or another reader-facing artifact.
Run `scripts/check_prose.py` before submitting repository prose.

## Ground the case

Inspect the implementation, issue, tests, logs, measurements, and cited decisions.
Separate observations from inferences. Do not invent evidence or treat agent output as
evidence.

Write the core in this order:

1. State the **claim**. Name the decision or observable result.
2. Give the **grounds**. Cite the facts that support the claim.
3. State the **warrant**. Explain why the grounds support the claim.
4. Add **backing** when the warrant depends on a standard, invariant, or established
   project decision.
5. Apply a **qualifier**. Limit the claim to the conditions that the evidence covers.
6. Give the strongest **rebuttal**. State the condition that could weaken or defeat the
   claim.

Ask these questions before recommending action:

- What evidence would prove the claim wrong?
- Which important user, boundary, failure, or regression case is missing?
- Does the warrant depend on an unstated assumption?
- Does the recommendation exceed the evidence boundary?
- Does a human need to decide a product, security, privacy, accessibility, or
  architecture trade-off?

## Use the full case

Use these headings when readers need to inspect or challenge the reasoning:

```markdown
## Claim

<Decision or observable result, with its qualifier.>

## Grounds

<Measured facts, implementation evidence, tests, or cited decisions.>

## Warrant and backing

<Why the grounds support the claim and which invariant, standard, or decision supports that reasoning.>

## Limits and rebuttal

<Scope boundary, uncertainty, strongest counterexample, and evidence that would change the decision.>

## Decision or next step

<One accountable action, owner, and checkpoint.>
```

Omit a heading only when the artifact provides the same field elsewhere. Never omit
the reasoning itself because the claim feels obvious.

## Use the compact engineering case

State the failure risk first. State the mechanical action second. State the supported
result third. Add the evidence and uncertainty that matter to the reader.

Use one or two sentences for a routine summary:

```text
<Risk or conflict>. <Mechanical action>, so <supported state at the named boundary>.
Evidence: <test, file, measurement, or reproducible behavior>. Limit: <remaining uncertainty>.
```

This sequence is a compact presentation, not a replacement for Toulmin reasoning:

- the supported state is the claim.
- the observed failure and cited evidence are grounds.
- the mechanism that connects the action to the state is the warrant.
- tests, standards, and project invariants provide backing.
- the named boundary is the qualifier.
- the remaining uncertainty is the rebuttal.

## Explain a code change

Follow the repository
[`Code Change Standard`](../../../docs/CODE_CHANGE_STANDARD.md) for a pull request or
decision record. State why the selected mechanism supports the claim. Compare it fairly
with the closest credible alternative.

State why the alternative loses under the named conditions. Name the trade-off that the
selected design accepts and the evidence that should reopen the choice.

Explain module ownership, contract effects, failure signals, recovery, and complexity.
Use names, types, interfaces, and tests for ordinary behavior. Reserve comments for
non-obvious reasons, invariants, policy constraints, and failure behavior.

## Translate dense technical text

Use exactly these sections when a reader requests a translation:

```markdown
## Part 1: Plain-English Translation

<One or two direct sentences that state the mechanism.>

## Part 2: Key Concepts Explained

- **Term:** <Plain definition and effect in this system.>
```

Preserve state ownership, operation order, atomic boundaries, locks, transactions,
timeouts, retries, resource limits, and failure behavior. Do not call a lock a
transaction. Do not call a transaction a lock.

## Apply the language rules

- Use American English.
- Prefer active voice and subject-verb-object sentences.
- Use 25 words or fewer in descriptive sentences.
- Use 20 words or fewer in procedural sentences.
- Put one instruction in each procedural sentence.
- Do not use contractions or semicolons in prose.
- Define a specialized term at its first important use.
- Use one stable term for one concept.
- Replace vague praise with a mechanism, condition, and effect.
- Preserve code identifiers, commands, protocol names, version identifiers, quoted
  interface text, and citations.

## Use direct editorial cadence

Lead with the subject, mechanism, decision, or instruction. Follow it with evidence,
conditions, or consequences. Remove introductory throat-clearing and empty transitions.

Vary sentence length only to support comprehension. Use a short sentence for an
important contract. Use a longer sentence for a necessary condition or consequence.
Do not use fragments or repeated three-part lists only to create rhythm.

Write with authority only when evidence supports the claim. Do not use promotion,
false urgency, generic inspiration, or formulaic AI transitions as substitutes for
reasoning.

## Keep one editorial present

Describe the complete system contract. Do not narrate the prompt, author process,
editing sequence, or the time when explanatory content entered the repository.

Put completed history in a changelog. Put capability state in a status document. Put
planned sequence in a roadmap. Put version transitions in migration or compatibility
notes.

Preserve time words when they describe runtime order, dated evidence, or an actual
project state.

Do not claim formal ASD-STE100 compliance. A qualified human must review the controlled
dictionary, approved technical terms, and intended meanings.

## Review the result

Confirm that:

- every claim has grounds.
- every recommendation has a visible warrant.
- the qualifier matches the evidence boundary.
- the strongest relevant rebuttal receives a fair answer.
- facts and inferences remain distinct.
- a reviewer can reproduce or inspect the cited evidence.
- the wording follows the language rules without removing technical meaning.
- the cadence emphasizes mechanisms and evidence instead of performance.
- no phrase exposes prompt history, editing history, or formulaic AI narration.
- the next human decision is explicit.

The checker enforces sentence and paragraph limits in Markdown. It rejects contractions,
semicolons, vague promotional terms, process narration, and high-signal AI clichés.

Automation cannot judge active voice, approved word meaning, stable terminology,
cadence, Toulmin completeness, technical accuracy, or rhetorical fairness. A human
reviewer must assess those properties.
