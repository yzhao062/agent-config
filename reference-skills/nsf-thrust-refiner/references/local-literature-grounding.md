# Local Literature Grounding

Use this file when refining a unit requires stronger citation support.

## Source Priority

Prefer sources in this order:

1. active proposal bibliography:
   `<proposal-dir>/bibs/*.bib`
2. template bibliography:
   `template/bibs/*.bib`
3. example proposal bibliographies:
   `examples/proposals/**/*.bib`
4. citations already used in neighboring units

Use the repository-local helper:

```powershell
python skills\nsf-thrust-refiner\scripts\search_local_bib.py --proposal-dir <proposal-dir> <keyword> <keyword>
```

Example:

```powershell
python skills\nsf-thrust-refiner\scripts\search_local_bib.py spatio temporal knowledge graph provenance workflow
```

## What To Look For

For methodology-driven units, local citations usually play one of these roles:

- prior anomaly-detection or modeling baselines
- benchmark or evaluation precedent
- failure-mode evidence
- enabling methods that justify the proposed mechanism

For ecosystem-building units, local citations usually play one of these roles:

- infrastructure or knowledge-graph precedent
- open-science or FAIR precedent
- domain-data ecosystem precedent
- workflow or reproducibility precedent
- user-community or adoption precedent

## Citation Rules

- Prefer citations that support a concrete sentence, not just a topic.
- Group citations by function rather than dumping many keys into one sentence.
- For overview, motivation, or background paragraphs, prefer external surveys,
  standards, community systems, or foundational papers as the main anchors.
- Do not use the team's own papers as the main support for broad field-wide or
  infrastructure-wide claims unless the paragraph is explicitly about prior
  project outputs or direct technical inheritance.
- If the exact cite key is uncertain, leave:

```latex
\todo{Add citation for "Paper Title"}
```

- Do not fabricate cite keys.
- Do not widen the claim beyond what the local literature actually supports.
