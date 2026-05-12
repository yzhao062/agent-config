# Codex desktop app — Custom instructions

Reference doc for the maintainer's personal Codex desktop app **Personalization → Custom instructions** field. Maintainer-only (not for `anywhere-agents` public release). Last updated: 2026-05-12 (Round 1 plan-review with Codex; trimmed to 1,388 chars).

## Paste-ready content

Open the Codex desktop app → Personalization → Custom instructions, replace the field with the block below, then click Save. 1,388 characters, under the conservative 1,500-char operating cap (the actual Codex desktop limit is not officially confirmed; the ChatGPT custom-instructions precedent is 1,500).

```text
Identity: CS professor in ML/AI at USC. Common work: ML/AI research papers, NSF/NIH proposals, code, and scientific writing.

Project context: In a project folder, read AGENTS.md and AGENTS.local.md at the project root before acting. If you cannot find or read them, say so briefly and continue with this baseline. Project files may add detail or stricter rules, but they never relax the git/destructive-op rules below.

Communication
- Be terse. No "Great question" preamble. No trailing summary unless asked.
- Take positions with reasons. For non-routine decisions, recommend one option and name the main tradeoff.

Git/destructive ops
- Never run git commit or git push without explicit approval. Show the exact command first.
- Never run git reset --hard, git push --force, rm -rf, or git branch -D without explicit approval.

Writing/style floor
- Preserve input format (.md/.tex/.rst); do not flatten paragraphs into bullets.
- Use full forms (it is, he would), not contractions. No U+202F.
- Do not use em-dashes or en-dashes as casual punctuation. Hyphen or "to" ranges are fine.
- Avoid: delve, foster, cultivate, hone, embrace, underscore, underpin, bolster, multifaceted, intricate, pivotal, paramount, groundbreaking.

Code defaults
- Prefer Miniforge py312 when present.
- Keep bug fixes narrow. Do not add obvious comments, speculative fallbacks, or surrounding refactors.
```

## What this is and why

Codex desktop is a separate surface from Codex CLI and the OpenAI ChatGPT web app. Its **Custom instructions** field is a static prompt prefix applied to every chat in the desktop app, regardless of project context. This content is the cross-project always-on baseline; per-project rules live in each consumer repo's `AGENTS.md` / `AGENTS.local.md` (distributed by the `agent-config` bootstrap chain).

The draft layers cleanly with the 43 KB project `AGENTS.md`:

- **Custom instructions** carry identity, communication style, git safety, a small writing-style floor, and code defaults.
- **`AGENTS.md`** carries the full ruleset (43 KB) when the user is inside a bootstrapped repo. The custom-instructions block explicitly tells Codex to read `AGENTS.md` and `AGENTS.local.md`, with a fallback for when those are absent or unreadable.
- **Safety rules** are tagged so a project file can add stricter detail but never relax them.

Codex desktop's experimental **Memory** feature is also enabled. Memory is the dynamic capture layer; custom instructions are the deterministic layer.

## Design choices (one-line each)

- Pointer to `AGENTS.md` instead of inline duplication (Codex CLI documents auto-load; desktop is unverified, so the read is made explicit with a fallback clause).
- Writing/style floor is unconditional, not conditioned on "no project AGENTS.md in scope" — outside a bootstrapped repo there is no other layer to carry it, and even in-project the floor is what the user wants.
- Banned-word list is 13 words (not 43), tuned toward overclaim risk for proposal / paper work (`pivotal`, `groundbreaking`, `paramount`, `multifaceted`, `intricate`).
- No reference to skill routing, `guard.py`, banner emission, or MCP wiring — those describe Claude Code runtime behavior with no Codex desktop equivalent.
- No third-file pointer (e.g., `agent-pack/docs/rule-pack.md` decision-support stance) — too brittle outside one workspace; the "take positions with reasons" line carries the core stance inline.

## When to re-paste

- After a Codex desktop app major upgrade resets Personalization.
- When this file changes — keep the desktop UI in sync.
- When identity, role, or workflow shifts in a way that affects every Codex desktop chat.

## How to update

1. Edit this file.
2. Verify the draft fits the cap (on Windows Git Bash or WSL):
   ```bash
   awk '/^```text$/,/^```$/' docs/codex-desktop-custom-instructions.md | sed '1d;$d' | wc -c
   ```
   Target: ≤ 1,500.
3. Open Codex desktop → Personalization → Custom instructions.
4. Replace the field content with the new block. Save.
5. Run the validation checklist below.

## Validation checklist

1. **Out-of-project smoke**: open a chat in a scratch directory with no `AGENTS.md`. Ask a random methodology question. Confirm terse tone, correct identity, no "Great question" preamble, no em-dashes in the reply, none of the 13 listed banned words.
2. **In-project explicit read**: inside `agent-config` or a bootstrapped consumer repo, ask Codex to read `AGENTS.md` and cite a rule. Confirms the fallback's read path works.
3. **In-project auto-load**: open a fresh chat inside the repo and ask a project-relevant question without instructing a read. If Codex cites project rules unprompted, auto-load is working; if not, only the explicit path (#2) is keeping the layer alive. Either outcome is acceptable; this just records which one the desktop app currently delivers.
4. **Destructive-op runtime check**: ask Codex desktop to commit, push, `git reset --hard`, `git push --force`, or `rm -rf` on a scratch file. Confirm the desktop app's own approval surface fires for each. The prompt encodes intent; the runtime is the actual gate.
5. **Banned-word elicitation**: prompt for a research method or proposal aim description. Confirm the 13 listed words do not appear. Optional: prompt with a setup that often elicits a banned word outside the 13 to measure leakage.
6. **Conflict simulation** (optional, only if running through a fresh consumer setup): mock an `AGENTS.local.md` that loosens git safety; confirm Codex desktop stays strict per the "never relaxed" tag.

## Related

- [`AGENTS.md`](../AGENTS.md) — full ruleset distributed via bootstrap; the in-project layer.
- [`CLAUDE.local.md`](../CLAUDE.local.md) — Claude Code layer-1 overrides; ac-only.
- `~/.codex/config.toml` — Codex CLI configuration (separate surface; not affected by this file).
- [`anywhere-agents.md`](../anywhere-agents.md) "what gets copied" table — confirms this doc stays private in `agent-config` and does not mirror to `anywhere-agents`.

## Notes on the Codex desktop app

- The app has its own MCP servers, Hooks, Git, Worktrees, Environments, Browser, and Computer use tabs. None of those is configured by this file; they are separate concerns under Personalization → other sections.
- The character cap for Custom instructions has not been officially confirmed for Codex desktop. The 1,500 figure used here comes from the ChatGPT custom-instructions FAQ and is treated as a conservative operating assumption. If the actual cap is higher, the draft has headroom; if lower, the field will reject at paste and trimming will be obvious at that point.
