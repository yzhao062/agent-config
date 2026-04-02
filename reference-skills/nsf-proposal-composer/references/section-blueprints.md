# Section Blueprints

Use these blueprints to map a project brief into concrete proposal sections.

## Common Core Across Both Families

These sections appear in most NSF proposals regardless of family:

- project summary
- problem or need statement
- technical core
- evaluation and measurable outcomes
- broader impacts
- team fit or collaboration structure
- data management and other supporting documents

## ecosystem-building Blueprint

Preferred order:

1. problem landscape and blocked community need
2. ecosystem or platform vision
3. architecture or capability model
4. work package 1
5. work package 2
6. work package 3
7. work package 4 or community/adoption/sustainability package
8. evaluation and milestones
9. management, sustainability, and broader impacts

Recommended internal slots per work package:

- objective
- capability delivered
- research or engineering uncertainty
- dependencies
- expected artifacts
- adoption hook
- success metric

## methodology-driven Blueprint

Preferred order:

1. problem statement and gap
2. central premise or hypothesis
3. aim or study 1
4. aim or study 2
5. aim or study 3
6. aim or study 4
7. evaluation and risk mitigation
8. broader impacts and team fit

Recommended internal slots per aim:

- objective
- technical gap
- core method
- expected advance
- evaluation hook
- risk and fallback

## Mapping To This Repository

Current repo defaults are closest to `methodology-driven`, but both families can
use the same file skeleton under `template/`.

Primary files:

- `template/00-project-summary.tex`
- `template/00-project-description.tex`
- `template/03-team-qualification.tex`
- `template/11-aim1.tex`
- `template/12-aim2.tex`
- `template/13-aim3.tex`
- `template/14-aim4.tex`
- `template/20-evaluation.tex`
- `template/21-prior-nsf-support.tex`
- `template/31-data-management.tex`
- `template/32-collaboration-plan.tex`
- `template/33-bpc.tex`
- `template/34-facility.tex`

Mapping guidance:

- For `methodology-driven`, keep `template/11-14` as aims or studies.
- For `ecosystem-building`, reinterpret `template/11-14` as work packages, thrusts, or
  ecosystem components.
- Keep `template/20-evaluation.tex` for milestones, adoption evidence, and measurable
  outcomes in both families.
- Keep `template/03-team-qualification.tex` and `template/21-prior-nsf-support.tex`
  separate from the main description so collaborator-owned updates do not force
  direct edits to the proposal entrypoint.
- Treat `template/context/team/_template/profile.md` as the reusable schema for
  PI-source-material normalization before writing qualification prose.
- Use `template/32-collaboration-plan.tex` and `template/33-bpc.tex` only when
  the solicitation or project design makes them material.

## Drafting Order

Recommended order for patching files in this repo:

1. `template/11-14` core sections
2. `template/00-project-summary.tex`
3. `template/00-project-description.tex` structure and headings
4. `template/20-evaluation.tex`
5. team / prior-support modules
6. supporting sections

This order reduces cross-section drift and makes later consistency refreshes
cheaper.
