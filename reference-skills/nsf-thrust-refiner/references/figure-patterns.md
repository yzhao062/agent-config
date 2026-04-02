# Figure Patterns

Use this file when deciding whether a thrust or aim needs a figure.

## When A Figure Is Worth It

Add or rethink a figure when prose alone is making the reader work too hard to
understand one of these:

- a mechanism with several stages
- a data or workflow pipeline
- the relationship among subtasks
- how one thrust feeds another
- how the unit will be evaluated

Do not force one into every unit.

## Common Figure Types

### methodology-driven

- mechanism diagram:
  signal flow, latent state, control loop, or anomaly pathway
- failure taxonomy:
  grouped failure modes, their triggers, and mitigation points
- local evaluation matrix:
  subtasks against metrics, benchmarks, and outcomes

### ecosystem-building

- infrastructure stack:
  repositories, representations, discovery layer, workflow layer, users
- lifecycle figure:
  asset ingestion -> linking -> discovery -> workflow reuse -> adoption
- cross-domain testbed figure:
  shared abstraction plus domain-specific extensions
- adoption loop:
  users, contributions, feedback, releases, sustainability

## Minimum Figure Planning Output

When the figure is not being drawn in this pass, still produce:

- intended message
- likely filename
- placement in the unit
- caption skeleton
- any visible TODO needed for later asset creation

When a unit currently has no figure but clearly needs one, prefer adding both:

- a visible `\todo{...}` so human coauthors see the missing asset
- a commented LaTeX placeholder scaffold that can be uncommented later

Example placeholder scaffold:

```latex
% \begin{figure}[t]
%   \centering
%   \includegraphics[width=0.9\linewidth]{figure/thrust1-asset-graph-overview.pdf}
%   \caption{\textbf{Thrust 1 asset-graph pipeline.}
%   Repository records are normalized into a shared asset schema, linked into a
%   typed asset graph, and then exposed to downstream discovery and workflow
%   reuse components.}
%   \label{fig:thrust1_asset_graph}
% \end{figure}
\todo{Draft figure for Fig.~\ref{fig:thrust1_asset_graph} and save as
figure/thrust1-asset-graph-overview.pdf.}
```

Use an active placeholder box only when the user explicitly wants a visible
empty figure in the compiled PDF.

Example TODO:

```latex
\todo{Draft figure showing how linked assets, discovery traces, and workflow artifacts connect across the two testbeds. Save as figure/thrust3-workflow-overview.pdf.}
```
