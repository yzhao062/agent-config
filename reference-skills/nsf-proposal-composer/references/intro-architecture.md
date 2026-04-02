# Intro Architecture

Use this reference when the user wants the proposal introduction itself
improved, not just synced mechanically to existing aims.

## Goal

Build an introduction that does four jobs in order:

1. establish why the problem matters
2. identify the main gaps or challenges in current practice
3. present the central proposal claim
4. introduce a coherent thrust sequence

For this repository, `composer` should treat this as a proposal-level
architecture task, not a wording-only polish pass.

## Default Pattern

### Layer 1: Importance

The opening paragraph should usually answer:

- why this matters for science, infrastructure, national capability, or open
  science
- why the problem is broad enough to justify an NSF proposal
- why the cost of the status quo is real

At this stage, the paragraph can be structurally correct even if some
citations, figures, or precise wording still need to be added later.

### Layer 2: Gaps Or Challenges

The next move is to name the gaps explicitly. Prefer `2-4` gaps.

Good gaps are:

- structural, not incidental
- reusable across the whole proposal
- broad enough to justify a thrust
- specific enough that a reviewer can see what is missing today

Avoid listing disconnected annoyances. The gaps should feel like the actual
reasons the problem remains unsolved.

### Layer 3: Central Proposal Claim

After the gaps, state what the project will make possible.

This is not yet the full overview of the aims. It is the one- or two-sentence
answer to:

- what are we building or studying
- why is that the right answer to the gaps above

### Layer 4: Coherent Thrust Chain

Only after the importance and gaps are clear should the intro enumerate the
thrusts.

The thrusts should read like a progression, for example:

- representation -> discovery -> reproducible workflows
- data foundation -> intelligent methods -> deployment and reuse

If a unit does not fit as part of the progression, it may belong in evaluation
or adoption rather than as a separate thrust.

## Quality Checks

Before using the intro as the source of truth for aim generation, verify:

- the first paragraph is about importance, not the method
- the named gaps are actually the gaps the thrusts solve
- each thrust can be traced back to at least one named gap
- the thrust order looks intentional rather than arbitrary
- the intro does not overspecify subtask details that belong in the aim files

## Typical Prompt Patterns

```text
使用 $nsf-proposal-composer，先优化当前 intro：第一段讲 importance，第二段提炼 gaps，再映射到 thrusts
```

```text
使用 $nsf-proposal-composer，检查当前 intro 的 gap-to-thrust mapping 是否顺；如果不顺，先重组框架再刷新 aims
```
