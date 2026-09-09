<!-- Round 2 -->

# Skill consistency review — `editable-figure` (Round 2)

## Verification notes

Full reads: `editable-figure/SKILL.md`, `agents/openai.yaml`, `references/default-palette.{md,json}`, `document-contexts.md`, `iteration-example.md`, `mechanism-figures.md`, `native-powerpoint.md`, `panels-and-results.md`, `reference-search.md`, `scripts/render_powerpoint.ps1` (read-only; PowerPoint never launched, helper never executed), plus `review-round1-output.md`, `review-round2.md`, `round2-hashes.json`.

Read-only checks (one Python script under `py312`, one `grep -rn`, confined to this directory):
1. **Hashes:** recomputed SHA-256 for all 11 listed paths — **11/11 match**, and exactly 11 files exist under `editable-figure/` (no strays, no unlisted file).
2. **Links:** every non-HTTP Markdown link in `editable-figure/**/*.md` resolved against the filesystem — **0 broken**.
3. **Presets:** JSON parses; `pairOrder` `["mint","coral"]` and `categoricalOrder` `["mint","teal","gold","coral"]` both resolve entirely to declared tokens; token set and the `default-palette.md:9-18` role table match exactly in both directions (0 orphans).
4. **Frontmatter:** keys are `name`/`description` only; `name: editable-figure` matches the directory; description 440 chars.
5. **Helper contract:** the 7 inventory keys emitted at `render_powerpoint.ps1:37` (`groups, nativeShapes, textObjects, connectors, charts, pictures, otherObjects`) are now all enumerated at `native-powerpoint.md:74`.
6. **Constants grep** for `3:1|3.03|pairOrder|categoricalOrder|otherObjects|Artifact Tool|BFDFD2|C2DFD1|ED8D5A|ED986C|compile`.
7. **Arithmetic of the case measurements** (not required, but the drift risk flagged in Round 1): 1180 + 389 + 91 = 1660 in a 1664 canvas, and 1180 + 389 + 27 = 1596 in the prior 1600 canvas — the +64 widening equals the gutter delta exactly; 1180/389 = 3.03; 340/820 = 41%; 110/600 = 18%. All internally consistent.

Paper/arXiv statements and historical build observations treated as inherited evidence; no web access, no PowerPoint, no Git.

**Verification status: VERIFIED**

## Previously raised findings

| Round 1 finding | Status |
|---|---|
| Medium — `categoricalOrder` conflicts with mint/coral default | **Resolved.** `default-palette.json:16` adds `pairOrder`; `default-palette.md:20` forbids truncating the four-series preset, routes three-series to mint/coral + role-chosen third, and gives existing identities priority over either preset. Gray is not mandated. |
| Medium — Codex entry point hardcodes PPTX | **Resolved.** `agents/openai.yaml:4` now ends "unless another output format or an assessment or prompt-only deliverable was requested," matching `SKILL.md:12,23`. |
| Low — unidentifiable "Artifact Tool" | **Resolved.** `native-powerpoint.md:15` names it as one September 2026 observed authoring runtime, "not a required dependency," with a version-recheck guard; `:33,47` say "observed." |
| Low — `otherObjects` undocumented | **Resolved.** `native-powerpoint.md:74`, including "a nonzero `otherObjects` count is not itself an error." Script unchanged, as stated. |
| Low — which mint for a *new* CatchBench figure | **Resolved.** `default-palette.md:30`: those exact fills "govern both revisions and new figures in that document." |
| Low — `iteration-example.md` linked only from §6 | **Resolved.** Now cited at `SKILL.md:86` in §3; general graphics/text guidance sits at `:62`, outside the palette subsection. |
| Optional — 3:1 duplication | **Resolved as scoped.** Removed from `SKILL.md:92`; conditional starting point kept at `panels-and-results.md:15`; observed `3.03:1` at `iteration-example.md:23`. |
| Optional — version-fragile API content | Not adopted; accepted rationale recorded. Not reopened. |

Coordinator fixes 8 and 9 verified present: `SKILL.md:80` ↔ `native-powerpoint.md:59` now agree on the fixed-width condition, and `SKILL.md:137` scopes the canonical float fragment to LaTeX and says "render or compile."

## New findings

**Low — `SKILL.md:80` omits the scale half of the fix-8 condition.** It says "If the width changes too, recalculate printed text size," while `native-powerpoint.md:59` says "If the width or object scale changes." An agent that keeps the canvas width but rescales retained artwork reads `SKILL.md` as licence to skip recalculation. *Fix:* change to "If the width or object scale changes, recalculate printed text size."

**Low — `mechanism-figures.md:45` keeps LaTeX-only vocabulary in generic guidance.** "Update the caption's canonical fragment and all figure exports, compile, and inspect the actual page" is normative for a file that explicitly covers proposals (`:11`) and READMEs (`:11,35`), where there is no fragment and nothing to compile — the residue fix 9 removed from `SKILL.md:137`. *Fix:* "update the caption in its canonical place and all figure exports, then render or compile the document and inspect the actual page."

**Low — `categoricalOrder` still carries no arity signal inside the JSON.** `default-palette.md:5` tells agents to use the JSON directly in a builder; a builder reading only the JSON can still slice `categoricalOrder[:3]` and emit mint/teal/gold, dropping the coral focal role. The prose ban at `:20` covers the documented path, so this is residual, not a reopening. *Fix (optional):* rename the key to `categoricalOrder4` and update the two `default-palette.md:20` mentions.

## Verdict

All nine reconciliation items are present in the files as described, and the artifact matches `round2-hashes.json` byte-for-byte. Routing, frontmatter, cross-file instructions, preset semantics, the invocation contract, and the helper's documented inventory are mutually consistent; no contradiction rises above Low and no regression was introduced. The three items above are one-line wording changes and do not warrant another review round.
