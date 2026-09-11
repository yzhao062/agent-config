# Why prun defaults to Sonnet

**Status**: superseded 2026-09-10; kept as a pointer. **Source**: `skills/prun/SKILL.md` section "Executors".

## Original rule (2026-09-08)

Ordinary `prun` units defaulted to Sonnet to preserve Codex capacity for required adversarial reviews and the other evidenced exceptions listed in `skills/prun/SKILL.md`. Mechanical work went to Sonnet or an existing script; an explicit user instruction or a declared project-local routing policy could override the default. The measurement meant to justify this specific split never shipped. Four review rounds found it asserted more than it could support. A cwd hash was read as a run id, a switched token metric, repeated usage reports counted as turns, and a mid-window snapshot was read as a weekly result. The rule went out on Sonnet-preference reasoning alone, without the measurement its own title promised.

## Completed 2026-09-10

Commit 62f1489 ("feat: add Agy review and parallel routing") replaced the exception carve-out with a flat exclusion. Codex is no longer a `prun` executor at all; its quota is reserved for the `/vet` reviewer role instead. Agy (Gemini through the Antigravity CLI) is the new external second pool alongside Sonnet, which stays the in-session default. The current rule lives only in `skills/prun/SKILL.md`; this file no longer duplicates it.

## Open

Whether the Sonnet-versus-Agy split still wants the measurement this file's title promised (quota substitution versus cross-vendor diversity, not Codex-quota preservation) is unresolved. No study has been proposed or scheduled as of this writing. The previous attempt was cut for asserting more than it could support (see above). That finding applies to any future attempt, regardless of which second pool is being compared against Sonnet.
