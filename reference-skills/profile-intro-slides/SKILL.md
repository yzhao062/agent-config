---
name: profile-intro-slides
description: Generate a reusable 2-3 slide Yue Zhao / FORTIS Lab intro insert from local website-first sources in this repo. Use when the user wants a stable identity, agenda, and representative-systems module that can be merged into other decks. Do not use this skill for full paper talks, mini-CV decks, or automatic deck insertion.
---

# Profile Intro Slides

Read [references/source-selection.md](./references/source-selection.md) first.
Read [references/slide-recipes.md](./references/slide-recipes.md) before writing any frames.
Read [references/quality-checks.md](./references/quality-checks.md) before finalizing any draft.

This skill generates a small reusable slide family about Yue Zhao and FORTIS Lab. It is for a stable intro insert, not for a full opening sequence, not for a recruiting deck, not for a mini CV, and not for inserting slides into another talk automatically.

## Workspace Contract

This skill is repo-specific. Treat these paths as relative to the workspace root:

- `README.md`
- `theme/`
- `templates/`
- `yzhao062.github.io/`

Before generating anything, verify that the workspace contains at least:

- `README.md`
- `templates/demo.tex`
- `templates/paper-deck-base.tex`
- `theme/beamerthemeuscmoloch.sty`
- `yzhao062.github.io/index.html`
- `yzhao062.github.io/lab.html`
- `yzhao062.github.io/files/bio.txt`
- `yzhao062.github.io/data/open-source.json`
- `yzhao062.github.io/data/publications.json`

Useful optional sources:

- `yzhao062.github.io/data/lab-current-phd.json`
- `yzhao062.github.io/data/lab-members.json`
- `yzhao062.github.io/files/ZHAO_YUE_CV.pdf`
- `yzhao062.github.io/images/rsz_250.jpg`
- `yzhao062.github.io/images/lab-logo.png`

If the contract is not satisfied, stop and ask the user instead of improvising a different source stack.

## Default Outputs

Generate these artifacts by default:

- `templates/modules/yzhao-intro-slides.tex`
- `templates/modules/yzhao-intro-facts.md`

`yzhao-intro-slides.tex` should contain reusable frame blocks only. Do not include a document preamble, title page, section pages, bibliography appendix, or `\input{...}` edits to another deck.

`yzhao-intro-facts.md` should be the canonical fact sheet that records the stable positioning, representative systems, chosen impact signals, and the source file for each nontrivial claim or number.

Only create a standalone preview deck or compile output if the user explicitly asks for a preview.

## Workflow

1. Verify the workspace contract and read the source-selection reference.
2. Extract stable facts from website-first sources. Use the CV only to fill gaps such as awards, service, or older chronology.
3. Separate evergreen content from volatile content. Unless the user asks otherwise, omit recruiting details, news, collaboration logistics, live policy notices, and other time-sensitive site blocks.
4. Build or refresh `templates/modules/yzhao-intro-facts.md` first. Record:
   - identity and affiliation
   - one-line FORTIS expansion and mission
   - the three main research directions
   - 3-5 representative systems, projects, or agenda-anchor papers
   - a small set of durable impact signals
   - any selected sponsor or research-support logos that may appear in a secondary acknowledgment strip
   - the preferred portrait and lab logo assets
   - source path for each nontrivial claim or number
5. Choose the slide family. Default to exactly three slides with fixed role separation:
   - `About Yue Zhao`
   - `FORTIS Lab Research Agenda`
   - `Representative Systems and Impact`
6. Before drafting, assign each slide:
   - exactly one role
   - exactly one dominant mode: `text-first`, `visual-first`, or `compact card grid`
   - exactly one primary object of attention
7. Write `templates/modules/yzhao-intro-slides.tex` as reusable frame blocks only.
   - Keep the canonical role split:
     - `About Yue Zhao`: identity and positioning
     - `FORTIS Lab Research Agenda`: agenda map
     - `Representative Systems and Impact`: execution evidence
   - Do not let one slide do two or three jobs at once.
8. Run the checks in `references/quality-checks.md` before preview generation or handoff.
   - If any density or role check fails, revise before finalizing.
   - Apply slide surgery in the low-risk order defined there before attempting a larger redesign.
9. Keep the slides mergeable into arbitrary decks: no talk-specific transitions, no venue-specific filler, and no dependency on surrounding slide numbers, sections, or presenter notes.
10. If the user wants a variant emphasis, keep the canonical core and vary only one axis at a time: auditing and assurance, agent safety and security, anomaly-detection roots, or lab-intro flavor.
11. If the website and CV disagree, prefer the more recent website wording unless the CV clearly contains the only reliable version. Note the conflict in the fact sheet.

## Operating Rules

- Treat the website as the primary source of current positioning.
- Prefer stable positioning over exhaustive biography.
- Keep the module a reusable insert, not a mini-talk.
- Distinguish personal identity, agenda mapping, and execution evidence; do not collapse them into one overloaded frame by default.
- Keep the default family to exactly `3` slides unless the user explicitly asks for a shorter variant.
- Each slide must have exactly one main job, one dominant mode, and one primary object of attention.
- Prefer not to put paper-count, download, or GitHub-star callouts on the personal identity slide unless the user explicitly asks for a metrics-forward version.
- Prefer one memorable phrase and three strong pillars over long bullet lists.
- Prefer `3-4` representative systems on a systems slide. Do not try to summarize every project.
- On the `FORTIS Lab Research Agenda` slide, prefer mixed examples under each pillar: named systems when tooling is the clearest anchor, and representative papers when they better communicate the current research direction.
- When a systems slide is likely to be shared as PDF, prefer clickable project names or project-title links that can route viewers to the corresponding site or repo.
- For open-source projects, default those links to the GitHub repository itself unless the user explicitly prefers docs or a project site.
- If project names are clickable, prefer subtle visible styling such as underlining rather than noisy explicit `[link]` labels.
- Keep Slide 1 qualitative and slide-native: one positioning sentence max, three short bullets max, no biography prose, no metrics strip.
- If Slide 1 reads cleaner with labeled signal lines than with plain bullets, prefer short labels such as lab, team, and style.
- If Slide 1 needs a lab-scale signal, prefer the stable current/incoming PhD count and describe the broader master's or undergraduate team qualitatively rather than fixing a volatile total.
- Team-scale wording on Slide 1 should read as appreciation and research capacity, not as a roster dump or recruiting pitch.
- Keep Slide 2 as a clean pillar map: one short mission line at top, three equal pillars, one short description line plus one compact examples line per pillar.
- If Slide 2 feels visually underused, prefer a subtle relation visual such as `Observe -> Control -> Deploy` across the three pillars before adding more prose.
- Keep Slide 3 as a compact project-card slide by default: `3-4` anchors, one-line payoffs, and only an optional small dated impact strip if it helps.
- If sponsor acknowledgment is desired, keep it as a thin secondary support strip on the systems slide rather than a separate sponsor slide or sponsor wall.
- If both metrics and sponsor logos are present on Slide 3, keep the project cards primary, the metrics strip secondary, and the sponsor strip quieter still.
- Never put both a long takeaway paragraph and a metrics strip on the systems slide.
- Treat volatile metrics as optional, dated, and visually subordinate. If they add clutter, remove them.
- Avoid full publication lists, full awards lists, full student rosters, or sponsor walls unless the user asks for them.
- Keep visible slide text concise, broad-CS readable, and slide-native rather than webpage-like.
- If you include numbers that can drift, record the exact source and date in `yzhao-intro-facts.md`. Use an absolute date in visible text only when the date matters for interpretation.
- Preserve USC styling by generating content-only frame blocks. If a preview deck is requested, inherit styling from `templates/paper-deck-base.tex` or `templates/demo.tex` instead of editing `theme/*.sty`.
- This skill generates reusable intro modules only. It does not insert them into existing decks, update presenter maps, or reorganize another talk around them.
