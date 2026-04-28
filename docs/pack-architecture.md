# Pack architecture (long-term design)

Design note for the `anywhere-agents` (aa) pack composition architecture. Spans aa core design, coordinated `agent-style` (as) variants, the future `agent-behave` (ab) product shape, and the knock-on effects on `MIGRATIONS.md`, `ONBOARDING.md`, and `docs/ac-to-aa-migration.md` across the v0.4.0 → v1.0.0 release trajectory.

**Audience**: maintainer; tracked in `ac` but not mirrored to `aa` (see `docs/anywhere-agents.md` for the mirror policy). Parts may be sanitized for public reference once implementation lands.

**Status**: active implementation reference. v0.4.0 shipped on 2026-04-24 (pack-v2 schema, active-kind dispatch, pack-management CLI, state + lifecycle primitives). Composer-side outer-lock acquisition, automatic startup reconciliation wiring, and bootstrap consumption of the 4-layer user-level resolver remain v0.4.x follow-ups tracked throughout this file. Replaces any prior `PLAN-skill-pack-composition.md` reference.

**Scope**: this design contract is scoped to ac → aa consolidation and bootstrap portability (private-pack support, user-level config, CLI, auth chain). Broader platform surface (registry, `~/.agent-profile/memory.md` bridge, consumer-facing rename migration, ecosystem framing) remains gated by the adoption tests in `docs/vision.md` and is not a deliverable of this contract.

**Related docs**: this file is the implementation hub. During coding, read this file only. Open companions at specific triggers:

- `docs/vision.md` — scope gates (Step 2/3 adoption tests, kill criteria, naming stance). Consult before adding or expanding this contract to confirm the proposed feature passes vision's gates. Frozen after 2026-04-22; not edited during impl.
- `docs/ac-to-aa-migration.md` — consumer-side migration runbook for today's ac → aa rollout. Updated at release time per the Per-release maintainer-doc impact table below; not touched during impl iteration.
- `archive/plans/PLAN-skill-pack-composition.md` — archived source plan (gitignored under `/archive/`); superseded by this file per the Status line above. Consult only for design archaeology, not for current truth.
- `../anywhere-agents/RELEASING.md`, `ONBOARDING.md`, `scripts/check-parity.sh` — release runbook, release-runbook cheat sheet, STRICT parity gate. Touched at release time per the impact table.

## Purpose

Decide the long-term pack abstraction so that:

1. Rule-pack and skill-pack stop being parallel concepts with parallel code paths (Axis 1 below: passive vs active).
2. Future content types (safety bundles, behavior bundles) fit the same shape without schema carve-outs.
3. Hard-enforcement noise is a first-class manifest property, not an emergent cost.
4. Paper / proposal / submodule repos can leave `ac` and use `aa` via private-source packs (Axis 2: public vs private).
5. The `ac` ↔ `aa` divergence stops being a mirror maintenance problem and becomes a natural source-axis asymmetry the platform handles natively.
6. The release-runbook contract (consumer migration, STRICT parity, bootstrap self-update, local end-to-end install smoke) stays enforceable at every step of the v0.4.0 → v1.0.0 trajectory.

## Non-goals

- Shipping v0.4.0 code as part of this doc.
- Changing `agent-style`'s 21 rules or `RULES.md` content.
- Picking a product name between `agent-behave` and `agent-enforce` (both fine; product naming is separate from taxonomy).
- Setting an EOL date for `ac`. `ac` shrinks organically; no forced calendar.
- Public marketing / README rewrites; those follow the architecture lock-in.

## Context: the four questions

The design came out of a single session walking four architectural questions on `ac` / `aa` / `as`:

**Q1 — Real `ac` ↔ `aa` divergence today**: three ac-only shared skills (`bibref-filler`, `dual-pass-workflow`, `figure-prompt-builder`), `reference-skills/*`, USC / Overleaf AGENTS.md sections, aa-only rule-pack composer, aa-only PyPI + npm packaging. Hooks (`guard.py`, `session_bootstrap.py`) and generator (`generate_agent_configs.py`) are STRICT byte-identical. The real blocker for migration: `aa` cannot load private content.

**Q2 — Migration lever**: one change unlocks ac→aa for paper / proposal / submodule repos: `aa` gains a unified `packs:` config surface with SSH / gh CLI token / `GITHUB_TOKEN` auth. Paper repos become "aa + one private pack" and stop depending on `ac`'s private skills directory.

**Q3 — `aa` final shape**: composition platform. Packs (public or private) declare content; `aa` composes into `AGENTS.md` + `.claude/` + `~/.claude/hooks/` + `~/.claude/settings.json`. `ac` shrinks to "content that does not belong in any private git repo either" (personal planning, scratch, vision docs).

**Q4 — Is safety a third pillar?**: no. Safety content (text instructions, hook code, permission patterns) reduces to a passive-rule pack that ships optional hook and permission items. The real axis is passive vs active; enforcement strength is a property of active items only.

## The two axes

**Axis 1 — behavior**:

```
passive   →  text absorbed into the agent's context (inline into AGENTS.md)
active    →  explicit invocation on a trigger (agent-invoked OR runtime-invoked)
             - "skill" = active, trigger = agent-detect
             - "hook" = active, trigger = PreToolUse / SessionStart / etc.
             - "permission" = active, trigger = PreToolUse (declarative form)
```

Enforcement strength (`warn / ask / deny / allow / modify`) is a property of each active item. Passive content has no enforcement dial; it is soft by construction.

**Axis 2 — source**:

```
public    →  fetched from public repos on GitHub (or other open source);
             no auth required (today: aa shared skills, agent-style rule-pack)
private   →  requires auth chain: ssh key → gh CLI token → GITHUB_TOKEN env
             (today: blocked; this is the ac→aa migration gap)
```

**2x2 grid of real packs**:

```
                  passive                            active
public       agent-style (rule-pack)             implement-review, my-router,
             agent-style-field (as v0.4)          ci-mockup-figure (aa-shipped)
             agent-behave text (future)          agent-behave hooks (future)

private      lab-writing rules                   nsf-helper skill
             USC-Overleaf rules                  bibref-filler / dual-pass /
                                                 figure-prompt-builder (migrated
                                                 out of ac to per-user private repo)
```

Every cell uses the same manifest shape. Axis 1 is expressed via `passive:` / `active:` field presence. Axis 2 is expressed via `source:` URL + auth chain. The composer does not branch on either axis; dispatch is by field presence.

Six candidate third-axis dimensions were considered and rejected through two plan-review rounds; see "Open questions / Axis completeness" at the end of this doc for the rejection rationale for each.

## The unified manifest

A pack is a set of passive slots plus a list of active items. No `type:` field; composer dispatch is by `kind:` on each active entry (four kinds below). Every active entry declares which agent hosts it targets.

```yaml
# bootstrap/packs.yaml (keeps rule-packs.yaml as a loader alias through v0.5.x)
version: 2
packs:
  - name: agent-style
    description: Writing rules (21 from Strunk/White, Orwell, Pinker, Gopen-Swan + field observation).
    source:
      ref: v0.3.2
      repo: https://github.com/yzhao062/agent-style
    update_policy: locked                      # explicit override (v0.5.0 default is prompt); see Source resolution below
    passive:
      - files:
          - from: docs/rule-pack.md
            to: AGENTS.md
    active:
      - kind: hook
        hosts: [claude-code]
        files:
          - from: scripts/banned-word-hook.py
            to: ~/.claude/hooks/agent-style/01-banned-word.py
        trigger: PreToolUse
        scope: [Write, Edit, MultiEdit]
        file-filter: [.md, .tex, .rst, .txt]
        decision: ask                          # demoted from deny; see Noise audit
        trigger-rate: high
        false-positive-risk: high
        impact-if-allowed: low
        rationale: Banned AI-tell words; false positives on meta-discussion are common.

  - name: agent-behave
    description: Behavior rules (git safety, shell guards, permission policies).
    source:
      ref: v0.1.0
      repo: https://github.com/yzhao062/agent-behave
    update_policy: locked
    passive:
      - files:
          - from: docs/behave-rules.md
            to: AGENTS.md
    active:
      - kind: hook
        hosts: [claude-code]
        files:
          - from: scripts/git-destructive-guard.py
            to: ~/.claude/hooks/agent-behave/01-git-guard.py
        trigger: PreToolUse
        scope: [Bash]
        match: [git push, git commit, git merge, git rebase]
        decision: ask
        trigger-rate: medium
        false-positive-risk: low
        impact-if-allowed: high
      - kind: hook
        hosts: [claude-code]
        required: false                        # skip with warn on non-claude hosts; pack still installs
        files:
          - from: scripts/compound-cd-guard.py
            to: ~/.claude/hooks/agent-behave/02-compound-cd.py
        trigger: PreToolUse
        scope: [Bash]
        match: [cd * && *, cd *; *]
        decision: ask                          # demoted from deny
        trigger-rate: high
        false-positive-risk: high
        impact-if-allowed: medium
      - kind: permission
        hosts: [claude-code]
        files:
          - from: settings/permissions.json
            to: ~/.claude/settings.json
        merge: permissions

  - name: implement-review
    description: Review-loop workflow skill.
    passive: []
    active:
      - kind: skill
        hosts: [claude-code]
        files:
          - from: skills/implement-review/       # directory; deep-copied
            to: .claude/skills/implement-review/
        trigger: agent-detect
        scope: [on user request, on staged diff]
        decision: execute                         # not a gate
        trigger-rate: low
```

**Four active kinds** (explicit `kind:` replaces target-path inference):

- `kind: hook` → copy files to `~/.claude/hooks/<pack>/<NN>-<name>`, where `<NN>` is the manifest-order two-digit prefix (forces deterministic execution order against Claude Code's filename-alphabetical hook runner). Wire up in `~/.claude/settings.json` hooks block.
- `kind: skill` → deep-copy the source directory into `.claude/skills/<name>/`, preserving `references/`, `scripts/`, `assets/`, etc. Auto-emit `.claude/commands/<name>.md` pointer unless the pack ships one explicitly via a separate `kind: command` entry. Starting v0.4.0, all `aa`-shipped skills (`implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`) become pack-emitted, removing the 4 static pointers from the STRICT parity list (see STRICT trajectory table).
- `kind: permission` → merge declarative JSON into `~/.claude/settings.json` permissions array (add-only during install; ownership tracked in `.agent-config/pack-state.json` and `~/.claude/pack-state.json`, not inline since JSON disallows comments).
- `kind: command` → standalone `.claude/commands/<name>.md` files not tied to a skill. v0.4.0 parser accepts `kind: command` entries but treats them as **no-op + warn** (forward-compatibility slot). Full install support lands when a shipped pack first uses it; decision deadline before that pack merges.

**Per-entry required field**:

Every active entry carries `required: true | false` (default: `true`). On composition:

- If the current host appears in the entry's `hosts:` list, the entry installs normally.
- If the current host is **not** in `hosts:` and `required: true`: composition fails with a `host-mismatch: pack '<name>' requires host X, current host is Y` error. The pack does not partially install.
- If the current host is **not** in `hosts:` and `required: false`: the entry is skipped with an info-level log line (`pack '<name>': skipping active entry for host X on current host Y`). The rest of the pack (passive + other compatible active entries) installs normally.

The default `required: true` protects pack authors who designed their pack around a specific host; pack authors mark optional cross-host entries with `required: false` explicitly. At v0.4.0 the only supported host is `claude-code`, so entries with `hosts: [claude-code]` install and entries with any other host either fail (if `required: true`) or skip (if `required: false`). This future-proofs the schema without committing v0.4.0 to multi-host implementation.

**Pack-level fields**:
- `hosts:` can be declared at the pack level as a default; each `active:` entry may override. Entry-level value wins on conflict.
- `update_policy:` (`locked` | `prompt` | `auto`) governs whether a mutable ref may refresh content across bootstraps. Default: `prompt` for both passive and active items as of v0.5.0 (was `locked` in v0.4.x). `prompt` surfaces upstream drift via a banner and asks the consumer to apply or skip; `ANYWHERE_AGENTS_UPDATE=apply` opts in non-interactively. `locked` remains available for packs that must not auto-update active code without an explicit pack-update command. `auto` is permitted for passive items only. See "Source resolution and active-code trust" below.

**Dispatch order**: passive entries inline-concatenate into `<consumer>/AGENTS.md` with begin/end markers, byte-stable under re-compose, deterministic sort by pack name. Active entries dispatch by `kind:` per the four rules above. All writes produce entries in the pack state files (see "Pack lifecycle operations").

**Public vs private source (Axis 2 in practice)**: `source:` is the only field that distinguishes public from private. No `visibility:` flag, no `auth:` branch in the composer's top-level dispatch. **Starting in v0.5.0**, the composer attempts the auth chain for every source URL; public URLs succeed on anonymous, private URLs succeed on an authenticated method. Manifest shape is identical across the 2x2 grid. In v0.4.0, private source entries are rejected at parse time with a "v0.5.0 feature" error; the v0.4.0 composer only fetches public anonymous URLs.

**Source resolution and active-code trust**: public / private controls how a pack is fetched, not whether the fetched content is trusted. Every source resolves to an immutable commit id before composition. The composer writes `.agent-config/pack-lock.json` recording, per pack and per file: the declared source URL, the declared ref (tag or branch), the resolved commit id, and the sha256 of every passive and active input. The default `update_policy: prompt` (v0.5.0+) surfaces upstream drift on every bootstrap: when the resolved commit id or any input hash differs from the lock, the composer emits a banner listing the affected packs and files and asks the consumer to apply or skip. `ANYWHERE_AGENTS_UPDATE=apply` short-circuits the prompt for CI / scripted refresh; `ANYWHERE_AGENTS_UPDATE=skip` keeps the locked snapshot. Packs that must never auto-refresh active code can declare `update_policy: locked`, in which case the composer fails closed on any drift outside an explicit pack-update command. Passive entries may declare `update_policy: auto` for silent refresh. The first install and every explicit update print the active files that will be copied into `~/.claude/hooks/`, `.claude/skills/`, `.claude/commands/`, or `~/.claude/settings.json`. A public tag, private branch, SSH auth, or `GITHUB_TOKEN` proves only where the content came from; the lock file proves what content is currently installed.

**`update_policy: auto` churn semantics**: a passive entry with `auto` policy refreshes content when the upstream commit id or file sha256 changes. The composer rewrites `pack-lock.json` **only when the resolved hash actually changed**. Repeated bootstraps against an unchanged upstream leave `pack-lock.json` byte-identical (no git-diff churn). Active entries never use `auto`; attempting to set it on an active entry is a manifest error.

**`pack-lock.json` schema** (expanded example covering mixed pack types):

```json
{
  "version": 1,
  "packs": {
    "agent-style": {
      "source_url": "https://github.com/yzhao062/agent-style",
      "requested_ref": "v0.3.2",
      "resolved_commit": "39cdc67a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e",
      "pack_update_policy": "locked",
      "files": [
        {
          "role": "passive",
          "host": null,
          "source_path": "docs/rule-pack.md",
          "input_sha256": "f175e39b...",
          "output_paths": ["AGENTS.md"],
          "output_scope": "project-local",
          "effective_update_policy": "locked"
        }
      ]
    },
    "agent-behave": {
      "source_url": "https://github.com/yzhao062/agent-behave",
      "requested_ref": "v0.1.0",
      "resolved_commit": "ab12cd34...",
      "pack_update_policy": "locked",
      "files": [
        {
          "role": "active-hook",
          "host": "claude-code",
          "source_path": "scripts/git-destructive-guard.py",
          "input_sha256": "9a8b7c6d...",
          "output_paths": ["~/.claude/hooks/agent-behave/01-git-guard.py"],
          "output_scope": "user-level",
          "effective_update_policy": "locked"
        },
        {
          "role": "active-permission",
          "host": "claude-code",
          "source_path": "settings/permissions.json",
          "input_sha256": "fe09dc...",
          "output_paths": ["~/.claude/settings.json"],
          "output_scope": "user-level",
          "effective_update_policy": "locked"
        }
      ]
    },
    "implement-review": {
      "source_url": "bundled:aa",
      "requested_ref": "bundled",
      "resolved_commit": "bundled",
      "pack_update_policy": "locked",
      "files": [
        {
          "role": "active-skill",
          "host": "claude-code",
          "source_path": "skills/implement-review/",
          "input_sha256": "dir-sha256:1122aa...",
          "output_paths": [".claude/skills/implement-review/"],
          "output_scope": "project-local",
          "effective_update_policy": "locked"
        },
        {
          "role": "generated-command",
          "host": "claude-code",
          "source_path": null,
          "input_sha256": null,
          "output_paths": [".claude/commands/implement-review.md"],
          "output_scope": "project-local",
          "effective_update_policy": "locked",
          "generated_from": "active-skill:implement-review",
          "source_input_sha256": "dir-sha256:1122aa...",
          "template_sha256": "aa-composer-command-v1:7f8e9d...",
          "output_sha256": "b4c3d2e1..."
        }
      ]
    }
  }
}
```

Fields per file entry:
- `role`: one of `passive`, `active-hook`, `active-skill`, `active-permission`, `generated-command`. Distinguishes fetched-then-installed files from composer-generated outputs (like skill command pointers).
- `host`: the host this file targets (e.g., `claude-code`); `null` for passive content.
- `source_path`: path inside the pack source tree; `null` for generated outputs.
- `input_sha256`: hash of the fetched source file; for directory copies (skills), the prefix `dir-sha256:` denotes a merkle-style hash over the directory tree. `null` for generated outputs.
- `output_paths`: list of on-disk paths written (multi-target allowed).
- `output_scope`: `project-local` or `user-level`. Drives which state file (`project` or `user`) owns the entry.
- `effective_update_policy`: per-entry resolution of `pack_update_policy` plus any overrides. Active entries with `auto` are rejected at parse time.
- `generated_from` (generated-command only): references the active-skill entry that produced this output.
- `source_input_sha256` (generated-command only): copy of the referenced active entry's `input_sha256` at the time the output was generated. Drives re-generation when the source entry's source changes.
- `template_sha256` (generated-command only): identifier + hash of the composer's internal generation template (versioned as `aa-composer-<template-name>-<version>`). Drives re-generation when the composer's pointer template itself changes across aa releases.
- `output_sha256` (generated-command only): hash of the rendered on-disk output. Drives drift detection against the current file.

The composer reads this file on every bootstrap; mismatch between recorded `input_sha256` and current upstream content, or between recorded `resolved_commit` and current source tip, triggers either the `locked` fail-closed path or the `auto` refresh path depending on `effective_update_policy`. For `generated-command` entries, re-generation fires when any of `source_input_sha256`, `template_sha256`, or `output_sha256` no longer matches reality; unchanged inputs produce byte-identical outputs with no re-write.

**Consumer opt-in syntax**:

```yaml
# agent-config.yaml at consumer project root
packs:                          # new unified field (v0.4.0+)
  - agent-style                 # short form: name only; look up in manifest

  # ----- v0.5.0+ only: private sources -----
  - name: my-lab-writing
    source:
      url: ssh://git@github.com/yzhao062/private-writing
      ref: main
      path: rule-pack.md
      auth: ssh                 # disables anonymous fallback; required for private
  - name: nsf-helper
    source:
      url: https://api.github.com/repos/yzhao062/nsf-helper/tarball/v0.2.0
      auth: GITHUB_TOKEN

rule_packs:                     # legacy alias; accepted through v0.6.x,
  - agent-style                 # hard-fail at v1.0.0; warning on use from v0.4.0
```

**User-level config layer**:

A user-level config file carries pack selections that can be managed one time for the current OS user ("one time, all projects"). In v0.4.0 the file is CLI-writable via `anywhere-agents pack add/remove/list`, and `scripts/packs/config.py` implements the full four-layer precedence described below; consumer bootstrap in `scripts/compose_packs.py` still resolves selections through the legacy project-tracked / project-local / env path. Adopting the new resolver so user-level entries drive consumer bootstrap is a v0.4.x follow-up. The file is optional; consumers that never create one behave exactly per the project-level-only design in the block above.

**Path**:

- POSIX: `$XDG_CONFIG_HOME/anywhere-agents/config.yaml` when `$XDG_CONFIG_HOME` is set and non-empty, else `$HOME/.config/anywhere-agents/config.yaml`.
- Windows: `%APPDATA%\anywhere-agents\config.yaml`.
- When neither `$HOME` nor `%APPDATA%` is set, CLI `pack add` / `pack remove` fail with an actionable error ("user-level config home not resolvable; set $HOME or $XDG_CONFIG_HOME"). In v0.4.0 consumer bootstrap does not yet read the user-level file, so there is no separate composer-side fallback path to invoke here; bootstrap continues to resolve selections through the legacy project-tracked / project-local / env path. The composer fallback + stderr note described below activates when `scripts/compose_packs.py` adopts the new 4-layer resolver in v0.4.x.

**Precedence (implemented in `scripts/packs/config.py`; bootstrap consumption deferred in v0.4.0 → v0.4.x)**:

1. User-level (base list).
2. Project tracked (`<project>/agent-config.yaml`).
3. Project local (`<project>/agent-config.local.yaml`).
4. `AGENT_CONFIG_PACKS` env var (transient additive overlay).

**Merge semantics**:

- Different pack names across layers: union (all appear in the final list).
- Same pack name at different layers: the more-specific layer overrides for all fields (`ref`, `skills-path`, etc.).
- Explicit opt-out (`packs: []` at any layer, plus legacy `rule_packs: []` during the v0.4.0–v0.6.x alias window): **clears all earlier-in-precedence layers** for that list. Later layers (env var) MAY still add. Project-level `packs: []` suppresses user-level and project-tracked entries for that project; env-var additions still apply. A consumer who wants zero packs regardless of env must also ensure the env var is unset in the invocation context (e.g., omit it in CI config).

**CLI `anywhere-agents pack ...`**:

Target workflow: "I have a private pack and I want it available in every project I bootstrap, with update behavior governed by the pack's `update_policy`." Writes target the user-level file only; project-level configs are never touched by these commands. The CLI always writes the unified `packs:` key. It never creates `rule_packs:`; that key is read as a legacy alias only.

```bash
# One-time mount of a private skill pack at user level (default --type skill):
anywhere-agents pack add git@github.com:me/private-skills.git

# With all available flags:
anywhere-agents pack add <source> \
    [--type skill|rule]            # defaults to skill
    [--ref REF]                    # defaults to main
    [--name NAME]                  # override derived pack name
    [--skills-path PATH]           # override default 'skills/'

anywhere-agents pack list                    # both types, user + cwd project merged
anywhere-agents pack list --type skill       # filter to one type

anywhere-agents pack remove <name-or-source> [--type skill|rule]
# --type is required only when a skill pack and a rule pack share the same name/source
```

CLI contract:

- `pack list` merges user-level + cwd project-level and labels each entry with its source layer.
- Default `ref: main` is a convenience default for branch tracking, not an auto-update guarantee. Active entries still honor `update_policy: locked`: if `main` resolves to changed active content, bootstrap fails closed and reports the new resolved commit until the user explicitly approves or pins a reviewed ref. Passive-only entries may opt into automatic refresh through manifest `update_policy: auto`.
- Idempotent on duplicate source; different `--ref` on an existing source updates the ref in place with a stderr notice.
- Credential-URL rejection before any file write (see Auth safety preconditions below).
- **First CLI add default preservation**: `pack add <src>` of either type into an empty or absent user-level `packs:` list auto-seeds the list as `[{name: agent-style}, {user pack}]` so the v0.3.0 default pack is not silently replaced by the first user-level write. Subsequent `pack add` operations append only. Users who explicitly want to drop `agent-style` globally run `pack remove agent-style --type rule`. Hand-editing user-level `packs:` remains subject to replacement semantics; the CLI is the recommended path. If a legacy user-level `rule_packs:` key exists, `pack add` / `pack remove` first normalizes it in memory to unified `packs:` semantics, then writes back only `packs:`.
- Atomic write: temp file + `os.replace`-style rename in the same directory. Interrupt mid-write leaves no partial file.
- Malformed-YAML safety: if the existing user-level file cannot be parsed, `pack add` / `pack remove` refuses to rewrite, prints the exact path and parse error to stderr, and exits non-zero. The file bytes stay unchanged.

**Env var grammar**: `AGENT_CONFIG_PACKS="name1,-name2"` accepts manifest names only, comma-separated. Subtract prefix `-` removes a pack from the resolved selection (Round 2 env-var decision). Direct-source entries are not supported in the env var because shell quoting of URLs with `&` / `/` across bash and PowerShell is fragile. Consumers who need transient direct-source use a temp project-local config.

**Auth safety preconditions**:

Before any network call in the auth chain below, the composer enforces two safety preconditions:

1. **Reject secret-bearing `source:` URLs** in every config layer (user-level, project-tracked, project-local). For HTTP(S), any userinfo component is rejected (`https://user@host/...`, `https://user:password@host/...`, or `https://<token>@github.com/...`). For SSH, the standard transport usernames in `git@host:path` and `ssh://git@host/path` are allowed because they are not credentials; SSH URLs are rejected only if they embed password-like secret material. Rejection happens at parse time, before any network call, with: "credentials in a URL are unsafe in config; use `git@` SSH, `gh auth login`, or `GITHUB_TOKEN` env instead." `AGENT_CONFIG_PACKS` is names-only; direct-source input there is rejected by env grammar before URL validation runs.

2. **Set noninteractive fetch env** on the composer subprocess: `GIT_TERMINAL_PROMPT=0` (HTTPS does not open a password prompt) and `GIT_SSH_COMMAND=ssh -o BatchMode=yes -o ConnectTimeout=10` (SSH does not hang on missing keys or unknown-host prompts). Failures surface a clear error within the connect-timeout window instead of a hung bootstrap.

**GitHub URL normalization (`github.com` only)**: for the exact host `github.com`, the composer extracts the canonical `<owner>/<repo>` identity regardless of URL form (`git@github.com:<owner>/<repo>.git`, `https://github.com/<owner>/<repo>.git`, `ssh://git@github.com/<owner>/<repo>.git`). After extraction, all four auth methods become applicable by identity rather than URL shape. `pack add git@github.com:me/private.git` on a Windows machine with no working SSH agent but with `gh auth status` OK still succeeds via gh CLI: the composer tries SSH (fails quickly under `BatchMode=yes`), normalizes to `me/private`, then tries gh CLI which succeeds. Normalization applies only to `github.com`; GitHub Enterprise hosts (`github.mycompany.edu`, etc.) and any other remote continue to gate the method by URL shape. Enterprise support is out of scope for v0.5.0 to keep the auth surface bounded; adding it later means calling `gh auth status -h <host>` and running gh commands with `--hostname <host>`.

**Auth chain** (v0.5.0+): tried in order per source URL: SSH agent → `gh` CLI token → `GITHUB_TOKEN` env → anonymous. First success wins. Explicit `auth: <method>` on a source disables the fallback chain (prevents a silent anonymous fallback from succeeding against a public repo of the same path). v0.4.0 does not run the auth chain; private entries are rejected at parse time.

## Pack lifecycle operations

Pack lifecycle state is **split by ownership boundary**. Two different files record two different classes of output; a third file records source provenance.

- **`.agent-config/pack-lock.json`** (project-local). Records the selected packs for this consumer repo, the declared source URL and ref, the resolved commit id, and sha256 values for every input file used to compose this repo. Schema above. Gitignored automatically.
- **`.agent-config/pack-state.json`** (project-local). Records project-local outputs: `AGENTS.md` begin/end marker blocks, `.claude/skills/<name>/` directories, `.claude/commands/<name>.md` pointers, and any files written under the consumer repo. One entry per output path with pack attribution and sha256.
- **`~/.claude/pack-state.json`** (user-level). Records shared user-level outputs: files under `~/.claude/hooks/<pack>/` and entries merged into `~/.claude/settings.json`. Each output is keyed by `(kind, absolute_target_path)`. The entry carries an `owners:` list whose items are full records of the form `{repo_id, pack, requested_ref, resolved_commit, expected_sha256_or_json}`. A second repo may **join** an existing user-level entry only when the target path **and** the expected content match byte-for-byte. A repo's uninstall removes its owner record from the list; the physical hook file or settings entry is deleted only when the `owners:` list becomes empty **and** the current on-disk content still matches the recorded value.

**Same-path / different-content conflict** (Round 3 decision): when a second repo tries to install a user-level output at the same target path with a **different** expected content (e.g., repo A has `agent-behave@v0.1.0` and repo B requests `agent-behave@v0.1.1`, both targeting `~/.claude/hooks/agent-behave/01-git-guard.py`), composition fails closed with `user-level-output-conflict`. The error surfaces the existing owners (repo ids, resolved commits) and the requested ref; no file is overwritten, no `owners:` merge is attempted, the installing repo receives no partial installation for that entry.

**Side-by-side version opt-in syntax** (Round 4 clarification): packs whose authors want multiple versions to coexist declare **versioned target paths** using two template variables that the composer substitutes at install time:

- `{pack}` → the pack name (from manifest `name:`).
- `{resolved_commit}` → the full resolved commit id (40-char hex) from `pack-lock.json`.

Example manifest fragment for a pack that opts into side-by-side:

```yaml
- name: agent-behave
  active:
    - kind: hook
      hosts: [claude-code]
      files:
        - from: scripts/git-destructive-guard.py
          to: ~/.claude/hooks/{pack}/{resolved_commit}/01-git-guard.py
      ...
```

Composed path with `resolved_commit = ab12cd34...`: `~/.claude/hooks/agent-behave/ab12cd34.../01-git-guard.py`. Repo A at v0.1.0 and repo B at v0.1.1 install to distinct directories, each with its own `owners:` list entry; neither conflicts with the other. The composer rejects unknown template variables at parse time.

Named slot support (arbitrary consumer-declared slot names with pack-documented conflict policy) is **deferred to a later release**. v0.4.0 shipped only the two template variables above plus the default fail-closed singleton behavior for any path without templating. The default singleton hook / settings target never merges owners across different content. The composer refuses to reason about user intent on its own.

**Atomicity contract** (recoverable staged transaction, not atomic directory swap). Cross-platform atomic directory replacement is not a reliable primitive: POSIX `rename(2)` atomicity on directories requires the target to be empty; Windows `MoveFileEx(MOVEFILE_REPLACE_EXISTING)` does not work on non-empty directories; antivirus, Python, or Claude Code may hold file handles that block rename. The contract below is "recoverable staged transaction" — the composer can always reconcile a partial state on the next run, and per-file atomic rename is the only primitive relied on.

All lifecycle writes follow this pattern (primitives shipped in v0.4.0; composer-side outer lock acquisition and automatic startup reconciliation wiring activate in v0.4.x):

- In the full lifecycle design, composer-side writes acquire a **per-user lock** (`~/.claude/.pack-lock.lock` via `flock` on POSIX, `msvcrt.locking` on Windows) before touching `~/.claude/pack-state.json`, `~/.claude/hooks/`, or `~/.claude/settings.json`. The lock helper (`scripts/packs/locks.py`) shipped in v0.4.0 and is used by the uninstall engine; composer-side invocation around the compose transaction is the v0.4.x wiring follow-up.
- In the full lifecycle design, composer-side writes acquire a **per-repo lock** before touching `.agent-config/pack-lock.json` or `.agent-config/pack-state.json`. Same "helper shipped in v0.4.0 / composer wiring in v0.4.x" split as the per-user lock.
- For every transaction (install, update, uninstall, re-stamp), write a `transaction.json` under a transaction-scoped staging directory: `~/.claude/hooks/<pack>.staging-<txn_id>/` for user-level hook-layout changes, `.agent-config/<txn_id>.staging/` for project-local. `transaction.json` records intent: the set of pending file writes, the set of state-file entries that must update, pre-state hashes (for rollback verification), and the target commit state.
- Stage every output to a sibling temporary path, `fsync`, then **atomic-rename per file** (`os.replace` on Python; maps to POSIX `rename(2)` for regular files and Windows `MoveFileEx(MOVEFILE_REPLACE_EXISTING)`).
- After all per-file renames succeed, update `pack-state.json` (project or user, per scope) using the same write-temp-then-rename pattern.
- On completion, delete the transaction staging dir and `transaction.json`.
- **Startup reconciliation design**: the orphan classifier (`scripts/packs/reconciliation.py`) shipped in v0.4.0. v0.5.0 Phase 7 added the `reconcile_orphans` orchestrator wrapper (also exposed under `scripts/packs/reconciliation.py`) that the composer calls before the main compose step. The wrapper scans `~/.claude/hooks/*.staging-*` and `.agent-config/*.staging/` for orphan transaction dirs, acquires the same per-user and per-repo locks before scanning or writing, and skips transactions whose owning process is still live (its PID is holding the relevant lock). For each true orphan, the wrapper reads `transaction.json`, compares on-disk content against pre-state hashes, and either rolls back, rolls forward, or surfaces a drift report. The composer's bootstrap entry path invokes `reconcile_orphans` at startup; the underlying classifier remains independently unit-tested.
- Hook filename re-stamping (consumer `hook_order:` changes) uses the same staged-transaction contract. The transaction primitives shipped in v0.4.0; automatic recovery of a crashed re-stamp on next bootstrap is deferred until the v0.4.x reconciliation wiring lands.
- On write failure before commit, roll back files whose hashes still match the transaction's pre-state; leave files with unexpected content alone and surface a drift report.

**Lock contention and cross-process safety**: the lock helper and 30-second timeout contract shipped in v0.4.0 and are used by the uninstall engine. Bootstrap-side concurrent-composer serialization is a v0.4.x follow-up, because `scripts/compose_packs.py` does not yet acquire the outer per-user / per-repo locks around the compose transaction.

**Three explicit operations**:

- **install or update**: v0.4.0 single-process composition stages every project-local and user-level output through the transaction layer (per-file atomic rename) and writes the split state files. If an update sees changed commit or sha256 on an `update_policy: locked` active entry, fail closed and surface the delta for explicit approval. Outer lock acquisition and automatic orphan reconciliation on next bootstrap are deferred to v0.4.x; hook filename re-stamping follows the same deferral.
- **uninstall**: the internal uninstall engine shipped in v0.4.0 and backs `anywhere-agents uninstall --all`, including the six-outcome contract (clean / no-op / lock-timeout / drift / malformed-state / partial-cleanup), ownership-aware cleanup, and fail-closed drift handling (drifted files skipped, state files untouched for safe retry).
- **rollback to ac** (or to a different upstream): remains the intended lifecycle operation, but the fully wired bootstrap-side rollback / recovery path is only complete once the deferred composer-side lock + reconciliation wiring lands in v0.4.x. `docs/ac-to-aa-migration.md` Path 1 still invokes the uninstall path internally; **Path 2 (`nuke and reinstall`) still must run `anywhere-agents uninstall --all` first when active packs are present**, since deleting `.agent-config/` alone is cache cleanup only and leaves user-level hooks / settings behind.

These operations share one design target, but v0.4.0 did not wire every part of that target into `scripts/compose_packs.py`. The release shipped transaction primitives, split state files, and the uninstall engine; bootstrap-side concurrent-composer protection and automatic startup reconciliation are v0.4.x follow-up work.

**CLI contract for `uninstall --all`** (called by `docs/ac-to-aa-migration.md` Path 2 pre-step):

The canonical invocation is `anywhere-agents uninstall --all`. Both the PyPI distribution (`pipx run anywhere-agents uninstall --all` or the installed `anywhere-agents` entry point) and the npm distribution (`npx anywhere-agents uninstall --all`) expose this exact command with identical semantics.

Exit code contract:

| Condition | Exit | Behavior |
|---|---|---|
| `.agent-config/pack-state.json` absent OR present-but-empty | 0 | no-op; print "no packs to uninstall"; safe to re-run |
| All packs uninstall cleanly; state files consistent after | 0 | state files updated; orphan staging cleaned; print per-pack summary |
| Lock timeout (per-user or per-repo lock held) | 10 | print lock holder PID if available; no state change |
| Drift detected (on-disk content neither pre-state nor expected) | 20 | print drift report with affected paths; abort; leave files in place; state files unchanged |
| Malformed state file (parse error) | 30 | print parse error; refuse to proceed; suggest manual inspection |
| Partial cleanup (some packs failed mid-operation) | 40 | roll back applied changes where safe; surface still-dirty packs; subsequent run resumes |

Idempotence: exit 0 on consecutive invocations when there is nothing left to clean. Path 2 in the migration runbook must check `exit == 0` before proceeding to `rm -rf .agent-config/`; any nonzero exit aborts Path 2 with the `anywhere-agents` output as the explanation.

The `ONBOARDING.md` release-runbook cheat-sheet gains a post-release verification covering: install smoke, uninstall-is-idempotent smoke, reorder smoke (consumer `hook_order:` override regenerates prefixes without breaking state), rollback smoke, and **two-repo shared-user-hook smoke** (two scratch consumer repos install the same pack, repo A uninstalls, assert repo B's hooks survive). These run on Windows and Spark Ubuntu against every release that changes active-entry dispatch, parallel to the existing Claude-Code-driven end-to-end smoke.

## Release sequence (detailed)

### aa v0.4.0 — Unified manifest (BC-preserving, public-source only)

**Scope decision (Option A after plan-review Round 1)**: v0.4.0 is schema unification on **public** sources only. The auth chain and private-source support move entirely to v0.5.0. Avoids a half-working state where v0.4.0 would parse private config without fetching it.

- Rename `bootstrap/rule-packs.yaml` to `bootstrap/packs.yaml`; keep the old filename as a loader alias (both paths read, deduped, unified into internal state).
- Add `active:` field support in the manifest schema with four kinds (`hook`, `skill`, `permission`, `command`). Accept both old (passive-only, public) and new shapes.
- Introduce `kind:`, `hosts:`, `required:`, `files: [{from, to}]` as required active-entry fields; v0.4.0 supports `hosts: [claude-code]` only.
- Non-claude-code hosts: `required: true` entries fail composition with a `host-mismatch` error; `required: false` entries skip with an info log. Default is `required: true`.
- `kind: command` entries are parsed and warned (`no-op at v0.4.0; full support in a later release`) rather than errored — forward-compatibility slot.
- `agent-config.yaml` schema accepts `rule_packs:` (legacy, passive-only) and `packs:` (new, both slots, public source only). `rule_packs: []` opt-out continues to work verbatim. **Note:** v0.4.0 ships schema acceptance and the legacy `rule_packs:` consumption path against names registered in `bootstrap/packs.yaml` only. Bootstrap-active consumption of `packs:` and inline-`source:` third-party fetches (i.e., a consumer naming a public GitHub repo not registered in the bundled manifest) lands in v0.5.0 alongside the auth chain. Consumers who try to bootstrap-load `agent-pack`-style third-party packs in v0.4.0 either copy the passive bodies into `AGENTS.local.md` or register the names in their own bootstrap-manifest fork. The v0.4.0 → v0.5.0 release sequence below tracks this explicitly so the gap closes in one coherent release rather than half-shipping in v0.4.x.
- Existing `agent-style` pack: remanifest with passive slot only. Its current banned-word enforcement remains inside `aa`'s built-in `guard.py` for this release (extraction is a v1.0 step).
- **Pack-emitted command pointers**: the four `aa`-shipped skills (`implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`) remanifest as `kind: skill` entries that auto-emit their `.claude/commands/<name>.md` pointer on install. The 4 static pointer files **left the STRICT parity list** in v0.4.0 because they are now outputs of the composer, not aa-core source files. `scripts/check-parity.sh` and `docs/anywhere-agents.md` "what gets copied" table update in the same release. See STRICT trajectory table below.
- Write `.agent-config/pack-lock.json` and `.agent-config/pack-state.json` on install; write `~/.claude/pack-state.json` for every active entry touching user-level paths. `update_policy: locked` enforced from day one.
- Lifecycle primitives shipped in v0.4.0: the transaction journal + staging dir + per-file atomic rename (`scripts/packs/transaction.py`), the uninstall engine with six typed outcomes and CLI exit codes (`scripts/packs/uninstall.py`), the cross-platform lock helper (`scripts/packs/locks.py`), and the orphan classifier (`scripts/packs/reconciliation.py`). Composer-side lock acquisition around the compose transaction and automatic startup reconciliation wiring move to v0.4.x; v0.4.0 single-process composition is protected by the transaction layer's per-file atomic rename but not by the outer lock + reconciliation layer. The `anywhere-agents uninstall --all` CLI still maps to the full six-exit-code contract via the internal engine.
- Ship `scripts/compose_packs.py` alongside `compose_rule_packs.py`; old script delegates. `compose_rule_packs.py` stays in STRICT parity list until the delegation is final.
- Private-source config entries are rejected at parse time with a "v0.5.0 feature" error (not silently ignored).
- Update `ONBOARDING.md` "Release cut" cheat-sheet: add `scripts/compose_packs.py` to the pre-tag real-agent-smoke coverage; add pack-lock integrity smoke, two-repo shared-user-hook smoke, reorder smoke, rollback smoke.

**Consumer-facing change**: none. Fresh v0.4.0 install on an unmodified consumer produces byte-identical `AGENTS.md` to v0.3.2; command pointers that used to be static copies now appear as composer outputs with the same content.

**Bootstrap compat**: post-2026-04-17 caches self-update via the sparse-clone tail; pre-2026-04-17 caches need the existing `MIGRATIONS.md` 2026-04-17 entry (already in place). No new MIGRATIONS.md entry required IF `bootstrap.{sh,ps1}` and the sparse-checkout spec stay unchanged. If either changes (e.g., sparse-checkout adds a new path for the new manifest filename, `pack-lock.json` placement, or the user-level `~/.claude/pack-state.json`), add a new MIGRATIONS.md entry.

**STRICT parity**: 4 shipped command pointers (`.claude/commands/{implement-review,my-router,ci-mockup-figure,readme-polish}.md`) **drop from STRICT list** as they become pack-emitted outputs. `rule-packs.yaml` stays (as alias); `packs.yaml`, `pack-lock.json`, and `pack-state.json` are aa-only content (not mirrored to ac since ac does not ship a composer). `docs/anywhere-agents.md` mirror policy table updates to reflect this reclassification.

### as v0.4.0 — Slim variants (coordinated; may ship before or after aa v0.4.0)

- Author `docs/rule-pack-field.md` (nine field-observed rules, RULE-A..I; hand-synced with the RULE-A..I section of `RULES.md`). Estimated size: 35-40k chars.
- Author `docs/rule-pack-lite.md` (21 directives + banned-word list; drops BAD/GOOD examples and rationale). Estimated size: 10-15k chars.
- Add release-time drift check (byte-identical mirror of the source section of `RULES.md`) to the `as` release runbook.
- `aa`'s manifest gains two entries: `agent-style-field` and `agent-style-lite`, both pointing at the new `as` doc paths.

**aa default selection**: still `agent-style` (full) at v0.4.0 ship. Default switch is a separate release (see below).

### aa v0.4.x — Default switch

- Change `DEFAULT_SELECTIONS` from `[{"name": "agent-style"}]` to `[{"name": "agent-style-field"}]`.
- Fresh installs produce a `CLAUDE.md` under the 40k warning threshold.
- Existing consumers with no `packs:` / `rule_packs:` override see a visible size change. Users who want the full pack pin via `packs: [agent-style]` or `rule_packs: [agent-style]`.

**Consumer-facing change**: visible. CHANGELOG highlights and release notes flag this.

**ac-to-aa-migration.md update**: the "Opting out of the default agent-style rule pack" section needs a parallel "Pinning the full pack" subsection for consumers who preferred the 21-rule default.

### aa v0.5.0 — Direct-URL packs + private-source release

Two related capabilities land together: bootstrap-active consumption of inline `source:` URLs in `agent-config.yaml` (closes the v0.4.0 schema-vs-consumption gap), and the auth chain that makes private-source URLs work alongside public-source URLs through the same code path. No half-shipped state before v0.5.0.

- **Direct-URL packs (public source).** `agent-config.yaml` `packs:` (and legacy `rule_packs:` for passive-only) entries with an inline `source: { repo: ..., ref: ... }` are bootstrap-active. The composer fetches the named pack from its source URL anonymously; manifest-registration in `bootstrap/packs.yaml` is no longer required for third-party packs. This is what the v0.4.0 schema already accepted; v0.5.0 finally consumes it. **`yzhao062/agent-pack` becomes loadable end-to-end via `agent-config.yaml`** as the v0.5.0 acceptance test (one-step migration replaces today's manual `AGENTS.local.md` copy).
- **Auth chain (private source).** SSH agent → `gh` CLI token → `GITHUB_TOKEN` env → anonymous. Auth chain tests against each private URL at compose time; fails closed on `auth: <method>` when the named method does not succeed.
- Parser accepts private source entries (removes the v0.4.0 rejection).
- Apply pack-lock integrity to private sources identically: resolve to commit id, record sha256, enforce `update_policy: locked` on active items.
- Paper / proposal / submodule repos can now consume private packs. The `docs/ac-to-aa-migration.md` decision matrix "Paper repo → stay on ac" row collapses to "Paper repo → aa + private pack". This release is the payoff for Q2.

**Why direct-URL packs are bundled with the auth chain (not extracted to v0.4.x):** the public-source path and the auth-chain path share one composer entry point that fetches per-pack from a URL. Shipping public-only without the auth chain duplicates code that the auth chain immediately replaces. Shipping the auth chain without the public path leaves the same `unknown rule pack` error standing for `yzhao062/agent-pack`-style consumers. Both land together so the composer touches each fetch site once.

**Consumer-facing change**: new capability only; no behavior change for existing consumers who do not declare private packs.

**Bootstrap compat**: if `bootstrap.{sh,ps1}` gains auth-chain plumbing (ssh / gh / token resolution), it is a bootstrap-script change → **new MIGRATIONS.md entry required** for seed-refresh of pre-v0.5.0 bootstrap caches.

**ac-to-aa-migration.md update**: the "Forward direction" section (already updated in the v0.4.0 cycle to point at `docs/pack-architecture.md`) gets its decision matrix updated; "Paper repo → aa + private pack" replaces "stay on ac".

### aa v0.5.1 → v0.5.6 — operational hardening

The v0.5.0 direct-URL release exposed a chain of operational gaps in the AC → AA + AP migration that surfaced only when the CLI ran against real legacy projects, not against the test fixture suite. v0.5.1 through v0.5.5 each closed a specific gap; v0.5.6 corrected an architectural mistake that all five prior versions had inherited.

- **v0.5.1** — `pack verify [--fix]` CLI plus banner pack-deploy check. The banner reads `.agent-config/pack-lock.json` and surfaces gap-count and update-count half-clauses on session start.
- **v0.5.2** — bootstrap auto-runs `pack verify --fix --yes` after the compose step. `pack verify --fix` invokes the composer subprocess after writing config rows, collapsing the prior verify-then-bootstrap dance into one command.
- **v0.5.3** — drift-gate adopt-on-match for pre-existing pack outputs (the composer adopts on-disk files into the lock when content matches expected pack output, avoiding spurious deploy on already-correct state); Phase 1d auto-watch mirror in the `implement-review` skill.
- **v0.5.4** — closes four AC → AA + AP migration gaps in one ship: composer bundled fallback for missing upstream `pack.yaml` (some `agent-style` versions never shipped one); `pack verify --fix` reconciles bundled-default packs (not just user-level entries); `commands/` AC-side moved aside to `commands.bak-<timestamp>/` on migration; user-config self-heal dedup.
- **v0.5.5** — composer resolver migrates from the legacy 3-layer to the 4-layer `config_mod.resolved_for_project` with `force_defaults=True`, so bundled defaults always merge into the resolved selection regardless of project-config presence (the v0.5.4 lock-truncation bug was in this branch). Windows cache cleanup hardened: `os.chmod` retry on read-only `.git/objects/pack/*.idx`, `\\?\` long-path syntax for paths above 260 characters, and `_archive_root` recovery for nested `aa-clone-*` directories left by prior failed cleanup.
- **v0.5.6** — bundles the composer + bundled-default content into the PyPI wheel under `anywhere_agents/composer/`. Closes the v0.5.5 failure mode where the wheel CLI shipped resolver and verify-display fixes but the actual subprocess invocation still ran the user's old composer at `.agent-config/repo/scripts/compose_packs.py`.

#### v0.5.6 architectural change: thick-wheel composer

Prior to v0.5.6 the CLI was a thin shim. `_invoke_composer` invoked `<project>/.agent-config/repo/scripts/compose_packs.py` — the composer cloned by `bootstrap/bootstrap.{sh,ps1}` at last bootstrap. Composer fixes shipped in `scripts/compose_packs.py` reached consumers only when they re-bootstrapped. The wheel-shipped CLI saw the new code; the runtime composer did not. v0.5.5 lock-truncation symptoms persisted on legacy projects despite a green test suite for exactly this reason.

v0.5.6 reverses the layout. The wheel ships its own composer at `anywhere_agents/composer/scripts/compose_packs.py`, plus its own bundled manifest (`composer/bootstrap/packs.yaml`), bundled active-pack source content (`composer/skills/{ci-mockup-figure,implement-review,my-router,readme-polish}/`), and bundled command pointers (`composer/.claude/commands/{4 names}.md`). Two CLI changes deliver this:

- `_bundled_composer_path()` returns the wheel-bundled composer path when `Path(__file__).resolve().parent / "composer" / "scripts" / "compose_packs.py"` exists.
- `_invoke_composer` keeps the project-local "bootstrap first" gate (a project without `.agent-config/repo/scripts/compose_packs.py` still returns rc=2 with `Run bootstrap first`) but switches the executed binary to `_bundled_composer_path() or project_composer`. Bundled wins whenever the wheel ships one.

`compose_packs.py` adds two helpers so the bundled composer reads its own bundled-default content instead of the project-local clone:

- `_composer_source_root()` returns `Path(__file__).resolve().parent.parent` (the directory that owns the running composer script).
- `_is_packaged_composer()` returns True when that source root is named `composer` and its parent is `anywhere_agents`. The two real layouts are unambiguous: wheel install → True (`<site-packages>/anywhere_agents/composer/`), project bootstrap → False (`<project>/.agent-config/repo/`), source-repo dev run → False (`<repo>/`).

When `_is_packaged_composer()` is True, `_resolve_manifest_path` prefers `composer/bootstrap/packs.yaml` over the project's stale `.agent-config/repo/bootstrap/packs.yaml`, and `_build_ctx` reads bundled active-pack file sources from `_composer_source_root()` instead of `<project>/.agent-config/repo/`.

The bundled composer is an execution-path replacement, not a bootstrap replacement. `bootstrap/bootstrap.{sh,ps1}` continues to clone the source repo into `.agent-config/repo/`; that clone provides the project signal (without it, the CLI fails fast) and the source for remote-fetched packs (the auth chain still pulls from public/private remotes per `agent-config.yaml`).

**STRICT parity (new aa-internal mirror)**: `scripts/compose_packs.py`, `scripts/compose_rule_packs.py`, `scripts/packs/*.py`, `bootstrap/packs.yaml`, `skills/{4 shipped names}/`, and `.claude/commands/{4 shipped names}.md` now have a wheel-bundled mirror at `packages/pypi/anywhere_agents/composer/`. The mirror must be byte-identical to the source tree (excluding `__pycache__/`). Drift produces a wheel that disagrees with the bootstrap clone — exactly the v0.5.6 fix is meant to prevent. As of v0.5.6 this is a manual release-gate check (run `diff -rq` between source and mirror trees before tagging); a follow-up release (v0.5.7 or v0.6.0) lands the aa-internal STRICT block in `scripts/check-parity.sh`.

**Consumer-facing change**: `pipx install --force` to v0.5.6+ delivers composer fixes to existing bootstrapped projects without re-bootstrap. Bootstrap from scratch is unchanged.

**Lesson learned**: shipping a fix in `scripts/compose_packs.py` alone does not deliver it to existing consumers. v0.5.0 through v0.5.5 each shipped fixes that the test suite confirmed and the legacy-project runtime did not see. The post-code smoke contract therefore extends with: validate every composer fix by `pipx install --force <new-wheel>` against an existing legacy project (an actual project, not a synthetic fixture), then run `pack verify --fix` and inspect the lock. If the lock state matches expectation, the fix is delivered; otherwise the wheel is the source of the disagreement, not the source tree. This check is now item 27 in the post-code smoke list below.

### ab (`agent-behave`) v0.1.0 — First multi-component pack

- Standalone repo, PyPI-published, parallel release flow to `agent-style` (same 12-section runbook pattern).
- First pack with all three active slot kinds (hook files, permissions, passive text).
- Logically separate from `aa` and `as`: new release stream.

**`ac` / `aa` impact**: none at this release — `aa`'s built-in `guard.py` still handles git / gh / compound-cd checks. `ab` is an opt-in addition, not a replacement.

### aa v0.6.0 — Noise audit

- Walk existing guards; demote `decision: deny` to `decision: ask` where the combination `false-positive-risk: high + impact-if-allowed: low|medium` holds. Trigger rate alone is not the criterion: a high-frequency, precise-match, harmful-action check may stay `deny` if false positives are rare and the impact of allowing is high (e.g., destructive git). Known demotion candidates: writing-style hook (high FP, low impact allowed), compound-cd hook (high FP, medium impact allowed).
- `compose_packs.py` enforces a noise budget at install time using the full criterion above. Warns (or refuses with explicit override) when a combined install produces more than N `high-FP + low/medium-impact + deny` entries; users can override per pack via `decision-override: deny` in `agent-config.yaml`.
- Per-guard escape hatch env vars: `AGENT_STYLE_HOOK=off`, `AGENT_BEHAVE_HOOK=off`, etc. The blanket `AGENT_CONFIG_GATES=off` stays as the emergency switch.
- **Update-UX revisit (open scope; specifics decided in v0.6.0 plan-review).** v0.5.6 closed the wheel-delivers-fix gap, but the day-to-day pack-update flow is still split across multiple commands with partially-documented policy semantics. v0.5.x shipped the primitives (`update_policy: {locked, prompt, auto}`, `pack update`, `pack verify --fix`, `latest_known_head` drift detection in the banner) and deliberately deferred the UX layer that ties them together. Items to settle in v0.6.0:
  - Should `pack verify --fix` apply `prompt`-policy drift inline, or stay as the "compose to current lock" path while `pack update` remains the only apply route? Current behavior is a partial mix that is not documented in the quickstart.
  - Should the banner's `ℹ N pack update(s) available` line gain a single follow-up command (e.g., `pack update --all` or `pack verify --fix --apply-drift`)?
  - Should the bundled-default `update_policy: locked` change for one or both of `agent-style` / `aa-core-skills`? Locked is correct for `aa-core-skills` (active code, hooks, skill content). For `agent-style` (passive text only) the wheel already ships a pinned ref, so user-side `prompt` may add redundant drift noise without protecting anything the wheel does not already pin.
  - Should `pipx upgrade anywhere-agents` (or an equivalent self-update check) run as a banner item or session-start hint, or stay strictly out of consumer-facing commands? The "wheel upgrade is a separate maintainer action" boundary is the conservative default; the v0.6.0 review tests whether that holds when the typical user is the maintainer's three-legacy-project + new-project set rather than a public consumer.
  - Should `update_policy: auto` remain accepted on active entries, and if so what UX guardrail should explain or constrain it? v0.5.0 removed the parse-time rejection (see `scripts/packs/schema.py` and `tests/test_packs_schema.py::test_active_entry_accepts_auto_policy`), but the Decisions / Round 1 section of this doc and the v0.4.0 churn-semantics paragraph still describe `auto` as passive-only. v0.6.0 should reconcile the docs, tests, and safety story: either keep active `auto` with explicit trust semantics and updated docs, or reintroduce a deliberate rejection with matching tests and migration notes.

  Concrete reproduction (usc-slides, 2026-04-28): `pack verify` printed "ℹ 1 pack(s) have updates available (run `pack verify --fix` to apply)" for an `agent-pack @ main` entry where `latest_known_head` differed from `resolved_commit`. `pack verify --fix` then printed "--fix: nothing to repair" because `_pack_verify_fix` only reruns the composer when packs are in `bad` state, and `prompt`-policy drift on a `deployed` pack is not `bad`. The actual apply route for prompt-policy drift is `pack update <name>`. The misleading message lives at `packages/pypi/anywhere_agents/cli.py:2069-2070`. This is the real-world version of Q1 above and the strongest single piece of evidence for why v0.6.0 must collapse the verify / `--fix` / `pack update` split into a single coherent flow before introducing more update primitives.

  Out of scope for v0.5.x because the v0.5.0 → v0.5.6 chain was already operational hardening of the install path, and bundling a UX overhaul into the same window would have lost the "one visible concern per release" discipline that the Round 1 decisions established.

- **Rule-pack size budget (cross-repo, blocked on agent-style v0.3.3).** Real consumer `CLAUDE.md` files reach 120-140k chars and trigger Claude Code's 40k size warning, with the agent-style rule pack alone contributing ~65% of the total. agent-style v0.3.3 will ship a `docs/rule-pack-compact.md` alongside the full file (issue tracker: yzhao062/agent-style#6). Once that lands, aa v0.6.0 flips `bootstrap/packs.yaml` so the agent-style entry's `from:` field points at the compact file. Consumers who want the full inline content override the `from:` field per-project in their own `agent-config.yaml`. The change is one line in `bootstrap/packs.yaml`; no `style: compact|full` schema knob is added.

**Consumer-facing change**: visible. Users who previously saw silent `deny` on compound-cd / banned-word writes will now see `ask` prompts. CHANGELOG highlights. Update-UX changes (if any land in v0.6.0) are also CHANGELOG-visible.

**Budget gate scope**: after demotions, `aa`'s own defaults have no `high-FP + deny` entries left, so the budget gate mainly serves third-party packs. It still exists as the guardrail that prevents a bundled pack install from accidentally stacking several noisy `deny` hooks.

**STRICT parity**: `guard.py` is STRICT byte-identical between ac and aa. Noise-audit changes land in both. `check-parity.sh` continues to enforce byte-identical until v1.0 extraction.

### aa v1.0.0 — Full decoupling

- `guard.py`'s git / gh / compound-cd logic extracts into `agent-behave`.
- `aa` core keeps only banner + session-event plumbing in `guard.py` (or renames to `banner-guard.py`).
- `DEFAULT_SELECTIONS` covers `agent-style-field` + `agent-behave` (both default-on for opinionated install; easy opt-out via `packs: []`).
- STRICT parity list **drops** `guard.py` (since most of the content is no longer in `aa` core); `check-parity.sh` and the `ONBOARDING.md` STRICT-category list update in sync.
- `ac`'s `scripts/guard.py` is either removed (if ac becomes pure text content) or kept as a pinned-version compatibility copy for consumers still bootstrapping from ac (paper repos not yet migrated).

**Consumer-facing change**: visible. Users who relied on aa-bundled git safety need `packs: [agent-behave]` to retain it (or it is default-on and they only notice the namespacing change).

**Bootstrap compat**: if `bootstrap.{sh,ps1}` changes, new MIGRATIONS.md entry. Otherwise consumer bootstrap caches self-update.

## Per-release maintainer-doc impact

Summary of which maintainer docs change per release:

| Release | `MIGRATIONS.md` | `ONBOARDING.md` (STRICT list + runbook) | `docs/ac-to-aa-migration.md` |
|---|---|---|---|
| aa v0.4.0 | New entry only if `bootstrap.{sh,ps1}` or sparse-checkout spec changes | Add `compose_packs.py` to release-smoke coverage; no STRICT change | Add note that `packs:` is the new opt-in; `rule_packs:` continues to work |
| as v0.4.0 | None (no bootstrap touch) | None | None |
| aa v0.4.x default switch | None | None | Add "Pinning the full pack" subsection under opt-out |
| aa v0.5.0 | **New entry required** (auth-chain plumbing in bootstrap) | Update "Claude-Code-driven end-to-end install tests" to cover private-source packs on Windows + Spark | Rewrite "Forward direction" section, replace PLAN-skill-pack-composition.md reference with pointer to this doc, collapse "Paper repo → stay on ac" matrix row |
| aa v0.5.1 → v0.5.6 | None (no bootstrap script change) | Document manual aa-internal mirror gate; extend post-code smoke contract with item 27 (`pipx install --force` validation against an existing legacy project). aa-internal STRICT block in `scripts/check-parity.sh` deferred to v0.5.7 / v0.6.0. | None — but `docs/anywhere-agents-quickstart.md` lands as the maintainer-internal install / verify cheat sheet for v0.5.6+ |
| ab v0.1.0 | None | None | Optional: add `agent-behave` to the examples of ab-available packs |
| aa v0.6.0 | None unless `guard.py` hook wiring changes in bootstrap, **or** the update-UX revisit lands a banner-side self-update hint that needs seed-refresh | Document per-guard escape env vars in "Mechanical Enforcement"; if the update-UX revisit lands, document the decided `pack verify --fix` vs `pack update` split | Update FAQ if consumer-visible prompt behavior changes; update `docs/anywhere-agents-quickstart.md` § "Common gotchas" with the decided update-flow semantics |
| aa v1.0.0 | **New entry required** if `bootstrap.{sh,ps1}` changes for default-pack set | **STRICT list changes**: drop `guard.py` (or rename entry to `banner-guard.py`). Update the mirror table in `docs/anywhere-agents.md`. | Major rewrite: decision matrix collapses further; "what ac keeps" section updates to reflect guard.py extraction |

## Consumer migration surface

The consumer-side migration mechanics in `docs/ac-to-aa-migration.md` must survive every release:

- **Path 1 (change upstream + rerun)** stays the one-line flip (`echo 'yzhao062/anywhere-agents' > .agent-config/upstream; bash .agent-config/bootstrap.sh`). Every v0.4.0+ change preserves this contract.
- **Path 2 (nuke and reinstall)** is a two-phase clean slate on aa v0.4.0+. If `.agent-config/pack-state.json` exists, run `anywhere-agents uninstall --all` first and require exit 0 before deleting `.agent-config/`. If the state file is absent (pre-v0.4.0 install, or passive-only install), Path 2 remains the pre-v0.4 cache cleanup (`rm -rf .agent-config AGENTS.md CLAUDE.md agents/codex.md` + re-curl). This preserves the old simple path where safe and prevents user-level hooks, settings entries, and `~/.claude/pack-state.json` owner records from being orphaned in the v0.4.0+ case.
- **Pre-migration checks**: (a) AGENTS.md manual edits (unchanged), (b) ac-only skill dependencies (refined per release as private-pack migration absorbs them), (c) four-aa-skills-enough (superseded by private-pack check post-v0.5.0), (d) pre-push smoke (unchanged).
- **Verification checklist**: `cat .agent-config/upstream`, `grep -c 'rule-pack:agent-style:begin' AGENTS.md`, `ls .agent-config/repo/skills/` — checklist content updates per release to match current shipped set. The `rule-pack:agent-style:begin` marker persists through v1.0 (switches to `rule-pack:agent-style-field:begin` at the v0.4.x default switch; consumers pinning the full pack see the original marker).
- **Rollback**: one-line upstream flip back to `ac`. Always free.
- **Submodules**: bootstrap does not recursively walk submodules. Each submodule has its own `.agent-config/upstream`; migration is per-submodule. Private skill-packs work per-submodule identically to the outer repo (post-v0.5.0). For co-authored paper submodules, the "stay on ac" default stands until the co-PI explicitly agrees to the switch.
- **Opt-out**: `rule_packs: []` continues through v0.6.x; `packs: []` is the new primary syntax from v0.4.0. Both are equivalent. The `AGENT_CONFIG_RULE_PACKS` env var is renamed to `AGENT_CONFIG_PACKS` at v0.4.0 and gains a `-packname` subtract syntax (see Decisions section below); v1.0 hard-fail on legacy `rule_packs:` takes priority over any env override.

## STRICT parity trajectory

Snapshot of the STRICT list and how it evolves:

| File | v0.3.x | v0.4.0 | v0.5.0 | v0.6.0 | v1.0.0 |
|---|---|---|---|---|---|
| `scripts/guard.py` | STRICT | STRICT | STRICT | STRICT (demotions land in both) | **DROPPED** (extracted to ab) |
| `scripts/session_bootstrap.py` | STRICT | STRICT | STRICT | STRICT | STRICT |
| `scripts/generate_agent_configs.py` | STRICT | STRICT | STRICT | STRICT | STRICT |
| `scripts/compose_rule_packs.py` | — | STRICT (mirrored during delegation) | may drop once `compose_packs.py` is sole entry | dropped | dropped |
| `scripts/compose_packs.py` | — | aa-only (not mirrored) | aa-only | aa-only | aa-only |
| `bootstrap/rule-packs.yaml` | BY-DESIGN | BY-DESIGN (alias) | BY-DESIGN | deprecated | dropped (if alias removed) |
| `bootstrap/packs.yaml` | — | aa-only | aa-only | aa-only | aa-only |
| `.claude/settings.json` | STRICT | STRICT | STRICT | STRICT | may simplify if guard.py wiring moves |
| `.githooks/pre-push`, workflows | STRICT | STRICT | STRICT | STRICT | STRICT |
| 4 shipped `.claude/commands/*.md` pointers | STRICT | **DROPPED** (pack-emitted via `kind: skill`) | dropped | dropped | dropped |
| `skills/{implement-review, ci-mockup-figure, readme-polish}` | STRICT | STRICT | STRICT | STRICT | STRICT |

`check-parity.sh` updates in lockstep with each row change. The script's `STRICT=()` array lives in `scripts/check-parity.sh`; the edit is a single-line per dropped / added entry.

**aa-internal STRICT mirror** (introduced in v0.5.6): the table above tracks ac ↔ aa parity. v0.5.6 adds a separate axis — aa source ↔ aa wheel-bundled composer — that must stay byte-identical inside the `anywhere-agents` repo. As of v0.5.6 this is a manual release-gate check; a follow-up release adds an aa-internal STRICT block to `scripts/check-parity.sh`.

| Source | Wheel-bundled mirror | Enforcement |
|---|---|---|
| `scripts/compose_packs.py` | `packages/pypi/anywhere_agents/composer/scripts/compose_packs.py` | Manual v0.5.6 gate; script guard pending |
| `scripts/compose_rule_packs.py` | `packages/pypi/anywhere_agents/composer/scripts/compose_rule_packs.py` | Manual v0.5.6 gate; script guard pending |
| `scripts/packs/*.py` (recursive) | `packages/pypi/anywhere_agents/composer/scripts/packs/` (recursive) | Manual v0.5.6 gate; script guard pending, exclude `__pycache__/` |
| `bootstrap/packs.yaml` | `packages/pypi/anywhere_agents/composer/bootstrap/packs.yaml` | Manual v0.5.6 gate; script guard pending |
| `skills/{implement-review,my-router,ci-mockup-figure,readme-polish}` (recursive) | `packages/pypi/anywhere_agents/composer/skills/<name>/` (recursive) | Manual v0.5.6 gate; script guard pending |
| `.claude/commands/{4 names}.md` | `packages/pypi/anywhere_agents/composer/.claude/commands/<name>.md` | Manual v0.5.6 gate; script guard pending |

The aa-internal block extends `scripts/check-parity.sh`; it is independent of the cross-repo STRICT block above. Drift produces a wheel composer that disagrees with the bootstrap clone, which is exactly the v0.5.6 architecture is meant to prevent. v0.5.6 day-zero shipped with one drifted file (`skills/implement-review/SKILL.md`, single-phrase substitution caught by review and resolved in commit `6d156fe`); the parity guard prevents future single-character drift from recurring silently.

## Regression and failure analysis

**What could break**:

1. BC break on `rule-packs.yaml` loader if the schema change is not backward compatible. Mitigation: old schema stays valid through v0.5.x; warning from v0.4.0.
2. `AGENTS.md` byte drift if pack ordering changes. Mitigation: deterministic sort order by pack name; begin/end markers unchanged.
3. Hook namespace collision (two packs shipping hooks targeting the same file path). Mitigation: mandatory pack-name prefix in hook target path (`~/.claude/hooks/<pack>/<file>`).
4. `settings.json` merge: multiple packs adding the same permission pattern, or stale pack-owned entries after an uninstall. Mitigation: dedupe on exact JSON-value match during install; ownership tracked in `~/.claude/pack-state.json` (user-level) with `owners:` sets, not inline since `settings.json` is strict JSON and disallows comments. Uninstall removes this repo's id from `owners:` and only deletes the on-disk entry when `owners:` becomes empty and current JSON still matches the recorded value.
5. Active-hook execution order matters (first PreToolUse hook that denies wins), and Claude Code's hook runner dispatches in filename-alphabetical order, not in manifest declaration order. Mitigation: the composer prefixes hook target filenames with manifest-order two-digit indices (`01-foo.py`, `02-bar.py`). Consumer may override ordering via `hook_order: [pack-a, pack-b]` in `agent-config.yaml`; the composer re-stamps prefixes through the recoverable staged transaction in "Pack lifecycle operations" (transaction-scoped staging dir, `transaction.json`, state write by temp-file rename, then per-file `os.replace` for hook files). Mid-operation crashes are reconciled on next startup; the plan does not rely on directory-level atomic swap.
6. Private-source auth chain silently falls back to anonymous and hits a public repo at the same path. Mitigation: explicit `auth: <method>` disables the fallback chain for private sources. v0.5.0 ships this as the default posture.
7. Pre-2026-04-17 bootstrap caches do not self-update; any pre-2026-04-17 consumer missing the MIGRATIONS.md seed-refresh will not see v0.4.0+ behavior. Mitigation: detection check in `scripts/check-bootstrap-version.sh` recommended as part of v0.5.0 release runbook.
8. ac-only skills that import ac-internal paths (e.g., `../reference-skills/`) do not work unmodified as private packs. Mitigation: migration doc covers repackaging; low effort since the skill content is the same, only the load path changes.
9. STRICT parity gate becomes vestigial as aa-first features accumulate. Mitigation: formalize in `ONBOARDING.md` that STRICT is informational for specific files once extraction lands; the gate remains BLOCKING for files where byte-identical matters (hooks, generators, workflows until v1.0).
10. **Active-code supply-chain drift** (unreviewed active refs): a private pack on `ref: main` could install different hook code on each bootstrap with no approval record. Mitigation: `update_policy: prompt` is the v0.5.0 default for active entries; any resolved-commit or sha256 change emits a banner listing the drifted files and asks the consumer to apply or skip. Packs that must never auto-refresh active code can declare `update_policy: locked`, which fails closed on any drift outside an explicit pack-update command. Setting `update_policy: auto` on an active entry is a manifest error rejected at parse time.
11. **Stale active state after rollback or pack removal**: switching upstream or removing a pack could leave pack-owned hooks in `~/.claude/hooks/`, skill directories in `.claude/skills/`, or permission entries in `~/.claude/settings.json`. Mitigation: the three lifecycle operations (install/update, uninstall, rollback) read the split state files (project-local + user-level) and undo each recorded write under the `owners:` ownership contract. Path 1 in `docs/ac-to-aa-migration.md` calls uninstall-all before re-composing from the new upstream; **Path 2 must run uninstall-all first when active packs are present**, since deleting `.agent-config/` alone loses the project-local state record and leaves user-level hooks orphaned.
12. **Cross-repo user-level ownership collision**: two consumer repos install the same pack; one uninstalls. Without ownership tracking the second repo loses its hooks. Mitigation: `~/.claude/pack-state.json` carries an `owners:` set per user-level entry; uninstall removes only this repo's id; physical deletion happens only when `owners:` is empty and the current on-disk content still matches the recorded hash. Release runbook adds a two-repo shared-user-hook smoke test on Windows and Spark.
13. **Lifecycle-write interruption**: composer crash mid-operation could leave partial hook files, half-written state files, or incomplete settings merges. Mitigation: every write is recorded in `transaction.json`, staged to a temp path, `fsync`ed where supported, and committed with per-file atomic rename (`os.replace`); state-file updates use the same pattern. The reconciliation classifier and lock helper also shipped in v0.4.0, but automatic startup reconciliation and concurrent-bootstrap serialization move to v0.4.x when `scripts/compose_packs.py` wires those primitives in.
14. **Host-mismatch silent installs or whole-pack blocks**: before the `required:` field, unsupported hosts either block every pack touching them or silently skip their active content. Mitigation: `required: true` fails composition with a clear `host-mismatch` error; `required: false` skips the entry with an info log and installs the rest. Default is `required: true` (conservative) so pack authors annotate optional cross-host entries explicitly.

**False-positive / noise risk**:

1. `trigger-rate: high + decision: ask` is less blocking than today's `deny` but still visible. Users who preferred silent deny may see more prompts. Mitigation: noise audit is a separate release (v0.6.0); users pin `decision-override: deny` per-pack in `agent-config.yaml` if they want the old behavior.
2. Composing 3+ packs each with their own hooks doubles or triples PreToolUse latency. Mitigation: composer flags at install time when combined hook count exceeds a threshold (say 5).
3. Writing-style gate false positives on meta-discussion documents (style guides, CHANGELOGs that quote banned words). Mitigation: `ask` instead of `deny` from v0.6.0 reduces the blast radius; per-file-name whitelist in manifest (e.g., `exempt: [STYLE.md, CHANGELOG.md]`) is a possible extension.

**BC policy**:

- `rule_packs:` accepted with deprecation warning from v0.4.0 through v0.6.x. In **v1.0.0 the key is detected and the composer hard-fails** with an explicit migration error: prints the current value, prints the equivalent `packs:` rewrite, and does not compose any default packs until the user edits `agent-config.yaml`. This prevents the silent-break case where a `rule_packs: []` opt-out gets replaced with "no config, use v1.0 defaults" during upgrade.
- `rule-packs.yaml` manifest file: alias through v0.6.x, same hard-fail treatment at v1.0.0 if still present without a parallel `packs.yaml`.
- `DEFAULT_SELECTIONS` change from `agent-style` to `agent-style-field` (v0.4.x): visible; CHANGELOG + release notes highlight. Users pin back via `packs: [agent-style]`.
- `guard.py` git / gh / compound-cd logic extraction at v1.0: default-on `agent-behave` pack preserves behavior for most consumers; opt-out via `packs: []` and manual hook install if a user wants the old aa-bundled layout.
- **Python + PyYAML dependency fallback** (v0.3.0 contract, preserved through v1.0.0): consumers without Python 3 + PyYAML see the verbatim upstream `AGENTS.md` on bootstrap; the composer does not run and no pack content is mounted. Skill-pack opt-in additionally requires `git` (already a bootstrap prerequisite for sparse clone). This preserves the v0.3.0 BC path byte-for-byte regardless of later pack schema changes.

## Validation plan

**Pre-code (this doc's plan-review)**: walk three case-study packs through the proposed manifest.

1. **Today's `agent-style`**: passive slot (`docs/rule-pack.md` → AGENTS.md) ✓; active slot (banned-word hook) currently lives in aa core — declarable via manifest once hook is extracted ✓. Verdict: backward fit works; migration = remanifest-then-extract.

2. **Hypothetical `agent-behave`**: passive (behave-rules.md) ✓; active 1 (git-guard hook) ✓; active 2 (compound-cd hook) ✓; active 3 (permissions merge) ✓. Verdict: forward fit works.

3. **Private `nsf-helper` skill-pack**: source (ssh url + ssh auth) ✓; passive empty; active (SKILL.md → `.claude/skills/nsf-helper/`, trigger=agent-detect, decision=execute) ✓. Verdict: migration fit works.

If any case cannot be expressed in the schema, extend the schema before implementation.

**Post-code smoke tests** (run on each release):

1. Fresh v0.4.0 install with no `agent-config.yaml` → `AGENTS.md` byte-identical to v0.3.2 install (including the 4 pack-emitted command pointers matching their old static content); `.agent-config/pack-lock.json` and `.agent-config/pack-state.json` present; `~/.claude/pack-state.json` records every user-level write with correct `owners:` set.
2. Fresh v0.4.0 install with `packs: [agent-style-field]` (after default switch) → `AGENTS.md` contains only the nine-rule block, under 40k.
3. v0.4.0 active-code trust: manually modify a pack's source on a mutable branch between two bootstrap runs with `update_policy: locked` → second bootstrap fails closed with a clear delta (no silent overwrite of installed hooks).
4. v0.4.0 `update_policy: auto` no-churn: install a passive pack with `auto` policy, bootstrap twice with unchanged upstream → `pack-lock.json` byte-identical across runs (no git diff).
5. v0.4.0 hook order: a manifest declaring two hooks on the same trigger installs them as `01-<a>.py` and `02-<b>.py`; consumer `hook_order: [B, A]` override re-stamps to `01-<b>.py` / `02-<a>.py` via staged transaction; kill composer mid-restamp via SIGKILL and re-run → hook directory either fully at old layout or fully at new, never mixed.
6. v0.4.0 private source rejection: a consumer's `agent-config.yaml` entry with SSH URL returns "v0.5.0 feature" error at parse time; no partial installation, no silent skip.
7. v0.4.0 `kind: command` forward-compat: a manifest entry with `kind: command` parses without error, emits a `no-op at v0.4.0; full support in a later release` warning, and does not write any `.claude/commands/<name>.md` file.
8. v0.4.0 `required: false` skip: a manifest entry with `hosts: [codex], required: false` on a Claude Code install logs the skip, installs the rest of the pack normally, and records no user-level state for the skipped entry. `required: true` on the same entry returns a `host-mismatch` error.
9. v0.4.0 uninstall idempotence: install `packs: [X]`, then remove → every file recorded in `pack-state.json` and every user-level entry with this repo in `owners:` is cleaned per the ownership contract; re-run uninstall with no state → no-op, no error.
10. v0.4.0 two-repo shared-user-hook: scratch consumer repos A and B both install pack X (same ref) with a user-level hook; uninstall X from A → A's owner record removed from `owners:` list but hook file and settings entry remain (B still owns them); uninstall X from B → `owners:` empty, hook file and settings entry removed.
10b. v0.4.0 same-path different-version conflict: repo A installs `agent-behave@v0.1.0`; repo B attempts to install `agent-behave@v0.1.1` with the same default target path → composition fails closed with `user-level-output-conflict`, repo A's hook untouched, repo B receives no partial install for the conflicting entry. Manifest with versioned target path (`to: ~/.claude/hooks/<pack>/<resolved_commit>/01-name.py`) installs both versions side-by-side with distinct `owners:` lists.
10c. v0.4.x startup reconciliation (wiring deferred from v0.4.0): run `install`, kill the composer process mid-transaction with SIGKILL, leave orphan `~/.claude/hooks/<pack>.staging-<txn>/` dir. Re-run bootstrap → composer detects orphan, reads `transaction.json`, rolls back (pre-state hashes match) or rolls forward (new files all in place). Consumer state ends fully consistent. A third run with no orphan is a no-op. In v0.4.0 the classifier primitives are exercised at unit-test level via `scripts/packs/reconciliation.py`; composer-side bootstrap wiring lands in v0.4.x.
10d. v0.4.x drift detection on reconciliation (wiring deferred from v0.4.0): stage a transaction, manually corrupt one of the staged files before re-running. Startup reconciliation reports drift, leaves the orphan in place, does not auto-overwrite; user resolves manually. Same deferral as 10c.
10e. v0.4.0 side-by-side versions: two scratch repos install the same pack at different `ref:` values with `to: ~/.claude/hooks/{pack}/{resolved_commit}/...` in the manifest → both versions install to distinct `{resolved_commit}` subdirectories; each repo's `owners:` list contains only its own record; uninstall of one repo leaves the other version intact.
10f. v0.4.0 generated-command drift detection: install a pack with a skill; manually edit `.claude/commands/<name>.md` on disk; re-run bootstrap → composer detects `output_sha256` mismatch and re-emits the pointer (restoring byte-identical content), leaving no drift.
10g. v0.4.0 `uninstall --all` exit-code contract: run on a project with no packs → exit 0; run twice in a row → second call exits 0 with "no packs to uninstall"; run with a held lock → exit 10; run with a corrupted state file → exit 30 without modifying state.
11. v0.4.0 Path 2 active cleanup: install `packs: [X]` (X has active entries), run `docs/ac-to-aa-migration.md` Path 2 (uninstall-all then `rm -rf .agent-config/`) → user-level state and files cleaned; re-bootstrap starts clean.
12. Fresh v0.5.0 install with a private-source pack (test fixture) + valid SSH → skill materialized in `.claude/skills/<name>/`, pack-lock records resolved commit; invalid SSH → clear error, no silent anonymous fallback to a public repo of the same path.
13. Fresh v0.5.0 install in a submodule with its own `.agent-config/upstream` → private pack loads per-submodule without leaking into the outer repo.
14. v0.5.0 rollback: `packs: [X]` installed, then flip upstream back to `ac` → uninstall-all runs before re-bootstrap, resulting in no `X`-owned hooks / skills / permissions remaining.
15. v0.6.0: previously-denied writing-style match now surfaces `ask` prompt; user confirm → write succeeds; user deny → write rejected with no side effects.
16. v1.0.0: fresh install + `packs: [agent-behave]` → git / gh / compound-cd guards active at same severity as today's v0.3.x aa-bundled `guard.py`. Legacy `rule_packs: []` in `agent-config.yaml` → composer hard-fails with explicit migration error, prints the `packs: []` rewrite, does not compose any default packs. `AGENT_CONFIG_PACKS=-agent-style` env var does not bypass the legacy-key hard-fail (migration error takes priority).
17. User-level config absent: no user-level file → bootstrap behavior byte-identical to project-level-only mode (v0.4.0 through v1.0.0).
18. User-level config path resolution: POSIX `$XDG_CONFIG_HOME` honored when set; fallback to `$HOME/.config/anywhere-agents/config.yaml` when unset or empty; Windows `%APPDATA%\anywhere-agents\config.yaml`; missing both `$HOME` and `%APPDATA%` produces actionable error from CLI `pack add` / `pack remove` and stderr-only warning from composer (v0.4.0).
19. User-level config CLI (`pack add` / `pack remove` / `pack list`): absent / empty / pre-existing user-level file handled; atomic write via temp file + rename in the same directory; malformed YAML refuses rewrite with exact path + parse error to stderr and non-zero exit (v0.4.0).
20. First CLI add default preservation: `pack add <src>` with default `--type skill` into empty or absent user-level `packs:` seeds `[{name: agent-style}, {user pack}]`; `pack add <src> --type rule` does the same for the first rule-pack add. Subsequent adds append only. `pack remove agent-style --type rule` drops the default explicitly. Legacy user-level `rule_packs:` normalizes to `packs:` on write (v0.4.0).
21. Four-layer merge matrix: all meaningful intersections of user-level / project-tracked / project-local / env-var, including same-name override (more-specific layer wins for all fields) and `packs: []` clearing earlier layers while env-var additions still apply (v0.4.0).
22. Env var grammar: `AGENT_CONFIG_PACKS` accepts names and `-name` subtracts, comma-separated; rejects direct-source URLs with explicit grammar error before URL validation (v0.4.0 through v1.0.0).
23. Credential-URL rejection: HTTP(S) `source:` with any userinfo (`user@`, `user:password@`, `<token>@`) rejects at parse time before any network call; SSH `git@host:path` and `ssh://git@host/path` transport usernames are allowed (not credentials). Applied in every config layer (v0.5.0 once auth chain activates; v0.4.0 rejects private at parse regardless).
24. Noninteractive fetch env: with no SSH key and no `gh auth status` and no `GITHUB_TOKEN`, private-pack fetch fails within `ConnectTimeout=10` window (does not hang) and produces composite auth-failure error listing all attempted methods (v0.5.0).
25. GitHub URL normalization: `git@github.com:owner/repo.git` source with no working SSH agent but `gh auth status OK` succeeds via gh CLI after SSH preflight fails quickly under `BatchMode=yes`. Non-`github.com` hosts (GitHub Enterprise, other remotes) do NOT get normalization; URL shape continues to gate the auth method (v0.5.0).
26. Python/PyYAML fallback: consumers without Python 3 + PyYAML see verbatim upstream `AGENTS.md` on bootstrap; composer does not run; no pack content mounted. Preserves v0.3.0 BC path byte-for-byte (v0.3.0 contract, preserved through v1.0.0).
27. **Wheel-delivers-composer-fix smoke** (v0.5.6+, gates every release that touches `scripts/compose_packs.py` or the `composer/` mirror): build the wheel; `pipx install --force <wheel>` on a maintainer test project whose `.agent-config/repo/` was bootstrapped at the previous release; run `pack verify --fix`; inspect `.agent-config/pack-lock.json`. Pass when the lock state matches the intent of the fix. Fail when it matches the previous-release behavior — that means the wheel did not deliver the composer fix to the existing project, which is the v0.5.0 → v0.5.5 failure pattern. Item 27 catches the class of bug that test-suite-only validation missed five times in a row.

**Install-lifecycle integration suite** (v0.5.5 deliverable, gate before v0.6.0 noise-audit):

The 26 release-tied scenarios above are checklist items, run by hand against a release candidate. v0.5.0 through v0.5.3 each shipped with at least one regression in the AC → AA → AA+AP migration path that a checklist run would have caught but did not, because by-hand smoke is non-deterministic and is skipped under release pressure. v0.5.4 closes the four migration gaps that surfaced in production; the underlying gap in coverage remains.

Land in v0.5.5 a `tests/integration/test_install_lifecycle.py` pytest module, marked `@pytest.mark.integration` so it stays opt-in (the existing `--ignore=tests/integration` flag in the default test command excludes it). Three baseline scenarios, parametrized through a shared fixture:

1. **fresh_no_user**: empty tempdir, no `~/.config/anywhere-agents/config.yaml` present, run `anywhere-agents`. Asserts: rc=0; bundled defaults deploy (`agent-style` + `aa-core-skills`); no `agent-config.yaml` written; post-bootstrap reconcile call short-circuits per Fix #4.
2. **fresh_with_user**: empty tempdir, pre-seeded user config with one third-party pack, run `anywhere-agents`. Asserts: rc=0; bundled defaults deploy; post-bootstrap reconcile fires; project `agent-config.yaml` written with the third-party entry; `pack-lock.json` records all entries.
3. **upgrade_from_prev**: tempdir pre-populated by running the previous-release CLI (loaded from a session-scoped `git worktree add v<prev>` fixture), then re-run with the current source. Asserts: rc=0 both runs; no AC migration triggered (no `commands.bak-*`); drift gate adopts pre-existing pack-output files; final state matches `fresh_with_user`.

Fixture: a session-scoped `prev_release_worktree` that runs `git worktree add /tmp/aa-v<prev>-worktree v<prev>` once, picking `<prev>` as the most-recently-shipped non-current tag. Each scenario invokes the CLI via `subprocess.run([python, "-c", "from anywhere_agents.cli import main; sys.exit(main([]))"], env={"PYTHONPATH": worktree/packages/pypi})`. Cleanup uses Windows-friendly `shutil.rmtree(onerror=_force_remove)` that clears the read-only attribute on git pack files (same pattern as `_migrate_legacy_ac` after v0.5.4).

CI: a dedicated `integration-lifecycle` job runs nightly against `main` and on every release-candidate tag push. Default PR runs do not invoke it (network plus 30-second per-scenario cost). Failure blocks release sign-off but does not block PR merge to `main`.

Non-goals for v0.5.5: no synthetic composer mock (the bug class that surfaces in v0.5.x lives in the real-network path); no Docker harness; no parallelism (each scenario runs serially to avoid worktree contention).

**Release-runbook integration** (per `ONBOARDING.md` cheat-sheet):

- Every release touching `bootstrap.{sh,ps1}`, `compose_packs.py`, `compose_rule_packs.py`, `bootstrap/*.yaml`, or the active-item dispatch must run the Claude-Code-driven end-to-end install smoke on Windows bash + PowerShell + Spark Ubuntu against the release candidate (existing gate).
- `scripts/check-parity.sh` STRICT category gate stays BLOCKING for every release; the list contents update per the STRICT parity trajectory table above.
- Pre-tag `bash scripts/pre-push-smoke.sh` continues to gate release-candidate commits.

## Decisions made in plan-review

Promoted from Open Questions across plan-review rounds; recorded here as fixed design decisions, not issues.

**Round 1 decisions**:

- **Trigger vocabulary and host coupling** (was #1): active entries declare explicit `hosts:`. v0.4.0 supports `[claude-code]` only. The trigger vocabulary is Claude Code's (`PreToolUse`, `SessionStart`, etc.) with a host-neutral `agent-detect` for skill invocation. When a second host lands, the composer translates triggers at compose time rather than leaking Claude Code naming into pack manifests. Host-mismatch handling is governed by the `required:` field on each active entry (see Round 2 below).
- **Hook execution order** (was #2): deterministic by manifest order via composer-generated two-digit filename prefix (`~/.claude/hooks/<pack>/01-<file>`), because Claude Code dispatches hooks filename-alphabetically at runtime. Consumer may override via `hook_order: [pack-a, pack-b]` in `agent-config.yaml`; composer re-stamps prefixes as an atomic staged transaction.
- **Permission merge and uninstall semantics** (was #3): add-only install with ownership tracked in sidecar state files (project-local and user-level, split by ownership boundary). Uninstall drops exact JSON-value matches from the permissions array, gated on `owners:` set becoming empty. Rollback (switching upstream) calls uninstall-all before re-bootstrapping.
- **Default switch timing** (was #5): `DEFAULT_SELECTIONS → agent-style-field` lands in a v0.4.x follow-up, not at v0.4.0 ship. Keeps v0.4.0 consumer-invisible and one visible concern per release.
- **Active-kind dispatch** (was #6): the schema uses an explicit `kind:` field (`hook | skill | permission | command`). The composer branches on `kind:`, not on inferred paths. `target:` path no longer carries hidden semantics.
- **`guard.py` extraction timing** (was #10): stays at v1.0.0. Folding it into v0.6.0 would couple two visible consumer changes (noise demotions + deploy-pattern change) in one release; keep them separate.

**Round 4 decisions** (internal-consistency and follow-on specs):

- **Still-open wording cleanup**: three stale atomic-directory-swap references in the regression and migration sections (items 5, 13, and the Consumer migration surface Path 2 bullet) rewritten to match the Round 3 recoverable-staged-transaction contract. No architectural change, just internal consistency.
- **Generated-command change detection**: `role: generated-command` entries in `pack-lock.json` record `source_input_sha256` (the referenced skill's hash at generation time), `template_sha256` (composer template version + hash), and `output_sha256` (rendered output hash). Re-generation fires when any of these no longer matches. Unchanged inputs produce byte-identical outputs with no re-write.
- **Side-by-side version syntax**: two template variables (`{pack}`, `{resolved_commit}`) substituted into `files.to:` paths at install time. Unknown template variables rejected at parse. Named slot support deferred to a later release; v0.4.0 shipped only the two template variables plus default fail-closed singleton.
- **`anywhere-agents uninstall --all` CLI contract**: canonical command name unified across PyPI and npm distributions; six exit codes defined (0 clean / no-op, 10 lock timeout, 20 drift, 30 malformed state, 40 partial cleanup); Path 2 in migration doc requires exit 0 before proceeding.
- **Startup reconciliation locks**: explicit requirement for the v0.4.x composer-wiring follow-up that reconciliation acquires the same per-user and per-repo locks before scanning / rolling back / rolling forward; transactions whose owning process is still live are skipped rather than treated as orphans. Runs before the main compose step once that wiring lands.

**Round 3 decisions**:

- **User-level same-path conflict policy**: `owners:` entries are full records (`repo_id`, `pack`, `requested_ref`, `resolved_commit`, `expected_sha256_or_json`), not bare ids. Same target path with different expected content = fail closed with `user-level-output-conflict`, surface existing owners and refs, no overwrite. Side-by-side versions require explicit versioned target paths via the `{pack}` and `{resolved_commit}` template variables in the manifest (named slots deferred to a later release per Round 4).
- **`pack-lock.json` schema completeness**: the lock file records each file entry's `role` (passive / active-hook / active-skill / active-permission / generated-command), `host`, `source_path`, `input_sha256`, `output_paths`, `output_scope` (project-local / user-level), and `effective_update_policy`. Generated outputs (skill command pointers) carry `generated_from:` attribution and `null` source-path / input-sha256. Active entries with `effective_update_policy: auto` are rejected at manifest parse time.
- **Atomicity via recoverable staged transaction** (not atomic directory swap): per-transaction staging dir with `transaction.json`; only per-file atomic rename (`os.replace`) is relied on. That transaction layer shipped in v0.4.0. v0.5.0 Phase 7 wired the composer's bootstrap entry path to call the `reconcile_orphans` orchestrator wrapper before the main compose step, with rollback / rollforward based on pre-state hash match and drift reporting. Works on Windows and POSIX without depending on directory-level atomic replace.
- **`ac-to-aa-migration.md` Path 2 update**: Path 2 must call uninstall-all first whenever `.agent-config/pack-state.json` exists, so user-level hooks and permission entries are cleaned before `.agent-config/` is removed. The migration doc text updates in the same release that ships this plan's implementation.

**Round 2 decisions**:

- **Compression layering** (was #4): passive text compression (lite vs full) is expressed by manifest entries pointing at different `source.path:` values (`agent-style` vs `agent-style-field` vs `agent-style-lite`). No `variant:` field needed. Decision closed.
- **Noise budget threshold** (was #7): v0.6.0 threshold is `> 0` — any combined install that produces at least one `false-positive-risk: high` + `impact-if-allowed: low|medium` + `decision: deny` entry from a third-party pack triggers the composer warning and requires explicit consumer `decision-override: deny` in `agent-config.yaml` to proceed. First-party packs post-v0.6.0 produce zero such entries by design, so the gate mainly serves third-party stacking.
- **Pack-local command pointers** (was #8): command pointers moved to pack manifests in v0.4.0 (not deferred to v0.5.0). `kind: skill` entries auto-emit their `.claude/commands/<name>.md` pointer; `kind: command` entries ship standalone pointers. The four aa-shipped skill pointers became pack-emitted outputs and dropped from the STRICT parity list in v0.4.0. `docs/anywhere-agents.md` mirror table updates in sync.
- **Env var semantics** (was #9): rename `AGENT_CONFIG_RULE_PACKS` → `AGENT_CONFIG_PACKS` (v0.4.0, with deprecation warning on the old name through v0.6.x, hard-fail at v1.0). Add subtract syntax: prefix `-` subtracts a pack from the resolved selection (`AGENT_CONFIG_PACKS=-agent-style` per-session opt-out without editing `agent-config.yaml`). v1.0 hard-fail on legacy `rule_packs:` in `agent-config.yaml` takes **priority over** any env var override — env vars cannot silently bypass an explicit migration error.
- **Host-mismatch semantics** (Round 2 new): `required: true | false` per active entry, default `true`. Unsupported host + `required: true` = fail closed with explicit `host-mismatch` error; unsupported host + `required: false` = skip with info log, rest of pack installs. See the "Per-entry required field" subsection of the manifest.
- **State split and atomicity** (Round 2 new): project-local state (`.agent-config/pack-lock.json`, `.agent-config/pack-state.json`) and user-level state (`~/.claude/pack-state.json`) are distinct; user-level entries carry an `owners:` set to prevent cross-repo deletion. All lifecycle writes are staged + atomic-rename + lock-protected; Path 2 in `docs/ac-to-aa-migration.md` must run uninstall before removing `.agent-config/`.
- **`update_policy: auto` churn**: composer rewrites `pack-lock.json` only when the resolved commit id or file sha256 actually changed. Unchanged upstream → byte-identical lock file → no git-diff noise.

## Open questions

**Axis completeness** (was #0; retained here as a living check, not a decision to lock):

Is the 2-axis (passive / active × public / private) model complete? Candidates considered and rejected through Round 2:

- "ownership" (maintainer / team / community) → reduces to source-axis variants, not a new axis.
- "language" (Python hook / shell hook / YAML permissions) → implementation detail captured by `files:` + `kind:`, not architectural.
- "lifecycle" (install-time / session-time / tool-time) → captured by `trigger:` on active items, not a separate axis.
- "scope" (repo-level vs user-level) → already handled naturally by `files.to:` paths (relative to consumer root vs absolute `~/.claude/...`); a strength of the current shape, not a new axis.
- "trust" (integrity / provenance) → handled as a required manifest field set (`update_policy:`, `pack-lock.json` with resolved commit id and sha256), not a top-level axis.
- "host applicability" (claude-code / codex / other) → handled by per-entry `hosts:` + `required:`, not a top-level axis.

If a further axis is spotted at any later release-planning round, schema change before v1.0 is cheaper than after.

**All Round 1 and Round 2 remaining open questions (#4, #7, #8, #9) are now closed and recorded in the Decisions section above.** Zero open questions remain as of the close of Round 2 plan-review.

## Release sequence summary

| Release | Theme | Key deliverables | Consumer-visible |
|---|---|---|---|
| aa v0.4.0 | Unified manifest (public-only) | `packs.yaml`, `active:` with four kinds, `hosts:` + `required:` semantics, `files: [{from, to}]`, project-local + user-level state files, atomic lifecycle ops, pack-emitted command pointers (4 aa pointers drop from STRICT list), BC aliases. Private source rejected at parse time. | None |
| as v0.4.0 | Slim variants | `rule-pack-field.md`, `rule-pack-lite.md`, release-time drift check | None |
| aa v0.4.x | Default switch | `DEFAULT_SELECTIONS → agent-style-field`, CHANGELOG note | Medium |
| aa v0.5.0 | Direct-URL packs (public + private) | Bootstrap-active consumption of inline `source:` in `agent-config.yaml` for both `rule_packs:` and `packs:` (closes v0.4.0 schema-vs-consumption gap; `yzhao062/agent-pack` loadable end-to-end), SSH / gh / token auth chain, parser accepts private entries, pack-lock integrity applies to private, MIGRATIONS.md seed-refresh entry | None (new capability only) |
| aa v0.5.1 → v0.5.6 | Operational hardening; thick-wheel composer at v0.5.6 | `pack verify [--fix]` CLI + banner pack-deploy check; bootstrap auto-fix; drift-gate adopt-on-match; AC migration helpers; `force_defaults` 4-layer resolver; Windows cache hardening; **wheel-bundled composer + bundled-default content under `anywhere_agents/composer/`** (v0.5.6); new aa-internal STRICT mirror | Low — `pipx install --force` to v0.5.6+ now delivers composer fixes to existing bootstrapped projects without re-bootstrap |
| ab v0.1.0 | `agent-behave` product | First 3-slot pack | None (opt-in) |
| aa v0.6.0 | Noise audit | Demotion criterion is `false-positive-risk` × `impact-if-allowed` (not trigger-rate alone); composer noise budget; per-guard env vars | Medium |
| aa v1.0.0 | Full decoupling | `guard.py` extraction, STRICT list shrinks, default-on ab, **hard-fail on legacy `rule_packs:` / `rule-packs.yaml` with explicit migration error** | Medium |

## Reference example: `agent-pack` repo

[`yzhao062/agent-pack`](https://github.com/yzhao062/agent-pack) is the canonical third-party reference for the v2 manifest format. It declares 3 packs (`profile` passive, `paper-workflow` passive, `acad-skills` active with `kind: skill` entries for 3 skills) and ships the matching content at conventional paths: `docs/rule-pack.md`, `docs/paper-workflow.md`, and `skills/{bibref-filler,dual-pass-workflow,figure-prompt-builder}/`. Its `pack.yaml` uses the same v2 `active[].kind` plus `files[].from/to` structure as `aa-core-skills`, with remote `source` metadata added for third-party fetches, so consumers and v0.5.0 remote-fetch tooling can read it without special handling.

The repo is the **v0.5.0 acceptance test**: `anywhere-agents pack add https://github.com/yzhao062/agent-pack --ref v0.1.0` installs all 3 packs cleanly without any agent-pack changes. If installation requires a manifest tweak in agent-pack, the v0.5.0 design has drifted from this contract.

In v0.4.0, agent-pack documents the loadability gap honestly: stock `compose_rule_packs.py` rejects pack names not in aa's bundled manifest, so consumers reuse agent-pack content today by either (a) copying passive bodies into project `AGENTS.local.md`, or (b) registering pack names in a controlled bootstrap manifest (a fork of aa). The README's "Consumer Setup" section spells the v0.4.0-vs-v0.5.0 split out explicitly; pack-architecture.md should retain that boundary in any future revision.

## References

- `docs/vision.md` — strategy doc and scope gates (Step 2/3 adoption tests, kill criteria). Frozen after 2026-04-22 pass. Consulted before expanding this contract.
- `docs/anywhere-agents.md` — two-repo mirror policy and "what gets copied" table. Must update on STRICT-list changes (v1.0).
- `docs/ac-to-aa-migration.md` — consumer-side migration runbook. Updates per release per the table above; the "Forward direction" section is rewritten at v0.5.0.
- `MIGRATIONS.md` — bootstrap-cache seed-refresh entries. New entries at v0.5.0 (auth chain) and potentially v1.0.0 (guard.py extraction) if `bootstrap.{sh,ps1}` changes.
- `ONBOARDING.md` — release runbook cheat-sheet, STRICT parity reference. Updates on STRICT-list changes.
- `scripts/check-parity.sh` — STRICT list implementation. Updates in lockstep with the STRICT parity trajectory table.
- `skills/implement-review/SKILL.md` — the plan-review-first loop used to validate this doc before implementation.
- `archive/plans/PLAN-skill-pack-composition.md` — archived source plan (gitignored under `/archive/`); superseded by this file per the Status line. Kept for design archaeology.
- [`yzhao062/agent-pack`](https://github.com/yzhao062/agent-pack) — canonical third-party reference repo for the v2 manifest format; also the v0.5.0 remote-fetch acceptance test. See "Reference example" section above.
