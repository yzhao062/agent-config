---
name: nsf-bibref-filler
description: Add or tighten bibliography citations in NSF proposal sections such as the intro, summary, team qualification, evaluation, and thrust files. Use when Codex needs to place bibrefs conservatively, prefer existing local cite keys for the team's own work, respect user-specified citation density, verify every inserted citation against local .bib files or primary-source metadata, and leave visible TODOs instead of guessing.
---

# NSF Bibref Filler

## Overview

Use this skill when the prose mostly exists and the job is to add or tighten
bibrefs without inventing anything.

This skill is optimized for NSF proposal sections, but it can also support
other calls when the section purpose and call requirements are explicit. When a
non-NSF call uses different section logic, follow the supplied call context and
section role rather than assuming NSF section semantics.

This skill is for citation filling, not for full section rewrites:

- keep the section's argument intact
- add citations only where they materially support a claim
- default to conservative coverage unless the user asks for denser support

For intro framing, thrust overviews, and motivation or background paragraphs,
do not let the team's own papers become the main support for broad field,
infrastructure, or gap claims. Use external literature, standards, surveys, or
community-system papers as the primary anchors there. Reserve the team's own
papers for prior capability, concrete project outputs, or places where the
proposal explicitly builds on that prior work.

Read `references/citation-rules.md` only when you need section-specific
placement patterns or citation-density guidance.

Use these helpers when needed:

- local bib search: `../nsf-thrust-refiner/scripts/search_local_bib.py`
- cite-key validation after patching: `scripts/check_cite_keys.py`

In a multi-proposal repo, use `<proposal-dir>` to mean one concrete proposal
workspace such as `proposals/nsf-25-533-fairos`.

Use this storage convention for bibliography entries:

- existing human-maintained bibliography stays in the current local `.bib` files
- machine-added entries go into `<proposal-dir>/bibs/working.bib`
- if you are editing the scaffold itself, use `template/bibs/working.bib`

## Workflow

### 1. Calibrate Scope And Density First

Before editing, identify:

- the target section file(s)
- whether the user wants `sparse`, `moderate`, or `heavy` citation density
- whether the user wants local-only citations or allows externally verified
  additions

If the user does not specify density, default to `sparse`: fill only the
claims that most obviously need support.

### 2. Gather Only The Inputs Needed

Read the smallest useful set of files:

- the target `.tex` file(s)
- neighboring sections only when needed for citation style or cite-key reuse
- active bibliography files under `<proposal-dir>/bibs/*.bib`
- `template/bibs/*.bib` and example proposal bibs only when the active bib
  lacks a known exact entry

Do not scan the entire proposal unless the user asks for a broad pass.

### 3. Search Local Bibliography First

Start with local evidence in this order:

1. `<proposal-dir>/bibs/*.bib`
2. citations already used in nearby sections
3. `template/bibs/*.bib`
4. example proposal `.bib` files under `examples/proposals/`

For the team's own work, prefer existing local cite keys. If the prose names
one of the team's papers, systems, or datasets and no exact local entry is
available, do not invent a key. Leave a visible `\todo{Add citation for ...}`
or stop and ask for the missing entry.

Do not move or rewrite human-maintained entries just to normalize them. The
default behavior is to keep existing local bib files intact and add any new
machine-verified entries only to the dedicated `working.bib` file.

This local-first rule is about exact-key reuse, not about preferring
self-citations. If the target paragraph makes a field-wide or community-wide
claim and the local matches are mostly the team's own papers, treat that as
insufficient support and look for externally verified anchors instead.

### 4. Verify Every Candidate Before Inserting It

Insert a cite key only if all of these are true:

- the key exists in a local `.bib`, or you have just added it from an exact
  verified source
- the title and authors match the claim you are supporting
- the venue and year are not materially ambiguous
- the paper actually supports the sentence, not just the general area

Do not use "close enough" matches. A nearby topic match is not enough.

### 5. Use External Search Only When Local Evidence Is Insufficient

When local bibs do not contain the needed reference and the user allows
external additions:

- verify against primary or canonical sources first: DOI or publisher page,
  official arXiv page, DBLP, OpenReview, ACL Anthology, IEEE, ACM, Springer,
  Nature, or equivalent venue sources
- cross-check title, author list, venue, year, and DOI or canonical URL
- add the BibTeX entry to the dedicated active machine-managed bib file before
  citing it in prose

If any key metadata remains uncertain, do not add the entry. Leave a visible
TODO instead.

### 6. Place Citations Conservatively

Follow `references/citation-rules.md` for section-specific placement.

Default rules:

- cite non-obvious technical or empirical claims
- cite the team's own concrete prior outputs when claiming prior capability
- prefer one strong citation cluster over many weak ones
- avoid turning every sentence into a citation dump
- keep project summary citations especially sparse unless the user explicitly
  wants more
- for intro framing and thrust motivation or overview paragraphs, prefer
  externally verified anchors over self-citation-heavy clusters

### 7. Validate Cite Keys After Patching

After editing:

- run `scripts/check_cite_keys.py` on the touched `.tex` files
- fix any unresolved keys before finishing
- if the edit added new external entries, confirm they were added to the
  intended `working.bib` file and that the target `.tex` includes it in the
  bibliography list

If the section is compile-sensitive or the user asks for it, also recompile
the relevant LaTeX target.

### 8. Leave Visible TODOs For Anything Uncertain

Use visible `\todo{...}` for:

- missing exact cite keys
- external papers whose metadata is not yet confirmed
- claims that need a source but have only a vague candidate
- places where the user requested higher citation density but the available
  evidence is not strong enough

Never hide uncertainty in comments and never silently insert fabricated
bibrefs.

## Output Style

When using this skill, prefer one of these outcomes:

- a patch that adds verified citations only
- a patch plus 1-2 visible TODOs where accuracy blocked insertion
- a citation audit summary before patching when the user asks for planning
  first
