<!-- Round 1 -->

# Skill consistency review — `editable-figure`

## Verification notes

Reads completed (full file contents): `editable-figure/SKILL.md`, `references/default-palette.md`, `references/default-palette.json`, `references/mechanism-figures.md`, `references/native-powerpoint.md`, `references/document-contexts.md`, `references/reference-search.md`, `references/panels-and-results.md`, `references/iteration-example.md`, `agents/openai.yaml`, `scripts/render_powerpoint.ps1` (read-only; PowerPoint not launched), plus `review-round1.md` and `round1-hashes.json`.

Commands run (read-only, in the snapshot directory):
1. `find . -type f` + per-file `wc -c` — 11 skill files, no strays.
2. One Python script (`py312`) that: parsed `default-palette.json`; diffed its token set against every backticked token in `default-palette.md`; resolved every non-HTTP Markdown link in `editable-figure/**/*.md` against the filesystem; computed WCAG relative-luminance contrast for the palette; and extracted/compared SKILL frontmatter `name` against the directory name and measured `description` length.
3. `grep -rn` for `categoricalOrder|BFDFD2|C2DFD1|3:1|otherObjects|Artifact Tool` to locate duplicated constants.

Results: JSON parses; token set matches the `default-palette.md` role table **exactly** (0 orphans either direction); all 4 `categoricalOrder` entries resolve to real tokens; **0 broken relative links**; frontmatter `name: editable-figure` matches the directory, `description` is 440 chars. Contrast: `ink`/white 14.97, `mutedText`/white 4.84, `mintStroke` 7.36, `coralStroke` 4.45, `ink` on `mint` 10.48, `ink` on `coral` 6.10 — all usable; `mint` vs `coral` is only 1.72, which `default-palette.md:22` already warns about explicitly, so it is not a finding. `render_powerpoint.ps1` matches its documented contract at `native-powerpoint.md:63-74`: absolute-path enforcement (`:11-19`), refuses pre-existing outputs (`:28-31`), opens read-only (`:66`), single-slide guard (`:67`), input SHA-256 re-check after export (`:79`), non-empty export check (`:80-83`), and quits PowerPoint only if it started it (`:107`). Paper/arXiv facts treated as inherited evidence per the prompt; no web access used.

**Verification status: VERIFIED**

## New findings

**Medium — `categoricalOrder` conflicts with the stated mint/coral default.** `default-palette.json:16` exposes `["mint","teal","gold","coral"]`, but `SKILL.md:64` and `default-palette.md:14` both say mint/coral is the *main contrast* and teal/gold are only for additional categories. `default-palette.md:20` scopes the array to "a four-series plot," but the JSON — which `default-palette.md:5` tells agents to "use directly in a builder" — carries no arity note. A builder that slices `categoricalOrder[:2]` for a two-series comparison emits mint/teal, silently breaking the default visual identity and the cross-panel color-to-meaning mapping required at `SKILL.md:66`. *Fix:* rename to `categoricalOrder4` or add a sibling `"pairOrder": ["mint","coral"]`, and add one clause at `default-palette.md:20` stating that two- and three-series work uses mint/coral(/gray), not a prefix of `categoricalOrder`.

**Medium — the Codex entry point hardcodes PPTX, dropping the format guard.** `agents/openai.yaml:4` ends "…and deliver an editable PPTX with an appropriate preview or publication export," with no counterpart to `SKILL.md:23` ("Do not replace an explicitly requested SVG, Illustrator document, or screenshot with PPTX") or `SKILL.md:12` (assessment/prompt-only requests need no deck). This is exactly the failure the user called out, on the surface that seeds the Codex-side prompt. *Fix:* append "…unless another output format or a non-deck deliverable was requested" to the `default_prompt`.

**Low — `native-powerpoint.md:15,33` keys guidance to an unidentifiable "Artifact Tool."** A cold reader cannot map `nativeChartTargetApplication` or `materializeLiteralChartWorkbooks` to any runtime they have, and naming one unnamed plugin's options mildly cuts against the model/runtime-agnostic goal. The generic table at `:19-25` is fine. *Fix:* one clause at `:15` identifying it as "one deck-authoring runtime observed in Sept 2026," or drop the two option names at `:33` and keep the behavioral lesson.

**Low — helper inventory field undocumented.** `render_powerpoint.ps1:37,56` emits `otherObjects` (placeholders, tables, SmartArt), but `native-powerpoint.md:74` enumerates only shapes/text/connectors/charts/groups/pictures. A nonzero value looks like an error. *Fix:* add `otherObjects` to that sentence.

**Low — which mint for a *new* CatchBench figure is ambiguous.** `default-palette.md:30` says preserve `#C2DFD1`/`#ED986C` "when extending or editing that accepted figure series" and never mix variants; `SKILL.md:64` says use canonical `#BFDFD2`/`#ED8D5A` for new figures while `:66` gives an "established document palette" priority. A third CatchBench figure is reachable by both rules. *Fix:* at `default-palette.md:30`, say the paper's existing variant governs all figures in that document.

**Low — `iteration-example.md` is linked only from §6.** `SKILL.md:137` sits in "Deliver for the destination," but the content is design-phase (§3). Reachable via `panels-and-results.md:57`, so cosmetic. *Fix:* also cite it near `SKILL.md:80`.

**Optional (over-engineering).** `native-powerpoint.md:37-49` (float reserialization, `TextFrame2.WordWrap`, `PlotArea.InsideLeft`) is the most version-fragile content and the least tied to the skill's editorial purpose; consider trimming. The 3:1 ratio now appears at `SKILL.md:90`, `panels-and-results.md:15`, and as `3.03:1` at `iteration-example.md:23` — the likeliest number to drift; keeping the normative statement only in `panels-and-results.md` would help. Both are preferences, not required fixes.

## Previously raised

None. `review-round1.md` in this snapshot is the dispatch prompt, not a prior review; no earlier round exists to reconcile.

## Verdict

Internally sound and appropriately scoped to the requested additions. Links, JSON tokens, frontmatter, and the helper's documented contract all check out, and every case measurement (canvas sizes, word counts, 7.16/7.62 pt, gutters) is explicitly dated and hedged as an observation rather than a target — the main risk the user flagged is handled. No High findings. The two Medium items are narrow, one-line wording/schema fixes; the rest are polish.
