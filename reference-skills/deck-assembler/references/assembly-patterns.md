# Assembly Patterns

Use these patterns to keep the merged talk coherent without over-editing the source decks.

## Default Families

### 1. Intro + One Paper

- master title
- optional short roadmap
- `1-3` intro slides from `templates/modules/yzhao-intro-slides.tex`
- one bridge slide: why this paper belongs in the talk
- one paper segment
- one short closing or synthesis slide only if needed

### 2. Intro + Two Papers

- master title
- optional short roadmap
- `1-3` intro slides
- quick talk-overview slide that tells the audience this is a combined long talk
- bridge into paper `A`
- paper `A` segment
- bridge into paper `B`
- paper `B` segment
- one short synthesis slide connecting the two papers

### 3. Research-Thread Talk

- master title
- intro module
- one agenda or thread slide if needed
- paper segments grouped by research role rather than by chronology
- short final synthesis on what the combined set establishes

## Bridge Slide Recipe

Each bridge slide should do only one job: explain why the next paper segment is here.

Recommended structure:

- title framed in the merged talk's language, not just the paper title
- one short sentence on why this paper matters in the larger agenda
- `2-3` short bullets:
  - what question this segment answers
  - why this paper is the right example
  - what the audience should watch for

Avoid:

- re-explaining the full paper abstract
- adding a second mini-introduction to the entire talk
- turning the bridge into a dense literature review

## Talk Overview Slide Recipe

When more than one paper segment will follow the intro module, add one quick `Talk Overview` slide by default.

Recommended structure:

- one short line that says this is a combined long talk
- one bullet for each major segment
- one final line on the thread that connects the segments

Keep it audience-facing:

- set expectations for the rest of the talk
- explain the role of each paper in one line
- keep it shorter than a roadmap for a single paper talk

Avoid:

- repeating the intro slide family
- turning the overview into a full agenda page with too many sub-bullets
- preemptively summarizing all technical results

## Long-Talk Bias

When the user is explicitly assembling a long talk:

- preserve the main and supporting slides of each source talk by default
- keep each paper's own setup, evidence, and takeaway arc unless the user asks to shorten it
- trim wrappers and duplicate endings before trimming technical content

When the user does not specify short versus long:

- default to this long-talk behavior for multi-paper merged decks

## What To Trim First

Before editing technical frames, trim or shorten these from source decks by default:

- local title pages
- local roadmaps or section tables of contents only if the merged deck already has a stronger master overview
- standalone `Questions?` endings
- standalone reference appendices unless the merged deck still needs projected references
- repeated problem framing that the merged deck already covered
- repeated takeaways that do not add a new role in the combined talk

## Source Handling

Most existing paper decks in this repo are standalone Beamer documents. For merged talks:

- do not `\input` a full source deck with its own `\documentclass`
- extract the needed frame blocks into the merged deck or into `decks/<talk-slug>/modules/`
- move only the required macros, packages, and figure paths into the master preamble
- prefer talk-local extracts when the same merged deck will be revised repeatedly

## Low-Risk Integration Order

1. choose the master title and throughline
2. remove duplicate wrappers
3. add bridge slides
4. unify section names and a small number of titles
5. add one final synthesis slide if the merged talk still feels segmented
6. only then consider deeper edits inside paper frames
