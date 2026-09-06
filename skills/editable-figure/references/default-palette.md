# Default figure palette

The user selected CatchBench, Cat-DPO and No Attacker Needed as the lab's default color references on 2026-09-05. Apply this visual family to new paper, proposal and GitHub README figures unless the user or existing document specifies another palette. This preference concerns visual identity; it does not prescribe those papers' layouts, icon styles or scientific claims.

For proposal composition, the separately selected [proposal examples](proposal-style-exemplars.md) guide visual richness and hierarchy. They do not replace these color defaults or the established palette of a manuscript being edited.

`default-palette.json`, beside this file, is the canonical source of exact color values. Use it directly in a builder or copy its tokens into the figure's working brief. It is self-contained, so ordinary figure work does not depend on downloading the reference papers again.

## Roles and use

| Tokens | Default use |
|---|---|
| `background` | White canvas and open space. |
| `mint` | Main comparison, original record or supporting structure. |
| `coral` | Focal method, intervention, changed object or highlighted result. |
| `teal`, `gold` | Additional categories or methods when mint and coral are insufficient. |
| `gray` | Context, baseline or inactive objects, with a readable border when necessary. |
| `ink`, `mutedText` | Primary text and secondary labels. |
| `rule` | Quiet separators and non-data structure. |
| `mintStroke`, `coralStroke` | Dark outlines, connectors or labels associated with the corresponding light fills. |

Use a subset suited to the message. Most explanatory figures need mint, coral and neutrals. For a new two-series comparison, use `pairOrder`; `categoricalOrder` is a four-series preset, not a sequence to truncate for fewer series. For three series, retain the main mint/coral contrast and choose an additional color by its role. Establish a semantic mapping in the working brief and retain it across panels and related figures; existing identities take priority over either preset's order. Coral identifies the focal element, so it does not universally mean success, failure, danger or the proposed method. If a comparison is also shown in a results panel, its identities should retain their colors.

Pastel fills work with dark text and visible outlines. Use the darker stroke tokens where a light fill would disappear as a thin line. For small scientific curves, retain distinguishable markers, line styles and direct labels; do not rely on a mint/coral hue difference alone. Check the actual document width and grayscale legibility. Keep a white figure canvas for README exports unless the repository has an explicit dark theme.

## Source evidence and existing variants

These papers share a visual family, not an identical set of historical HEX values. The canonical tokens standardize future work; do not claim every token was used in all three papers or recolor their existing artifacts without a request.

Locators below are relative to the `internal-writing` repository unless a public link is given:

- **CatchBench** ([paper](https://arxiv.org/abs/2608.22808)): `papers/iclr-2027-auditablebench/figures-preamble.tex` declares mint, coral and gray used by the paper. The accepted editable Figure 1 and Gold mechanism builders under `figure-src/` supply the dark ink, secondary text, rule and darker outline tokens. Their existing mint/coral fills are `#C2DFD1` and `#ED986C`, slightly softer variants of the canonical pair. Those exact fills govern both revisions and new figures in that document unless the user requests a palette change. Do not mix both variants in a single new figure.
- **Cat-DPO: Category-Adaptive Safety Alignment** (Tiankai Yang and coauthors): [paper](https://arxiv.org/abs/2604.17299); local figures `references/style-exemplars/catdpo/figures/per_category_harm_bars_top8_floor.pdf` and `balance_panels.pdf`. RGB values recovered from their vector drawing objects are exactly the canonical mint, teal, gold and coral tokens. The overview `method_overview.pdf` also uses light mint and gold regions. Its illustrations are composition references, not artwork to copy.
- **No Attacker Needed: Unintentional Cross-User Contamination in Shared-State LLM Agents** (Tiankai Yang and coauthors): [arXiv v1 PDF](https://arxiv.org/pdf/2604.01350v1). Inspected Figure 1 on page 1 and Figure 2 on page 3 for pale green/warm fills, teal/gold accents, dark outlines and white space. The PDF also contains pale green `#D7E4BD` and pink `#F2DCDB` in Figure 1, and blue `#779BB8` and rose `#E37F80` in later plots. These document the reference's variants; they are not additional default categorical colors. New work should use the canonical tokens to keep the three-reference visual family consistent.

Source inspection date: 2026-09-05. CatchBench and Cat-DPO were checked from local source and figure PDFs; No Attacker Needed was checked from its public arXiv PDF. Existing document colors or an explicit user request override this starting palette.
