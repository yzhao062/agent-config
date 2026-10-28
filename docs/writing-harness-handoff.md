# Writing Handoff: Yue Zhao's Research Voice

Use this handoff to draft or revise English research papers and proposals with agent-style, evidence-calibrated claims, and Yue Zhao's author-voice. Using Yue Zhao's voice is intentional. Do not ask the student to supply personal writing samples or build a different voice profile.

## Load the Sources

Read the project's instructions first. Reuse existing installations of the resources below. Otherwise, retrieve the named files into a project-local reference directory, preserving the author-voice directory structure. Record the version or commit used. Do not install the professor's personal profile or change global agent settings just to complete this writing task.

1. From https://github.com/yzhao062/agent-style, use tag `v0.9.0` as the reference baseline and read `docs/rule-pack-compact.md`, including House Style. Consult `RULES.md` for explanations and examples. An existing project pin takes precedence; report its version.
2. From https://github.com/yzhao062/agent-pack, read `skills/author-voice/SKILL.md`. Retrieve its `references/templates.md`, `references/exemplars.md`, and `scripts/voice_check.py`. Use the project's pinned revision if present; otherwise resolve `main` and record its commit.
3. Apply the defensive-writing and revision rules below alongside those sources. They are part of this handoff and require no separate plugin.

Actually read the source files before drafting. A link or a skill name alone does not load the writing guidance. If a source cannot be retrieved, identify the missing file and ask for that resource. Do not claim that author-voice was applied without reading its exemplars.

## Establish the Writing Task

Use the student's supplied manuscript, notes, results, and verified references as the factual basis. Identify the target file and section, intended reader, main claim, supporting evidence, necessary qualifications, and length or venue constraints. Infer these from the project where possible. Ask only for missing information that prevents accurate writing.

Preserve the source format and citation syntax. Revise the requested section only. Do not invent results, numbers, datasets, citations, priority claims, releases, or future plans. A stylistic example supplies no facts about this project.

## Draft with the Voice

For an abstract, introduction, or conclusion, read the corresponding template and complete exemplar passages before writing. Follow their problem framing, order of ideas, mechanism explanations, and sentence rhythm where the supplied facts support those moves. For other sections, use House Style and the general rules.

Facts and necessary scope come first. House Style controls stylistic choices where it conflicts with generic defaults, subject to the explicit exclusions in author-voice. Do not copy exemplar sentences or force every template move into every draft.

## Control Defensive Writing

State what the evidence supports directly. Remove habitual caveat tails and repeated disclaimers that add no information. Keep a qualification when removing it would change the claim's meaning, scope, or certainty. A statistically inconclusive difference is not evidence of equivalence.

In results prose, explain the pattern with a rounded key magnitude and its material scope. Leave full measurements and intervals in tables when those tables hold them. Do not remove the only record of a result, hide losses, or turn bounded evidence into a general claim. Place general limitations together where the document calls for them.

Answer feedback by rewriting, moving, merging, or cutting the passage it concerns. Add text only for an identifiable missing fact, explanation, or required disclosure. Do not append defenses against imagined objections. Track section length across revisions; growth without new necessary content calls for consolidation.

## Check and Revise

Run the bundled `voice_check.py` on the draft with the appropriate `--section` value, following the skill's instructions. Read each `CHECK` in context, revise where helpful, and rerun after revision. Never add facts, examples, or causal relations to meet a statistical range. Retain a departure when forcing the range would make the writing worse.

If agent-style's CLI is available, run its deterministic review too. Otherwise, manually audit the loaded rules and disclose that the CLI check was not run. Mechanical checks do not verify scientific claims or citations. Separately check factual support, claim strength in both directions, reader comprehension, and revision growth. Review available evidence before accepting a suggested change.

Do not launch additional agents or repeated review loops unless the student requests them. A single writing agent can perform this workflow.

## Deliver

Save the draft in the requested format, with only manuscript text in the manuscript file. In the chat reply, link the result, briefly identify substantive changes, report the final voice-check summary and any retained departures, and name unresolved factual questions. Distinguish checks actually run from checks unavailable. Do not describe a low style-warning count as proof of scientific quality.
