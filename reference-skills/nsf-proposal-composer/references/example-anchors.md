# Example Anchors

Use `examples/catalog.csv` as the first source of truth when selecting prior
proposal anchors. Do not rediscover the family split from scratch unless the
user says the catalog is stale.

When the user wants aim-file generation that follows existing house style, first
match on:

1. `family`
2. `unit_label`
3. `unit_count`

## ecosystem-building anchors

- `examples/proposals/GEO OSE Proposal/1thrust1-spatio-temporal-scoping.tex`
- `examples/proposals/GEO OSE Proposal/4thrust4community_new.tex`
- `examples/proposals/NSF_POSE_Phase_1_Proposal/2Approach.tex`
- `examples/proposals/NSF-23-POSE-Phase-II-OpenAD`
- `examples/proposals/NSF_24_POSE_Phase_I_TrustLLM`
- `examples/proposals/NSF_24_ReDDDoT_Phase_II`

Use these to learn:

- ecosystem vision framing
- work package or thrust decomposition
- governance and sustainability language
- community, adoption, and open-source positioning

## methodology-driven anchors

- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/01aim1.tex`
- `examples/proposals/NSF-Core-2026-Feb5th-Agentic-AD/04aim4.tex`
- `examples/proposals/NSF-SaTC-MultiAgent-Safety/01aim1-perception.tex`
- `examples/proposals/NSF-SaTC-MultiAgent-Safety/04aim4-meta.tex`
- `examples/proposals/CPS_CIR_2025_Foodbank`
- `examples/proposals/NSF25_S_CC_Full_Proposal`
- `examples/proposals/NSF_Algorithms_for_Threat_Detection___2024`

Use these to learn:

- aim or study decomposition
- technical novelty framing
- evaluation logic
- risk and mitigation patterns

## Anchor Selection Rules

- Prefer 1-2 anchors from the same family over many loosely related examples.
- Use overlays, `unit_label`, and `unit_count` from `examples/catalog.csv` to
  break ties.
- Prefer the most structurally complete examples, not necessarily the newest.
- Do not copy phrasing. Reuse structure, sequencing, and argument function.
