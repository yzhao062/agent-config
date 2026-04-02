# Tool Selection

Use this file after the figure archetype is clear.

## Default Rule

Choose the simplest editable format that matches the figure structure.

## Preferred Formats

### draw.io or SVG

Best for:

- overview architecture
- ecosystem diagrams
- thrust-level mechanism figures
- layered boxes, arrows, actors, and swimlanes

Why:

- easy to edit later
- good collaborator handoff
- straightforward PDF export
- supports a middle ground between plain boxes and fully custom illustration

Preferred styling guidance for proposal figures in these formats:

- use grouped background regions rather than only isolated boxes
- use small icon badges or pictograms when they clarify semantics
- route arrows orthogonally or with smooth deliberate curves
- avoid the look of a raw slide wireframe unless the user asked for a
  placeholder

### Graphviz

Best for:

- typed graphs
- dependency diagrams
- asset-linking or relation-heavy figures

Why:

- good for automatic layout
- easier than hand-placing complex graphs

Avoid for:

- polished ecosystem art with many custom visual groupings

### matplotlib

Best for:

- charts
- simple timelines
- benchmark or evidence plots

Why:

- deterministic
- easy PDF output
- good for data-backed visuals

### TikZ

Best for:

- LaTeX-native timelines
- relatively regular technical diagrams
- cases where reproducible, code-side updates matter more than easy GUI editing

Use cautiously:

- avoid for highly detailed artistic diagrams
- avoid when many collaborators need quick manual edits

## Outside Image Tools

Gemini, Sora, Nano Banana, and similar tools are useful for:

- composition ideas
- visual mood
- rough icon or scene inspiration

They are not the preferred source of truth for final proposal figures because
their outputs are typically raster images that are hard to edit precisely.

Use them as ideation tools, then rebuild the final figure in an editable local
format.

## Quick Decision Guide

- boxes and arrows with collaborators likely to tweak text:
  choose `draw.io` or `svg`
- graph structure matters most:
  choose `graphviz`
- chart or timeline driven by data:
  choose `matplotlib`
- LaTeX-native and moderately structured:
  choose `tikz`
