Review only the changes introduced by this branch.

Apply the root and nearest `AGENTS.md` files. Apply
`.agents/skills/review-code-change/SKILL.md` and `docs/CODE_CHANGE_STANDARD.md`.

Compare the implementation with the stated claim, scope, evidence, and qualifier when
that submission record is available. Trace ownership, contracts, failure signals,
recovery, and test evidence. Focus on discrete defects introduced by the change. Leave
formatting, lint, and other exact checks to CI.

Return at most five high-confidence findings in priority order. Each finding must name
a realistic condition, observable effect, causal mechanism, shortest useful code
location, evidence boundary, and smallest supported correction. Return no finding when
the evidence does not support one. Do not edit files, approve the change, or merge it.
