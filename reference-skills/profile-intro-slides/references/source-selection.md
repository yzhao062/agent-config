# Source Selection

Use website-first sources by default. This skill is meant to preserve the current public positioning of Yue Zhao and FORTIS Lab, not to reconstruct an exhaustive CV narrative.

## Primary Sources

- `yzhao062.github.io/files/bio.txt`
  - Best source for polished personal positioning, affiliation, and compact impact summary.
- `yzhao062.github.io/index.html`
  - Best source for the current research summary and the three main research directions.
- `yzhao062.github.io/lab.html`
  - Best source for the FORTIS expansion, mission statement, and lab-level framing.
- `yzhao062.github.io/data/open-source.json`
  - Best source for representative systems, project roles, and project-level impact signals.
- `yzhao062.github.io/data/publications.json`
  - Best source for representative recent papers and direction coverage.

## Secondary Sources

- `yzhao062.github.io/data/lab-current-phd.json`
  - Use when a slide needs limited evidence of lab scope or trainee profile.
- `yzhao062.github.io/data/lab-members.json`
  - Use sparingly for lab breadth, student outcomes, or mentorship evidence.
- `yzhao062.github.io/files/ZHAO_YUE_CV.pdf`
  - Use only to fill gaps such as awards, service, or older history.
- `yzhao062.github.io/images/rsz_250.jpg`
  - Preferred portrait unless the user asks for a different image.
- `yzhao062.github.io/images/lab-logo.png`
  - Preferred lab mark.

## Omit By Default

Do not treat these as default fixed-slide content:

- news feeds
- recruiting logistics
- application instructions
- external employment disclosures
- collaboration policies
- full award rollups
- full publication dumps
- full member listings

These blocks are useful for the website, but they stale too quickly for reusable intro slides.

## Stable vs Volatile Content

Safe default content:

- current title and affiliation
- FORTIS expansion and mission
- three research directions
- representative systems and projects
- a small number of durable impact signals

Preferred placement:

- personal identity slide: qualitative positioning, not metric-heavy
- personal identity slide: if a lab-scale signal is useful, prefer `lab-current-phd.json` for the stable core count and treat `lab-members.json` as qualitative context for a broader rotating team
- agenda slide: a clean pillar map, not website prose
- systems slide: representative projects plus an optional dated impact strip only if it remains visually secondary
- systems slide: optional selected-support logo strip only if it remains quieter than both the cards and the metrics

Volatile content that needs caution:

- paper counts
- download counts
- GitHub star counts
- hiring status
- funding counts
- rolling news items

If a volatile number is important enough to include, record its source and exact date in the fact sheet. Prefer phrasing like `as of March 2026` instead of leaving the timestamp implicit.
If the number competes with the slide's main message, remove it instead of forcing it in.

When the deck is likely to circulate as PDF, it is usually worth adding hyperlinks on project names in the systems slide so the module can also function as a lightweight landing surface.
For open-source projects, default those links to the GitHub repository unless the user explicitly prefers docs or a project page.

## Conflict Resolution

When sources disagree:

1. Prefer the more recent website wording for current positioning.
2. Prefer structured data files for project lists and project metrics.
3. Use the CV only when the website lacks the needed fact.
4. If the conflict remains unresolved, note it in `yzhao-intro-facts.md` instead of guessing.
