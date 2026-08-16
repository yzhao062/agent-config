# Invisible-Character Detection: Research Findings

**Status:** research complete, no implementation, no repo file changed. Awaiting three maintainer decisions (§9).
**Scope:** `agent-config` (ac), `anywhere-agents` (aa), `agent-style` (as).
**Date:** 2026-08-15.

---

## 1. What Was Asked

The maintainer proposed adding invisible-character detection to the writing stack. The reasoning: the prose polish pass already rewrites the file, so stripping stray Unicode in that same pass costs almost nothing. Two motivations were offered at the start:

1. Hygiene. Invisible characters survive copy-paste into LaTeX, Word, and git diffs, where they are hard to see.
2. An unenforced rule. Shared `AGENTS.md:237` says "Do not use Unicode character `U+202F`" and nothing checks it. A grep of `scripts/guard.py` for `202F`, zero-width, invisible, NFKC, or `unicodedata` returns nothing.

A third motivation surfaced in conversation: that stripping such characters would also remove vendor watermarks. That claim was sent to the research explicitly flagged as ungraded, and §4 records what it turned out to be.

Two scoping decisions were taken by the maintainer during the research and are treated here as settled:

- **No silent rewrite of a pending write.** `hookSpecificOutput.updatedInput` exists and works (§7), but mutating content an agent already produced is a behavior change the maintainer declined.
- **General English is the target register.** This matches what `agent-style` already declares. Its README says "A curated set of English writing rules," and its own applicability table lists "Non-English prose" as out of scope.

## 2. How the Research Ran

Ten units across two vendors, cross-checked rather than merged. Five Codex units ran through `prun` in read-only scratch directories. Six Claude agents ran through one `Workflow` script: three panel agents, two adversarial skeptics, one reconciler.

Three questions were asked on both sides, because being wrong on them is expensive. A false-positive character policy ships breakage to a public package. An overstated evidence claim would repeat a mistake already made three times this month. A wrong architecture call forces migration through two package ecosystems. Prior art and hook mechanics ran on one side only, being lookups with checkable answers.

The value of the cross-check showed up immediately. Codex scanned the four source repos as instructed and found nothing. Claude widened the corpus without being asked and found the one case that breaks the obvious rule (§5).

## 3. Headline

The character policy is sound and survives review. The watermark motivation is refuted by a vendor statement and cannot appear in shipped copy. The write-time hook gate lost its evidence base: both Claude skeptics refuted their own panel's recommendation on the same mechanism, and Codex rejected the same option for an unrelated reason. That outcome contradicts a decision the maintainer had already taken, which is why §9 asks rather than proceeds.

## 4. The Watermark Motivation Is Closed

Anthropic published a text-watermark explainer on 2026-08-14, verified here by direct fetch. Its wording on mechanism: **"Nothing is added to the text and there are no hidden characters."** What it describes is keyed token choice, the same family as SynthID-Text. On removal it says: "Light editing probably won't remove the watermark completely; a complete rewrite where every word is replaced will."

| Claim | Grade | Basis |
|---|---|---|
| Any major vendor embeds invisible Unicode as a watermark | REFUTED | Every documented program operates on token selection |
| Anthropic watermarks Claude output as of August 2026 | CONFIRMED | Vendor explainer, 2026-08-14; EU AI Act Art. 50(2) effective 2026-08-02 |
| Anthropic's watermark uses hidden characters | REFUTED | Vendor verbatim, quoted above |
| SynthID-Text is sampling-only | CONFIRMED | Nature 634:818-823, "modifies only the sampling procedure" |
| OpenAI built a ~99.9% watermark and withheld it | REPORTED | WSJ 2024-08-04, internal documents and unnamed sources |
| ChatGPT emits U+202F where an ordinary space belongs | CONFIRMED | RumiDocs 2025-04-20 (o3, o4-mini); OpenAI forum #1362321, 2025-10-13 (GPT-5) |
| The U+202F characters are a deliberate watermark | REFUTED | Vendor denial; no key, no detector, no decoded payload |
| French typography in the training corpus is the cause | SPECULATION | Both available attributions point at the RL stage instead |
| U+202F still reproduces today | SPECULATION | No report later than October 2025; untested here |
| Stripping invisible characters removes a vendor watermark | REFUTED | Both shipped schemes live in token choice |
| `agent-config` carries a U+202F rule with nothing enforcing it | CONFIRMED | `AGENTS.md:237`, `CLAUDE.md:222`, `agents/codex.md:253`; grep returns nothing |
| Invisible characters break LaTeX, Word, and diffs | SPECULATION | Rendering breakage confirmed for macOS apps only; the rest is uncited |

**The watermark framing must not appear in shipped copy in any form.** Not as motivation, not as a benefit, not as a hedged aside. It is factually wrong, and the feature cannot deliver it. Shipping an invisible-character stripper into Claude Code hook plumbing weeks after EU AI Act Article 50 took effect also invites a reading as evasion tooling.

Approved copy, with the uncited LaTeX and Word assertion already softened:

```
The best-documented case of stray Unicode in model output is the narrow no-break space (U+202F); ChatGPT has emitted it in place of an ordinary space across several model generations, and users report broken text rendering as a result. Characters like this survive copy-paste into LaTeX sources, Word documents, and git diffs, where they are hard to see and awkward to track down. `agent-config` already tells agents not to use `U+202F` and ships nothing that checks it, so this change gives a standing rule a checker and runs it in the pass that reads the prose anyway. The motivation is hygiene alone: the text watermarks vendors actually ship live in token choice, so normalizing characters neither removes them nor aims to.
```

## 5. What the Corpus Actually Contains

Four scans. Files deduplicated by SHA-256 of raw bytes, because ac and aa are parity mirrors and would otherwise double-count.

| Scan | Scope | Files | Size | Result |
|---|---|---|---|---|
| A | Four source repos, `.md`/`.tex`/`.rst` | 422 unique | 3.7 MB | **0 violations** |
| B | Rest of `PycharmProjects`, same extensions | 3,853 | 45.3 MB | 109 flags, 1 load-bearing false positive (0.92%) |
| C | Same tree with `.txt` added | 9,802 | 12.5 GB | ~84,500 hits, over 99.9% in machine-ingested data |
| D | Synthetic fixture, 45 cases | n/a | n/a | 43/43 classification, 2/2 suppression, 0 FP, 0 FN |

Scan A was reproduced by three independent implementations: Codex P1, the Claude policy agent, and a coordinator script written to omit code-fence masking so that it would report strictly more. All three agree. The only candidate occurrences are eight `U+FE0F` in four copies of `skills/readme-polish/references/patterns.md`, at lines 98 and 100. Each sits on an emoji base inside a fenced block, so the policy suppresses it twice over.

**Every hit in scan B arrived by ingestion.** None came from a model's own token stream. One hundred no-break spaces sit inside OpenAlex paper titles pasted into Markdown audit tables. Sixty-seven zero-width spaces and fifty narrow no-break spaces sit in `pdftotext` output of NSF solicitations. Five `U+FE01` follow `U+2211` in PDF extractions of KDD papers. In 45 MB, exactly one occurrence is a candidate for model authorship, and the panel could not separate LLM drafting from Word autoformatting on it.

### The Single False Positive Is the Most Useful Result

`NSF-Proposal-Template-Yue/examples/proposals/CPS_CIR_2025_Foodbank/02 - project summary.tex:37` carries `U+202F` inside an `\includegraphics` path. The PNG on disk really is named `Screenshot 2025-09-04 at 9.39.47<U+202F>AM.png`, because macOS names screenshots that way. The obvious fix breaks the reference.

`U+202F` is the one character shared `AGENTS.md` bans by name. Its only authored occurrence in 45 MB is load-bearing. A path-and-URL suppression guard is therefore part of the policy rather than a later refinement. Both skeptics added that the enclosing figure block is commented out, so even this exhibit is inert.

### `.txt` Must Be Excluded

Adding `.txt` raises the corpus to 12.5 GB and the hit count to roughly 84,500: 65,075 no-break spaces, 16,258 zero-width spaces, 2,015 soft hyphens. Over 99.9% sits in SEC EDGAR filings, PDF-to-text caches, and scraped forum corpora, where the characters are evidence of the source and normalizing them corrupts the input. `guard.py`'s `PROSE_EXTENSIONS` includes `.txt`, so this rule must define its own narrower set rather than inherit.

## 6. Why the Write-Time Gate Lost Its Evidence Base

The Claude architecture agent first recommended shipping a `guard.py` gate. Its slogan was that the gate "puts the check where the evidence is." Both skeptics refuted that, independently, on the same mechanism. Codex reached the same rejection by a different route.

1. **The gate cannot see the population.** PreToolUse matches `Write|Edit|MultiEdit`. The measured characters arrived through a PowerShell `pdftotext` pipeline (`NSF-Proposal-Template-Yue/docs/skills-workflow.md:739`) and a bulk `git add` (commit `0e8435d`). A write gate is blind to both.
2. **The deny and advise split was inverted.** The proposal denied the zero-width and bidi class as having no legitimate occurrence and a clean one-character reroute. All 69 measured hits in that class sit in verbatim extraction output, where no reroute exists. Meanwhile `U+202F`, the rule's own motivating character, was assigned to advisory.
3. **The only reachable population should not be changed.** Roughly 70 no-break spaces inside quoted OpenAlex titles, duplicated across seven `*-audit.md` copies. Those are recorded upstream strings in a lookup artifact.
4. **Codex rejected the same option for an unrelated reason.** `guard.py:594-627` treats `agent_style` as an optional import and degrades silently when it is absent. A deny built on that policy would be enforced on some machines and not others, while the hardcoded banned-word list always fires.

Measured true positives for a write-time gate: zero.

## 7. Platform Facts That Hold Regardless of the Choice

Established by live probe on Claude Code 2.1.233 unless noted.

- **PreToolUse can rewrite tool input.** The field is `hookSpecificOutput.updatedInput`, introduced in 2.0.10 (2025-10-08), fixed for combination with `ask` in 2.1.0. It replaces the entire input object. Omitting `permissionDecision` still applies the rewrite and leaves permission handling unchanged. The maintainer has declined this path; the capability and the reason for declining are recorded here so the question does not reopen.
- **On `Edit`, rewrite `new_string` only.** Live probe confirms that `old_string` matching is undisturbed. Preserving `old_string` byte-for-byte also lets an edit match already-tainted text and replace it with clean text.
- **`MultiEdit` is not registered in 2.1.233** and could not be probed. Keeping the existing branch is harmless compatibility support.
- **Concurrent rewriters are non-deterministic.** When several PreToolUse hooks return `updatedInput`, the last to finish wins.
- **Model-side stripping cannot work.** A model emits tokens, not a code-point-indexed buffer. A zero-width character may be its own token, part of a token, or a byte sequence, with no dependable rendered cue. Any cleanup must be deterministic code.
- **`revision-prompt.md:11-16` currently protects hidden characters.** Its byte-for-byte frontmatter preservation invariant would preserve an invisible character sitting there, unless sanitization is explicitly ranked above it.
- **`_content_for_style_check` is wrong for this check.** It collapses each fence and inline-code span to a single space (`guard.py:446-469`). That shifts every subsequent line number and strips exactly where invisible characters hide. The Foodbank case is a filename, and in Markdown a filename lives in backticks.
- **The advisory has no offset channel.** It renders `detail` only (`guard.py:666`). An invisible-character finding without a line and column cannot be acted on.
- **`_ADVISORY_RULE_ATTRS` is all-or-nothing** (`guard.py:589-591`, `:607-627`, pinned by `tests/test_guard.py:833-848`). Adding a seventh name silently disables the entire advisory on any machine running an older `agent-style`. Because ac and aa CI install `agent-style` unpinned (`validate.yml:62`), a guard change could not pass CI until `agent-style` had published.
- **Riding `AGENT_STYLE_HOOK` is a coupling defect.** `aa/docs/faq.md:44` tells users to disable it for meta-discussion writes, which is precisely when someone documents invisible characters.
- **Read-side detection belongs in separate work.** Files pulled in with `@` trigger no hook at all. Grep, shell, WebFetch, and MCP are separate ingestion paths, and `PostToolUse` blocking does not stop Claude from seeing the original output. A partial read-side check would read as protection while leaving the main paths open.

## 8. A 22nd Rule Breaks Mechanically

Both vendors independently reached the same verdict on `RULE-J`, with citations. The failure splits into loud and silent halves, and the silent half is worse.

| Site | Behavior |
|---|---|
| `loader.py:197`, `loader.js:162` | `RULE-[0-9A-I]` stops at I. A `#### RULE-J:` heading never parses, **silently**, and its block is absorbed into RULE-I's source text |
| `primitive.py:191-213`, `primitive.js:12-33` | `_CLASSIFICATION` holds exactly 21 keys; an unknown id returns an empty set and emits no row, **silently** |
| `build-compact.py:56` | `EXPECTED_RULE_COUNT = 21`, enforced at four assertion sites, each exiting 1 |
| `verify-install.sh:265-285` | Count other than 21 exits 1 |
| `bench/rescore.py:33-64` | Literal 21-id list plus a literal 7-id mechanical set; `:141-149` raises on either mismatch |
| `real-agent-smoke.yml` | Six count assertions, running after the immutable publish |
| `test_handshake_parity.py:103-145` | The four handshake copies are compared only to each other |

The scorecard data model itself is not fixed at 21. Both engines iterate whatever the loader returns, and the fixture tests aggregate expected rule objects rather than assert a row count. A 22-row scorecard would work once the loader, generators, scope lists, handshakes, and CI assertions all change together. The cost is that six independent mechanisms encode the number, and two of them fail without an error.

The literal string `21 rules` / `21-row` / `21-rule` appears in **38 tracked files**, including nine source adapter files and their two nine-file package mirrors.

## 9. Options, Costs, and the Three Open Decisions

### Options As Costed

| Option | Shape | Files | Version cost | Verdict |
|---|---|---|---|---|
| A | `guard.py` deny or advisory gate | 13+, byte-identical in ac and aa | aa minor or patch | Evidence base refuted (§6) |
| B | `RULE-J` as a full 22nd rule | ~50-55 in as, plus 2 in aa | as minor | Rejected by both vendors (§8) |
| C | Non-rule hygiene module in `agent-style`, outside the scorecard | ~22-25, one bench replay | as minor with a `normalize` subcommand; patch if audit-only | Agreed home for the shared implementation |
| D2 | Deterministic normalization inside `style-review` post-processing | 6 skill and prompt mirrors, riding C | as minor | Agreed, collapses into C |
| F | Report-only repo lint where the characters actually are | new file per writing repo | none | Claude's revised first slice |

Codex recommends C plus D2 now. Claude, after its skeptics, recommends F first to establish a rate, then C. Both reject A and B.

Only one side raised two further arguments for F. First, it is agent-agnostic, satisfying the repo's own Agent Fungibility principle for free, whereas `guard.py` is Claude Code only by construction. Second, it has zero blast radius on the source repos: no byte-identical parity pair, no package mirror, no bench digest, no consumer prompt bytes.

### Two Workflow Defects to Fix in Any Option

1. `skills/style-review/SKILL.md:22-25` exits when the scorecard total is zero. A file whose only problem is an invisible character never reaches the ask or polish steps. A hygiene scan has to participate in that exit decision.
2. Step 6 writes model output immediately and step 7 re-audits it. Deterministic normalization must run in memory after the host rewrite and before the single write, with step 7 then asserting zero hygiene findings.

### The Strongest Surviving Motivation

Rehberger, February 2026, graded CONFIRMED: invisible Unicode tag characters inside a `SKILL.md` produced hidden-instruction execution in Claude Code, GitHub Copilot, and claude.ai Skills. `agent-config` and `anywhere-agents` distribute skills and packs. Scanning what this project ships carries stronger evidence than the hygiene argument, and no option above covers it as designed. For the maintainer this is a write-side concern, distinct from the read-side scope that §7 puts in separate work.

### Decisions Needed

1. **What does the U+202F rule mean?** "Do not type it" or "do not let it reach a file"? This decides whether copied upstream text counts, and therefore who the feature is for. The rule sits under Writing Defaults, which suggests the first reading. Choosing it removes the 100 citation-title no-break spaces from scope.
2. **Measure first, or build first?** F establishes a rate before anything else ships, and no scan so far measures a rate rather than a stock. This conflicts with the earlier decision that hook and skill coexist, which is why it needs an explicit answer.
3. **Does scope extend to the skill and pack files this project ships?** Independent of the first two, and the place where the evidence is strongest.

Twelve further questions of policy detail sit in the run ledger and do not gate the decisions above. They cover the extension set, the `U+202F` tier, variation-selector data vendoring, leading BOM handling, and `U+2007`. The rest concern the `.tex` no-break-space fix, `Edit` context reconstruction, option C shape, escape-hatch variable naming, and a live retest of `U+202F` before any present-tense copy ships.

## 10. What Was Not Verified

- **No flow rate exists.** Every number is a stock of characters already on disk. Nothing measures how often new ones arrive or through which tool. This gap drives decision 2.
- The 45-case fixture was written by the same panel that wrote the policy, so it validates internal consistency rather than external correctness. Persian, Arabic, Devanagari, Sinhala, and braille coverage is synthetic.
- Whether `U+202F` still reproduces in current models: untested, no report later than October 2025.
- Whether invisible characters break LaTeX, Word, and git diffs: no citation found. Testable in about a minute, and absent from the approved copy above.
- GlassWorm's reported 35,800 installs: second-hand from one research note. Verify before citing anywhere load-bearing.
- The filesystem read cost of building on-disk context inside a PreToolUse hook: not measured.
- Whether the audit-file no-break spaces are a defect worth reporting or a fidelity requirement worth preserving is a judgment call. The policy unit called them true violations because a no-break space defeats title search in a lookup artifact. Both skeptics called them false positives because the strings are recorded upstream data. Both readings are defensible.

## 11. Cross-References

- Run ledger, unit prompts, and all ten raw results: session scratchpad, `scratchpad/invis/`.
- `pack-architecture.md` §"The two axes" and §"Decisions made in plan-review": checked, no conflict with C, D2, or F. A `guard.py` deny would additionally have to satisfy the closed noise-budget and reroute decisions at `:938` and `:951-956`.
- Guard extraction to a pack is deferred to v1.0.0 at `pack-architecture.md:918`, reaffirmed at `:955`. Nothing here moves it.
- `aa#28` remains open and unrelated: cut aa v0.7.13 or de-version the docs that name it.
