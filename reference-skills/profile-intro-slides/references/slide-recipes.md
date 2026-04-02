# Slide Recipes

These recipes are for a reusable intro insert, not a full talk opening. Preserve the canonical three-slide family and keep each slide responsible for exactly one job.

## Canonical 3-Slide Family

### 1. About Yue Zhao

Role:

- identity and positioning

Default mode:

- `text-first`

Primary object:

- the compact identity-and-positioning block

Goal:

- establish who Yue Zhao is and what the research program is about in one glance

Allowed content:

- name
- title
- affiliation
- one compact positioning sentence
- `2-3` short signal bullets
- an optional short lab-scale signal if it stays scannable
- optional portrait only if it clearly supports the identity read

Hard limits:

- max `1` positioning sentence
- max `3` bullets
- bullets should be short and scannable
- no long biography-style prose
- no metrics strip
- no repeated restatement of the same research scope in multiple bullets

Prefer:

- qualitative framing over quantitative framing
- slide-native phrasing over profile prose
- if signaling lab scale, prefer the stable PhD core count and describe master's or undergraduate participation qualitatively
- short labeled signal lines such as `Lab`, `Team`, and `Style` when they scan better than plain bullets

Avoid:

- full biography paragraphs
- paper-count, download, or GitHub-star callouts by default
- long award or service lists
- time-sensitive recruiting or policy notes

### 2. FORTIS Lab Research Agenda

Role:

- agenda map

Default mode:

- `compact card grid`

Primary object:

- the three-pillar map

Goal:

- show the stable FORTIS Lab agenda in one glance

Required structure:

- one short mission line at the top
- three equal pillars:
  - `AI Auditing and Assurance`
  - `AI Safety and Security`
  - `AI for Science and Society`
- each pillar gets:
  - one short descriptive line
  - one compact examples line

Hard limits:

- do not copy a website-style paragraph into the slide
- do not use more than one short sentence per pillar
- do not let examples dominate the slide
- do not overload the slide with sub-areas

Prefer:

- short labels and grouped phrases over prose blocks
- mixed examples only when they clarify the pillar quickly
- if the slide needs more structure or presence, add one subtle relation visual such as `Observe -> Control -> Deploy` instead of expanding the text

Avoid:

- full student or sponsor information
- explanatory website copy
- long lists of subtopics

### 3. Representative Systems and Impact

Role:

- execution evidence

Default mode:

- `compact card grid`

Primary object:

- the representative project cards

Goal:

- turn the agenda into tangible systems or tools that show execution

Allowed content:

- `3-4` representative systems such as `PyOD`, `Aegis`, `agent-audit`, `TrustLLM`, `PyGOD`, or another current anchor
- one-line payoff per system
- subtle clickable project names when useful in a shared PDF
- optional very small dated impact strip only if it adds real value
- optional thin sponsor-support strip only if it stays clearly secondary

Hard limits:

- do not include both a long takeaway paragraph and a metrics strip
- if an impact strip is kept, it must stay compact and secondary
- if a sponsor strip is also kept, it must be thinner and quieter than the metrics strip
- do not let the slide read like a GitHub profile dump
- do not mix too many unrelated metrics
- prefer one-line project payoffs over multi-line mini-paragraphs

Prefer:

- `3-4` anchors only
- one-line payoffs
- GitHub-target links for open-source projects by default
- if adding support logos, keep them to a short `Selected research support` row with roughly `3-4` logos

Avoid:

- exhaustive project catalogs
- dense metric walls
- mini-abstracts under each project
- sponsor walls or a separate funding slide inside this module

## Optional 2-Slide Variant

Only if the user explicitly asks for two slides:

- keep role separation intact
- choose which role can be omitted for that use case
- do not overload a remaining slide by merging two jobs into one crowded frame

Do not compress to one slide unless the user explicitly asks and accepts the tradeoff.

## Variant Axes

Keep the canonical three-slide family stable. If the user wants a variant, vary one axis at a time:

- auditing and assurance emphasis
- agent safety and security emphasis
- anomaly-detection roots emphasis
- external-intro flavor

Do not make every variant a full rewrite. Preserve the stable role split and adjust only the agenda wording and project choices that need to move.

## Writing Rules

- Each slide must have exactly one dominant mode: `text-first`, `visual-first`, or `compact card grid`.
- Each slide must have exactly one primary object of attention.
- Prefer short claim-style or label-style titles.
- Keep visible text broad-CS readable.
- Prefer compact project cards and grouped bullets over long prose blocks.
- Keep the personal slide more qualitative than quantitative unless the user explicitly asks for a metrics-forward intro.
- Use hyperlinks selectively where they create obvious downstream value, especially on project titles in the systems slide.
- For open-source projects, default hyperlink targets to the GitHub repository unless the user explicitly wants docs or a project page.
- If a title is hyperlinked, use subtle styling so it still reads cleanly on the slide.
- Make the module understandable even when inserted into the middle of another deck.
- Do not depend on section pages, presenter notes, or slide-number context.

## Output Convention

`templates/modules/yzhao-intro-slides.tex` should contain frame blocks only, for example:

```tex
% About Yue Zhao
\begin{frame}[t]
  \frametitle{About Yue Zhao}
  ...
\end{frame}
```

`templates/modules/yzhao-intro-facts.md` should record:

- the chosen slide family
- the preferred project set
- the chosen impact signals
- the source file and date for each number
- any unresolved ambiguity to keep out of visible slides
