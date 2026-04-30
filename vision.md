# Vision: the agent-config ecosystem

Status: draft, evolving. This is a working vision document, not a spec. It captures the ongoing design discussion across `agent-config` (ac), `anywhere-agents` (aa), and `agent-style` (as), so future sessions can pick up the thread without reconstructing it from scratch. Sections may disagree with each other as thinking evolves; that is expected at this stage.

**Shorthand** (consistent with `anywhere-agents.md`): ac = `agent-config`, aa = `anywhere-agents`, as = `agent-style`.

## Where we are today

Three related repositories share a single architectural idea: most of a useful agent workflow is not about which model you use, but about what context the model loads, what rules it follows, what skills it can invoke, and how those pieces move between projects and agents.

| Repo | Role | Visibility |
|------|------|------------|
| ac | Canonical source of shared defaults and personal daily driver | Private |
| aa | Sanitized public mirror of ac's shared core, plus PyPI and npm packaging | Public |
| as | Standalone writing ruleset with its own CI, bench, and adapters across 7 agent surfaces; also a skill layer consumable from aa | Public |

What already works:

1. The bootstrap pattern syncs `AGENTS.md`, skills, hooks, and Claude project settings into any consumer repo at session start. One upstream edit reaches N downstream repos.
2. The same `AGENTS.md` is read by Claude Code, Codex, Gemini, Cursor, Aider, Copilot, and Kiro. Cross-agent context is not theoretical; it is already how every session starts.
3. `as` shipped as an independent package and is now the first **rule pack** `anywhere-agents` composes into `AGENTS.md` by default (as of v0.3.0, 2026-04-22). The rule-pack composition flow, manifest format, opt-in precedence, and pack-author contract are formalized in `anywhere-agents/docs/rule-pack-composition.md`. That proves a key pattern: a focused ruleset can exist as its own release artifact and still behave like an always-on module of the larger system.

## The bigger metaphor

An earlier framing described aa as an operating system and as as a plugin. That metaphor has a subtle mismatch. An OS owns the privileged runtime, but aa does not run anything. It supplies context. The runtime is actually the agent you happen to be using.

The sharper metaphor is **a portable profile, like a Google account**. Your config is the identity layer. Agents (Claude, Codex, Cursor, Kiro, and whatever ships next year) are the devices you log into. `bootstrap` is the sync protocol. `AGENTS.local.md` and its siblings are your personal preferences on top of the delivered defaults. When you switch machines, or when a new agent launches, your configuration follows you rather than starting from zero.

There is one tension: "account" implies server-side authentication, but aa's sync is actually just `git-pull`. For external-facing language, "profile" or "portable agent identity" is safer. It preserves the "log in and your stuff follows you" promise without committing to authentication infrastructure.

This framing also explains the asymmetry between **delivered defaults** and **personalization**. Defaults are what we ship and maintain upstream. Anything you override in your own files is yours. Today the delivered side is strong and well documented; the personalized side has the file-level primitives in place but is scattered and under-documented.

## Layers in the current design

| Layer | Files / surfaces | Status |
|-------|------------------|--------|
| Delivered defaults | `AGENTS.md`, shared `skills/`, shared `.claude/settings.json`, `~/.claude/hooks/*.py` | Strong. Synced by bootstrap on every session. |
| User personalization | `AGENTS.local.md`, `CLAUDE.local.md` / `agents/codex.local.md`, `.claude/settings.local.json`, project-local `skills/<name>/`, `~/.claude/settings.json`, Claude memory system | Six surfaces scattered across three levels. Read side works cross-agent. Write side is Claude-only. |
| Per-project overrides | Each consumer repo's own files and settings | Works; well understood by existing consumers. |

## Rule packs (shipped) and skill packs (deferred)

The architecture distinguishes two composition layers, but only the rule-pack layer has a public contract today:

- **Rule pack** (always-on, injected into `AGENTS.md` at bootstrap): formalized in `anywhere-agents` v0.3.0 (shipped 2026-04-22). Manifest at `bootstrap/rule-packs.yaml`; full contract in `docs/rule-pack-composition.md`. `as` is the first rule pack, default-on.
- **Skill pack** (on-demand, invoked via the Skill tool): no external formal contract yet. aa ships four internal skills (`implement-review`, `my-router`, `ci-mockup-figure`, `readme-polish`); `as` also ships a `style-review` skill. No skill-pack equivalent of `rule-pack-composition.md` exists, because naming a contract for a sample of one tends to either over-fit or over-generalize. Defer until a second-author skill pack appears.

**Ecosystem claim is still contingent.** One rule pack (`as`) and zero external skill packs do not yet make an ecosystem. Until a second author or external pack appears for either layer, the project remains a reusable configuration distribution pattern with one reference implementation each, not a plugin ecosystem. The staging kill criteria below make this contingency explicit.

## Skill bundle stash: the `2nd-eye` idea (parked, 2026-04-29)

A concrete instance of the deferred skill-pack layer above. Captured so the design conversation does not need to be replayed.

**Members** (three skills already exist in ac / aa / `yzhao062.github.io`):

- `implement-review`: pre-ship review loop (currently STRICT mirror in ac + aa).
- `readme-polish`: README quality audit (currently in aa only).
- `impact-audit`: external coverage / media reception audit (currently `news-search` in `yzhao062.github.io/skills/`; rename pending).

**Common theme**: bringing systematic outside-in perspective to one's own work, at three lifecycle moments: pre-ship, at first contact, and post-ship. Tagline: "a second pair of eyes for your code, your README, and how the world receives your work."

**Audience**: researcher-engineers. People who simultaneously ship code, publish papers, and care about external reception: CS / ML / engineering academics (faculty, postdocs, senior PhD students), industry researchers with public OSS, and the EB-1A / academic-immigration cohort needing press-coverage evidence. Pure OSS maintainers and pure humanities or social-science academics only hit 2 of 3, so they are secondary, not primary.

**Repo strategy**: one bundled repo named `2nd-eye` (or similar), one `pack.yaml` with three sub-pack entries, one CHANGELOG, one release runbook. Follows the `agent-pack` precedent (multiple sub-packs in one repo), not `agent-style` (single artifact). Rationale: each killer skill is component-scale (about 50 to 100 KB); one-repo-per-skill would 3x the maintenance cost with little findability gain. Distribution: aa's seed `packs:` includes `2nd-eye` by default; consumers can `pack remove` per sub-skill.

**Open before execution**:

- Final repo name (`2nd-eye` favored; alternatives: `outside-eye`, `reception`, `going-public`).
- Final rename of `news-search` (`impact-audit` favored; alternatives: `impact-evidence`, `impact-summary`, `reception-audit`).
- aa-side migration path so existing consumers do not break when the four currently-bundled aa skills move to the new repo (likely a v0.6.x or v0.7.0 release with an explicit migration step).
- README positioning that surfaces the EB-1A / tenure / broader-impact use cases for `impact-audit` (academic-search keywords pay off).

**Picked up when**: aa v0.5.7 settles in real consumers, v0.6.0 update-UX work is shaped, and an unblocked window opens for the extract + create-repo work. No deadline.

## The biggest current gap: portable memory

Claude Code maintains a rich per-user, per-project memory system at `~/.claude/projects/<project-slug>/memory/`. It captures real personalization: who the user is, what shorthand they use, what feedback they have given, what should be confirmed before acting. This is the strongest personalization layer in the whole system today.

The moment the user switches from Claude Code to Codex, all of it is gone. Codex reads `AGENTS.md` and its own `~/.codex/config.toml`, neither of which receives those dynamic capture signals.

The read side of the problem is already solved. The `User Profile` section in `AGENTS.md` is cross-agent: every agent that bootstraps sees it, every agent that respects `AGENTS.md` uses it. The broken half is the write side. Nothing cross-agent captures new facts at conversation time the way Claude memory does.

A minimal **bridge proposal**:

1. Define `~/.agent-profile/memory.md` as canonical portable memory: plain Markdown, human-readable, schema stable.
2. Claude memory system gains a "cross-agent relevant" flag. Entries that qualify (durable user facts, writing preferences, long-lived feedback) auto-mirror into `~/.agent-profile/memory.md`. Entries specific to Claude workflows stay in the existing location.
3. Bootstrap appends the `~/.agent-profile/memory.md` path to the user-level `AGENTS.md` under a "load also" directive, so every agent that reads `AGENTS.md` picks it up automatically.

Under this design, Claude remains the strongest writer because it has auto-capture built in. Codex, Cursor, and other readers stop losing context the moment a session starts. If a second agent later develops its own capture mechanism, it can write to the same file without disturbing the readers.

**Main tradeoff:** Claude memory schema is still evolving. A bridge couples sync logic to that schema and will occasionally need maintenance. The profile file itself stays simple and stable; the churn is isolated to the Claude-side mirror.

**Parked status.** Until a stable vendor-supported import/export path exists, or until real user demand justifies the ongoing maintenance cost, the memory bridge is a parked idea rather than a planned implementation target. The staging plan below (Step 3 and kill criteria) governs when and whether it gets built.

## Staging: prove demand before infrastructure

The staged path should first test whether portable agent personalization is a real user pain, rather than assume that it is.

**Step 1 is a catalog pass.** Inventory the personalization surfaces that already exist across ac, aa, and as: repository instructions, generated agent files, Claude skills, Codex rules, package data, install commands, and release checks. The output is a short map of which surfaces are already portable, which are vendor-specific, and which are only useful for this author. An early candidate landing page for the catalog is `docs/personalization.md` in aa.

**Step 2 is an adoption test, not only an implementation step.** Add one more skill pack or profile module only if it has a user other than the original author, a second maintainer, or a clearly documented consumer repo that would be worse without it. If that evidence does not appear, keep the system framed as a high-quality personal and shared configuration repo rather than a platform.

**Early signal (2026-04-21).** aa (platform layer) accumulated 109 stars in 5 days; as (a concrete writing-ruleset skill pack) accumulated 185 stars in 2 days. Same author, overlapping announcement window, topic is the main variable. The asymmetry is consistent with this step's premise that early-user demand is stronger for concrete skill packs than for platform framing. One data point rather than proof, but worth tracking as more evidence accumulates.

**Step 3 is reserved for infrastructure that proves its need.** Do not build `~/.agent-profile/memory.md`, a registry, or consumer-facing rename / migration surface until there is evidence that users are switching across agents often enough to make portability painful. Defensive name reservation, such as parked domains or `0.0.0` package stubs, is treated separately in Phase A and must remain non-promotional. If the evidence stays weak, park the memory bridge and keep the project focused on bootstrap, documentation, and small reusable rule packs / skill packs.

**Kill criteria.**

- If no second author or external consumer appears after the next public release cycle, describe skill packs as an internal packaging pattern, not an ecosystem.
- If users report that they mostly stay inside one agent, drop the portable-memory goal and keep only cross-agent instruction export.
- If vendor memory schemas keep changing faster than the bridge can be maintained, treat memory sync as out of scope.

The maintainer records each kill-criteria decision in this document or in a linked release issue before moving from one stage to the next, so future sessions do not re-litigate a closed gate.

## Naming and rename timing

The name `anywhere-agents` carries a narrow promise: agents that work anywhere. As the product moves toward the portable-profile vision, that name starts to under-describe what the system actually is. The main thing is not "agents in many places," it is "your config in every agent you use." The subject of the name should shift from the tool to the user.

### When rename becomes load-bearing

The timing question has two axes: when to *reserve* the name, and when to *rename*. They should be decided separately.

**Name reservation (Phase A) should happen as soon as the project is comfortable preserving the candidate as an option.** Reservation costs roughly $110 per year plus a few stub package publishes, buys permanent optionality, and does not commit the project to renaming. The main window risk is third parties noticing the project and grabbing the remaining available TLDs, the PyPI and npm names, or the social handles. The existing holder activity on `yougent.com` (actively listed for sale on Afternic) and `yougent.dev` (parked on a default registrar parking IP) is a concrete reminder that pronounceable portmanteau names do not stay free for long.

**Rename itself has two viable paths, not one.** A default reading suggests pairing rename with the infrastructure stage (Step 3 in the staging plan above, where cross-agent infrastructure and the second skill pack would ship), under the assumption that brand equity accumulates over time and rename cost rises accordingly. But aa has been public for under a week as of this writing. Adoption is effectively zero, external bootstrap URLs are near nonexistent, and brand recognition outside the author's circle is nil. The "wait is expensive" premise barely applies right now, which opens an earlier-rename path worth considering alongside the infrastructure-stage path.

Two paths that both work:

1. **Early rename** (before Step 3 infrastructure ships, paired with a dedicated minor release so the rename is not buried under other changes). Narrative: "during the first weeks of the public release we realized portable-profile is the real framing, and we renamed while the cost was still near zero." The low-adoption window mechanically lowers migration cost, and the new name can lead any later infrastructure narrative rather than chasing it. The risk is a thin story ("we renamed because we thought of a better name") if Step 3 is still months away, or never arrives under the staging kill criteria.

2. **Step 3 rename** (paired with a major version bump alongside the cross-agent infrastructure and the second skill pack, if and when the staging gates permit Step 3 to proceed). Narrative: "the product shifted, so the name shifted with it." A fuller story that ties rename to visible product progress. The risk is that the low-adoption window has closed by then and migration cost has risen; currently low, but grows if Step 3 is delayed. If the staging kill criteria halt Step 3 entirely, this path also disappears and only early rename or no rename remain.

Either path benefits from landing the rename in a single clean release note rather than letting it drift across several.

The real decision point is not cost. It is which narrative shape the project wants to ship: *listen-and-adjust* (early) or *mature-and-rebrand* (Step 3). Both are defensible. Founders who favor rapid-iteration storytelling will lean early; founders who favor deliberate-release storytelling will lean Step 3.

What would shift the answer:

- If aa accumulates meaningful adoption (say, 50 or more external consumers, or 500 or more PyPI downloads per week) before Step 3 is ready, early rename becomes strictly cheaper.
- If the second skill pack is imminent (within four to six weeks) and passes the Step 2 adoption test, Step 3 rename gets its full narrative without giving up much cost.
- If the staging kill criteria trigger (no second author, users confirm single-agent behavior, vendor memory schema instability), the Step 3 rename path collapses and only early-rename or no-rename options remain.
- If third-party holders grab the remaining available TLDs or the PyPI / npm / social names before Phase A is done, all rename options get more expensive and the decision becomes less flexible.

### Naming criteria

A replacement name needs to do three things at once:

1. **Carry a "you" signal.** The vision's subject is the user's portable identity, not the tool.
2. **Keep an "agent" category signal.** Avoid abstract brand words that require an elevator-pitch every time.
3. **Be product-grade for the current era, not descriptive.** AI-era products that land tend to be short, invented, or portmanteau-based (Cursor, Warp, Copilot, Replit, Arc). Descriptive names like `agent-profile` sound like category definitions rather than brands.

Earlier candidates evaluated and set aside:

- `agent-profile`: accurate, but too descriptive to function as a brand. Useful as a docs term ("your agent profile is your configuration identity..."), not as a product name.
- `your-agents`: strong "you" signal, but grammatically awkward as a brand and ambiguous in third-person docs.
- `Tote` / `Orbit` / `Trail` / `Signet`: brandable single words, but lose the "agent" category signal and require extra explanation.
- `agent-passport`: evocative metaphor, but semantically slides toward authentication products.

### Working candidate: `yougent`

Portmanteau of "you" + "agent." It meets all three criteria at once: "you" is literally in the brand, "agent" as the suffix keeps category clarity, and the coined-word shape is consistent with current AI-era naming patterns. Pronunciation rhymes with "urgent" (YOU-jent).

### Availability summary (2026-04-20)

On 2026-04-20, `yougent` appeared free on PyPI and npm, and likely available on `.ai` and `.io` (NXDOMAIN, necessary but not sufficient; a registrar check is still required before purchase). `yougent.com` is listed for sale on Afternic; `yougent.dev` is on default registrar parking. The GitHub user handle is taken but inactive. No same-category AI or developer-tools trademark conflict surfaced, but formal clearance was not performed; general web search returned near-spelling brands (`YOUgent Studios`, `YouGene`, `Yougen`, `Yugen`) and unrelated directory entries.

The full per-channel scan table is preserved in this file's git history. It should only be revived if the project opens an active rename issue; at the current "keep `anywhere-agents`" stance, the summary above is enough.

### Risks and tradeoffs

1. **Pronunciation ambiguity.** Spoken "YOU-jent" is natural once heard, but first-time readers may pause. Visual treatment (capitalization, logo) carries some of the clarity load.
2. **"Gent" suffix.** Mild masculine undertone in English (cf. "gentleman"). Not a blocker, but worth flagging in any public-copy review.
3. **Bilingual marketing.** The "你gent" pun lands instantly for Chinese readers and is invisible in English. Marketing copy should be designed in parallel for both audiences rather than translated one way.
4. **`.com` and `.dev` are held by third parties.** Not a hard blocker. `.com` is listed for sale on Afternic; `.dev` sits on default registrar parking. Both are buyable at unknown prices, and `.ai` and `.io` appear to have no DNS record (registrar availability still pending confirmation). `.ai` and `.io` are also more on-brand for an AI-era product. Purchase price for the third-party domains is unknown until approached, but likely moderate since no yougent-specific brand exists for the holders to extract value from.
5. **GitHub org name collision.** The `yougent` user handle is taken. Recommended path is a variant org; precedents like Vercel, Railway, and Resend show users tolerate handle-and-domain mismatch without confusion.
6. **Sound-alike and near-spelling collisions.** Pronunciation rhymes with "urgent," which helps memorability but risks voice-assistant mishearing and speech-to-text errors (e.g., "uagent," "you agent"). SEO also has to cut through existing "urgent" traffic. General web search surfaces unrelated near-spelling brands: `YOUgent Studios`, `Yugen`, `YouGene`, `Yougen`, plus Japanese and Korean business-directory entries. None appears to be a same-category AI or developer-tools conflict, but name-recognition tests with new audiences should watch for hearing drift and spelling drift in notes, email, and search.
7. **Social-setting risk.** A name can read fine in a written product doc and still fail in spoken professional contexts. Enterprise buyers may hear "consumer app" rather than "developer platform," peer researchers may hear a less serious brand, and candidates may need the name spelled out. This is not fatal, but it is the class of issue that typically shows up only after the initial naming glow fades. The spoken meeting test in the gates subsection is the primary validation for this risk.

### Phase A: thin reservation (optional, one short sitting)

If the project decides to preserve the `yougent` option cheaply, do only the two high-value steps that can be completed in one short sitting:

1. Register `yougent.ai` after confirming registrar availability (approximately $80 per year). NXDOMAIN is necessary but not sufficient; verify at the registrar before purchasing.
2. Publish `0.0.0` stub packages on PyPI and npm under the name `yougent`.

Skip the GitHub organization variant, social-handle map (X / Bluesky / Mastodon / Product Hunt), and fallback-naming pattern. Those are only worth the effort if the project later commits to an actual rename trigger. This section exists as option preservation, not as a reservation program. Completing these two steps does not approve the rename.

### Rename rule (simple)

Do not rename `anywhere-agents` unless one of two conditions holds: the current name actively blocks the product story (users consistently misread what the project does, or search intent no longer finds it), or a replacement name passes real spoken and search tests against three different audiences (for example, an enterprise buyer, a peer researcher, a first-time candidate hire) without requiring explanation. Neither condition is met today. If the project ever decides a rename is needed, record the trigger in this file or a release issue and only then expand this rule back into the detailed gates and Phase B checklist preserved in git history.

### Phase B: actual rename (dormant)

If a rename is ever triggered, execute it through a coordinated migration covering repo and packaging, bootstrap pipeline, documentation and site, and release narrative. The detailed 11-step checklist is preserved in this file's git history (under the commit that first introduced the Naming section) and can be restored if the project commits to a real rename. Keeping it out of the main doc avoids making a parked decision feel like an active runbook.

### Naming reconsideration (2026-04-21)

The subsections above were drafted on 2026-04-20 under the assumption that aa had near-zero adoption. Star velocity data observed on 2026-04-21 (aa 109 stars in 5 days, as 185 stars in 2 days) shifts that assumption.

**What the data actually says.** aa is past its launch spike and still accumulating roughly 25 stars per day on day 5 and day 6. That could be steady-state organic discovery or delayed launch distribution; at this timescale the two are hard to distinguish. Either way, aa is no longer a blank-slate project, so rename cost has moved from near-zero to non-trivial. The aa-versus-as asymmetry mostly says concrete skill packs are easier to understand and share than the platform layer; it does not by itself prove `anywhere-agents` has brand equity worth protecting. The derived rule is to lead with concrete use cases and let the platform story follow. The data justifies "do not rush a rename," not "the current brand is now proven."

**What it does not change.** The structural reasons that originally motivated the rename still exist: the portable-profile positioning is richer than what the current name literally carries. Those reasons can be partially addressed by a tagline pass rather than a rename. Candidate taglines: "one config, any agent," "your agent config, anywhere," "portable agent profile, anywhere."

**Current action (2026-04-21):** keep `anywhere-agents`. Ship a tagline pass now, preferably "one config, any agent," and park the rename decision. Preserve `yougent` only as a cheap option: register `yougent.ai` and claim PyPI / npm stubs if that can be completed in one short sitting (see the thin Phase A above). Do not create a GitHub organization, social-handle map, Product Hunt surface, or rename migration track unless the project later commits to a real rename trigger.

## Open questions

1. Does "Google account" survive public documentation, or is "portable profile" closer to what we actually want to promise? "Account" implies server-side identity and authentication; "profile" is lighter and consistent with `git-pull` reality.
2. If we mirror Claude memory into a portable file, which entry types are cross-agent relevant by default? User-profile facts and writing preferences are obvious candidates. Feedback about specific tools or flows may or may not transfer.
3. Skill-pack versioning vs aa bootstrap version: unresolved. Rule-pack versioning is answered by v0.3.0 (per-pack `default-ref` in `bootstrap/rule-packs.yaml`, with a consumer-side `ref:` override in `agent-config.yaml`); skill packs do not yet have a parallel story.
4. Does `as` stay the reference rule pack for a while, or do we actively ship a second rule pack (for example, `agent-security`) to validate the pattern at the layer where a formal contract already exists? The Step 2 adoption test in the staging plan gates this.
5. At what point is this vision ready to move from ac (private) into aa (public)? Probably when the personalization catalog is documented in aa and a second rule pack (or skill pack) is at least planned.
6. What is the minimal schema for `~/.agent-profile/memory.md`? Reusing the existing Claude `MEMORY.md` index pattern plus per-entry Markdown files is one candidate; a single flat Markdown file is another. Tradeoff is maintenance cost versus readability.

## What this document is and is not

This is a living vision document. It is not a release plan, not a spec, and not a commitment to ship any of the ideas above. Its job was to separate platform ambition from current product work, park memory sync, and clarify the naming options.

Freeze this document after the 2026-04-22 pass (which incorporates the v0.3.0 rule-pack-composer implementation). Move execution into the aa README (tagline), CHANGELOG, release issues, public docs, or the next rule-pack / skill-pack repo. Reopen this document only when new user evidence changes the decision: for example, adoption patterns that make the current name actively misleading, a second skill-pack author appearing, or a concrete cross-agent memory import/export path shipping from a vendor. Continued incremental polishing of this file without such evidence is no longer the best use of time.
