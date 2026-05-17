# agent-pack: `pack.yaml` self-refs `ref: main` despite v0.1.0 ship

**Status**: open. **Source**: `agent-pack/pack.yaml:33, 49, 66`. **Target**: next ap release prep or v0.2.0 cycle.

## Why this file exists

The deferral is tracked in-line in `agent-pack/pack.yaml` via three inline comments at the source-ref lines. This local file is a thin pointer so the maintainer's working memory (in `agent-config`) surfaces it when planning ap work, instead of relying on remembering to grep the ap repo.

## Symptom

`agent-pack/pack.yaml` declares three pack entries (`profile`, `paper-workflow`, `acad-skills`); each entry's `source.ref:` field is pinned to `main` with an inline `# development ref; consumers should pin a tag (e.g. v0.1.0) once published` comment. Tag `v0.1.0` was published 2026-04-26 (per `git -C ../agent-pack log v0.1.0 -1`), so the deferral condition has been met, but the manifest was never bumped.

Consequence: consumers following the manifest get the `main` ref, not a tagged ref. Composer-side drift becomes possible if ap's `main` advances between consumer installs. Not currently a release-gate blocker; `agent-pack` is a third-party user-installed pack, not a bundled default of aa (per `anywhere-agents/CHANGELOG.md:237`, which describes `agent-pack v0.1.0` as the direct-URL install acceptance test target for aa v0.5.0).

## Suggested approach

Three single-line edits in `agent-pack/pack.yaml`:

- `pack.yaml:33`: `ref: main` -> `ref: v0.1.0`
- `pack.yaml:49`: `ref: main` -> `ref: v0.1.0`
- `pack.yaml:66`: `ref: main` -> `ref: v0.1.0`

Plus a CHANGELOG note in `agent-pack/CHANGELOG.md` if one exists.

If `main` carries newer content that should ship before pinning, instead cut `v0.1.1` first, then bump the refs to `v0.1.1`. Decide at edit time based on `git log v0.1.0..main`.

## When to pull in

Next time work touches ap (e.g., aa-side bundled-default switch to `agent-style-field` per `2026-05-16-aa-gh-1-context-bloat-remaining.md` Item A, which may surface ap stacking concerns), OR next ap release prep, OR opportunistic next time the maintainer opens `agent-pack/`.

## Effort estimate

15 minutes: 3 line edits + CHANGELOG note + ap commit + push.
