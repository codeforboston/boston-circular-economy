# Editorial Voice, Cadence, and Rhetoric

Use this reference for documentation, interface text, comments, docstrings, reviews,
and technical explanations.

## Write the artifact, not the drafting story

Describe the system as one coherent artifact. State its behavior, interfaces,
constraints, evidence, and failure modes.

Remove these forms of process narration:

- references to what the prompt or requester asked for.
- reports that an author added, changed, moved, or improved content.
- labels such as “new,” “updated,” or “latest” without a dated baseline.
- placement phrases such as “as described above” or “in the following section.”
- discovery narratives that do not affect operation, migration, or compatibility.

Use sequence words for actual order. Runtime transitions, procedures, dependencies,
migrations, and evaluation methods have meaningful order.

## Control cadence

Start a paragraph with its claim, mechanism, or topic. Put supporting facts and limits
next. End when the topic is complete.

Use a short sentence for an invariant, prohibition, or decision. Use a longer sentence
only when a condition or consequence must remain attached. Stay within the language
profile limits.

Avoid artificial rhythm:

- repeated sentence openings.
- several fragments used as dramatic beats.
- repeated sets of three that add no technical structure.
- one-sentence paragraphs that repeat the prior point.
- rhetorical questions when a direct statement is clearer.
- repeated “Moreover,” “Furthermore,” or “Additionally” transitions.

Lists must expose real structure. Do not turn ordinary prose into a list only to make
it appear complete.

## Use evidence-based rhetoric

Lead with a concrete subject and verb. Name the affected user, component, operation,
condition, and result when they matter.

State confidence through a precise qualifier. Do not use confident tone to hide weak
grounds. Present the strongest relevant rebuttal instead of an implausible alternative.

Avoid these substitutions for reasoning:

- promotion instead of measured behavior.
- urgency instead of a dated constraint or observed failure.
- authority language instead of a cited standard or decision.
- broad benefits instead of a named user and outcome.
- claims of simplicity without the operation and boundary.
- claims of readiness without the required tests and operating evidence.

## Remove formulaic AI language

Do not use stock openings, inflated transitions, or promotional combinations such as:

- `In today's fast-paced world`.
- `It is important to note`.
- `It is worth noting`.
- `At its core`.
- `In conclusion`.
- `This highlights the importance of`.
- `This underscores the importance of`.
- `a testament to`.
- `ever-evolving landscape`.
- `delve into`.
- `navigate the complexities of`.
- `unlock the potential of`.
- `seamlessly integrates`.
- `robust and scalable`.
- `not only ... but also` when the contrast adds no technical meaning.

Words such as `robust`, `scalable`, `powerful`, and `improved` require a named
property, baseline, workload, and evidence. Replace them with the measured result or
remove them.

## Preserve useful human qualities

Direct language can remain considerate. State the problem without blaming a person.
Explain why a constraint exists. Offer a concrete next action when the reader can
resolve the problem.

Do not erase uncertainty, disagreement, or judgment. Name each one and identify the
person or evidence that can resolve it.
