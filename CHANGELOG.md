# Changelog

All notable changes to the shared agent configuration are documented here.
Consuming projects pull the latest on every bootstrap run; this log helps
track what changed between runs.

## Unreleased

### Added

- `skills/prun/references/agy-quota-and-models.md` describes the machine-local `autoMode.allow` entry for `dispatch-task-agy.py` and `dispatch-task.sh`, beside the Grok one, and the `prun` Reference Index sends a coordinator there when auto mode refuses a dispatch. In two sessions the classifier refused the Agy and Codex dispatchers and let the Grok one through, so a route the user had named for three agents ran on one.
- `docs/followups/2026-11-26-consumer-harness-audit.md` records an audit of real consumer sessions since 2026-11-15 against the harness and its skills: nine Agy units read the session logs and a five-agent Claude Workflow verified their claims. Its Disposition section lists what v0.11.0 fixes and what is recorded but not fixed.
- `programmatic-figure` builds scientific plots from data and code and ships in the default core skill pack.
- `AGENTS.md` § Skills: when the user asks for a skill or alias by `/<name>`, even mid-sentence, the agent reads its current `SKILL.md` for that request and does not rely on memory or a compaction summary. In the first consumer runs after the `prun` and `implement-review` slimming, two coordinators met `/vet all` or `/prun` inside a sentence and worked from memory; one ran two review rounds without a health check. The four existing Skills bullets are tighter, so the size gates for the generated and composed files still pass.
- `docs/writing-harness-map.md` is the one place that says where each part of the writing harness lives across the four source repositories. It tables where a new rule, banned word, check, review criterion, polish step, or project exception goes and what the same change must also update. Further sections give the canonical home of each layer, coverage by agent and file type, and the open follow-ups that a five-unit inventory found on 2026-11-15. `AGENTS.local.md` points at it before any writing change. The companion `/polish` skill in `agent-pack` reviews and polishes a draft in place; it holds the procedure and the line between content and expression, and points at the style rules in their homes.
- Claude Code consults an advisor. The registry gains an `advisor` role: Claude only, a model with no effort, and no inheritance from the family row, so a registry without the row has no advisor; the shipped row is `fable`. `scripts/agent_models.py render` writes it into `user/settings.json` as `advisorModel` in both repositories, bootstrap merges that into `~/.claude/settings.json`, `doctor` compares the live value (a key left after the row is removed counts as drift, and `CLAUDE_CODE_DISABLE_ADVISOR_TOOL` skips the check), `scan` flags an `advisorModel` or `--advisor` literal outside the registry, and `set --family claude --role advisor --off` removes the row. `AGENTS.md` gains a rule on when to consult it (before committing to a plan for a non-trivial change, after a failure recurs, before calling a multi-file change done, before settling a paper, proposal, or rebuttal argument) and says that a consult never fills a `/vet` reviewer slot. To stay inside the size gates, it drops the sentence explaining why fan-out has no gate and shortens two formatting bullets. `skills/agent-models/SKILL.md` covers billing and consent, the variables that remove the tool without a warning, how to check that it fires, and how to turn it off.
- Codex lists a repository's own skills. `agent-config` tracks one `.agents/skills -> ../skills` link, since a source repo is never composed and Codex reads repository skills only from `.agents/skills/`. In a consumer, the composer in `anywhere-agents` links each project-local `skills/<name>/SKILL.md` there beside the pack skills.
- `skills/implement-review/SKILL.md` opens with the rule that a subagent of the coordinator, or the coordinator's own checks, cannot fill a reviewer slot, and that an Auto-terminal round reports the reviewer, its review file, and the health-check result. The frontmatter description names `/vet`.
- Codex runs `scripts/guard.py` as a `PreToolUse` hook. Bootstrap registers it in `~/.codex/hooks.json` through the new `scripts/merge_codex_hooks.py` and reminds the user to trust it at Codex's startup review. Under Codex the writing-style gate also reads `apply_patch`, and the four `ask` rows pass, because a Codex hook cannot ask and a deny would outlast the user's approval in the conversation. The banner and compound-`cd` gates stay with Claude Code, and the Windows entry point does not register the hook yet.
- With `agent-style` 0.8.0 or newer, the style advisory in `scripts/guard.py` runs a document-level RULE-12 profile in place of the per-sentence rule. It also runs RULE-08, which reports the same caveat framing stated three or more times outside a limitations section. The profile reports a share of long sentences outside the human range, a run of `, so` clause joins, and sentences over 80 words, each worded as a departure from human-written papers. Releases before 0.8.0 keep their rule sets, and the summary line now says that a finding which reads well can stay.
- `skills/implement-review/scripts/style-audit.py` reports RULE-12 through the profile when the guard's set holds it. It keeps a document-level finding for a changed file even when the diff misses its anchor line, because a revision elsewhere can move the share, the `, so` rate, or the count of long sentences. That covers every finding that starts with `_PF_DOCUMENT_PREFIX` and every RULE-12 finding of the profile. Findings about one place keep the changed-line scoping.
- `/vet` reads a user-scoped reviewer default, `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`. Set to `both`, a bare `/vet` runs the two of Claude, Codex, and Agy that are not coordinating. An explicit reviewer token still wins, and without the variable the default stays Codex.
- `/vet all` runs the three of Claude, Codex, Agy, and Grok that are not coordinating, where `both` stays the pair without Grok. `all` also works as the value of `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`. A Grok slot that is absent or failed does not fail over, and the round continues with the other two.
- `/vet` triage asks whether a fix is worth a revision as well as whether the finding is correct. A correct but low-value finding is declined with a one-line reason and recorded as `Deferred` once the user confirms. Agreement between reviewers and a passed factual check no longer make a finding Will fix by themselves, and the loop ends when no new or still-open finding meets the bar.

### Changed

- The `vet` alias loads `implement-review` through the Skill tool when the first match in the lookup order is the deployed skill (`.claude/skills/implement-review/`, which bootstrap deploys) and the tool lists it; otherwise it reads the first matching file, so a project-local `skills/implement-review/` still comes first. The tool carries the whole `SKILL.md`, and invoking it again after compaction reloads it. The alias alone injected a 1.5 KB pointer, so a long session could lose the round checklist after compaction. The audit found four loops that skipped the health check, clustered after compaction and in runs with custom watchers. A headless run confirmed that a typed `/vet` now loads the 65.7 KB skill.
- Contract change: `health-check.py` Check 6 (scope correspondence, run only with `--prompt-file`) warns instead of failing when the review names none of the files the prompt referenced. All four Check 6 FAILs in the audit were valid reviews that discussed the plan without writing its filename, and every coordinator overrode them by hand. Step 7 of the round checklist and `references/health-check.md` list Check 6 with the inspected warnings.
- Contract change: approval moves to the point where work leaves the machine. `AGENTS.md` asks before `git push`, `gh pr create`, `gh pr merge`, `gh pr close`, `gh repo delete`, `gh release` changes, and package publishes. Commits, merges, rebases, resets, branch and tag changes, and deletes run without asking, and the user reviews the work at the push or publish. The maintainer approved the old local-step prompts by reflex. Two limits remain: `dd`, `mkfs`, and `shred` still ask, since they can wipe a disk and almost never run in routine work, and an agent does not delete or discard work it did not create unless the user asks. `scripts/guard.py` drops the local git checks and the recursive-delete check, and `user/settings.json` keeps six `ask` rules. A settings merge only adds to a list, so bootstrap passes `--retire-withdrawn` to `scripts/merge_settings.py` for `~/.claude/settings.json`, which removes the fifteen withdrawn rules unless the shared file lists them again. To keep one, add it to a project's `.claude/settings.local.json` or drop it from `WITHDRAWN` in a fork. The PowerShell fallback merge, which runs only without Python, does not retire rules. In `agent-pack`, `paper-workflow` now confirms only a submodule push, and `docs/codex-desktop-custom-instructions.md` gives the Codex desktop app the same rule.
- `/polish` gives the abstract, introduction, and conclusion the most care. Each tells a story, moving from the problem and what makes it hard to the insight and the takeaway. A full-section redraft tries two or three versions, with at least one within the page budget. When a section already tells its story, the redraft keeps the devices that carry it, such as an early question, a sentence that sets the stakes, signposts that order the findings, or a last sentence with a point. It uses a template phrase such as "In this work, we" only where the section lacks its own turn, and the `author-voice` templates now say the same. In a first blind read of ten sections, the maintainer kept the original three times, and each of those rewrites had dropped such a device. Two of them were abstracts. On ten new sections read with the rule, the maintainer preferred the rewrite in six, including all four abstracts, and called one a tie. The originals kept were two conclusions and a proposal summary. An abstract or conclusion also cuts by default a detail the body holds when the reader gets the same answer at the same strength without it: a metric, variant, or baseline name, a symbol or notation, an interval or test statistic, a secondary number, or a restated setup. The work's own name stays, and so does a baseline named by its kind when it is the comparison. Unless the venue sets another structure, a conclusion usually runs one or two paragraphs. Among drafts with the same answer, strength, and story devices, the one that reads best wins, and length breaks a tie. Across thirty sections in three blind reads, all six abstract or conclusion rewrites that lost to the original were longer than it. Four of the nine winning abstract or conclusion rewrites were longer too. The maintainer's notes flagged excess detail twice and a four-paragraph conclusion once as too fragmented. A fourth read of eight conclusions with the rule preferred the rewrite five times and the original twice, with one tie. Its notes flagged a notation and an interval bound that a conclusion did not need, which is why both join the list. An appendix serves the main text. `/polish` plans an appendix part by part, cuts parts and passages that support no main-text claim (run records such as hashes, run IDs, file paths, and logs, or code that restates the text), and reports each cut by heading or location. When a figure and a table show the same values, it keeps whichever serves the reader: usually the figure, and the table when a reader needs its exact values to check a claim. It trims each caption to what the display shows, how to read it, and one conclusion. Some drafts had appendices that ran to dozens of pages of run records, repeated displays, and long captions. Under `/vet`, the Paper lens asks whether the introduction tells that story and whether the appendix supports the main text.
- `/polish` in `agent-pack` is the one entry for writing. The pass had shrunk to small edits of the passages its review flagged, so many writing rules never reached a draft. It now drafts prose from its sources. Where a paragraph does not read well, it writes that paragraph again from a note of its claims and values, tries two or three versions where it matters, and checks the result against the original and the sources. Values and claims stay fixed, while how the prose shows a number is open: a sentence may round it, give a difference of two stated values, or point to the table that holds it. The profile rule, `my-router`, and Task Routing in `AGENTS.md` send writing to it, and `author-voice` becomes one of its parts. The Paper lens checks whether a revision changes the content or flattens the author's voice. `content_check.py` marks a removed token when its search finds no remaining occurrence.
- Abstracts, conclusions, and contribution lists follow habits of the maintainer's papers. The `author-voice` templates in `agent-pack` ask what a reader learns from an abstract or conclusion, since agent drafts tended to list the steps the work took. For completed work, they state the answer at the strength the body gives it; for proposed work, the question the work will test. Neither section points at a section, appendix, figure, or table, and both cite papers rarely. Contribution items in the introduction open on short labels in the MetaOD form. When the evidence establishes priority, the first label may name the advance. Later labels name the kind of contribution in two to four words, and the sentences after each label give the finding. `voice_check.py` counts pointers and cited works in an abstract or conclusion, flags any later contribution label over four words, and flags a pointer in any label. On the author's exemplar passages these measures pass, and tests cover drafts that fail each. `/polish` redrafts an abstract or conclusion that only lists steps, and it may remove a pointer, or a redundant citation whose removal keeps attribution, while keeping the claim. Under `/vet`, the Paper lens asks the same of both sections. `agent-style` takes these habits into its House Style at its next release, an open follow-up in `docs/writing-harness-map.md`.
- `editable-figure` requires multiple complete generated concepts and author selection before reconstruction for Yue Zhao's new overviews, standalone mechanisms, and substantial redesigns. The default is five concepts, with explicit user overrides and local-edit exceptions. See the [workflow feedback](skills/editable-figure/references/recent-workflow-feedback.md).
- `/vet` dispatches exactly the reviewer set it resolved and says so first. Step 3 of the round checklist now states the decision: before dispatching, the coordinator emits one channel line per reviewer naming what selected the channel and the reviewer set, then dispatches that set. Only the user's words for that review, or a rewrite or failure path the skill defines, change it, and the line names the reviewer and the reason. Section 1c no longer carries a second rule for the expected reviewer set, which fell back to Codex alone and never read `IMPLEMENT_REVIEW_DEFAULT_REVIEWER`; it takes the set step 3 resolved. A coordinator that had read the whole file sent a bare `/vet` under `IMPLEMENT_REVIEW_DEFAULT_REVIEWER=both` to Codex alone for three rounds and printed no channel line.
- `skills/implement-review/scripts/style-audit.py` reports the `AGENTS.md` banned list as `BANNED` findings, with the close variants the guard catches. It takes the patterns and the code-span stripping from `guard.py`, skips LaTeX comments, and does not repeat a word RULE-06 already reported on the same line. When no guard is reachable it lists `BANNED` as not covered. The guard checks only what an agent writes, and RULE-06 matches the base words but not their close variants: in a `/polish` acceptance run, the agent found four such variants in a proposal Introduction by reading after the audit had passed them. `tests/test_style_audit.py` also checks that the list in `AGENTS.md` and the one in `guard.py` agree.
- `/polish` in `agent-pack` gains a form for one round's edits (stage the round, audit without file arguments). It runs every step and reports before going on when nested in a larger task. Step 2 now writes its list down before any edit, and for an abstract, introduction, or conclusion it reads the `author-voice` template in that step. Step 4 checks `git status` so that intermediate files stay in the scratchpad, and step 5 reports every finding with its outcome. A seeded run on a real paper round and a proposal Introduction exercised the RULE-08 line and the local-rules step (`docs/followups/2026-10-06-defensive-writing-trial.md`), which closes that item in the backlog of `docs/writing-harness-map.md`.
- `/polish` in `agent-pack` now asks the writer to make a draft read well without changing its scientific content, where it used to make the smallest edit that cleared each finding. A Content and Expression section lets the writer change wording, sentence structure, and the order of sentences within a section while keeping the document's facts, numbers, citations, links, definitions, and results at their strength and scope, with their qualifiers, stated relations, ties, losses, and status markers. An abstract, introduction, or conclusion may leave out a secondary detail, or round a figure, when the body or a table states that result at its original precision, and it keeps its answer and every bound on that answer. Step 2 marks such a section *redraft* when it has more figures than the House Style and the `author-voice` template allow, more labels or terms than a first read can hold, or an order of moves that loses the thread; the redraft follows that template. An unsupported claim and a fact to verify go to the author unchanged. `agent-pack/skills/polish/scripts/content_check.py` saves the targets before the pass and reports per-file count changes for the numbers, citations, links, labels, cross-references, and math expressions it recognizes, with nearby files that hold the same token as leads; the writer reads every changed passage against the baseline. Acceptance runs are in `docs/followups/2026-10-06-defensive-writing-trial.md`.
- The `/vet` lenses apply Code item 12 (temporary-artifact hygiene) to every diff, and the item now names build outputs, trial copies of source files, and generated data or binaries when a repository does not need them. A paper round had left three trial copies of its source inside the paper's repository, and no lens a paper review uses asked about them.
- `agent_models.py map` lists the reviewer families a review panel leaves out. A file that resolves two or more reviewer rows dispatches its own reviewers, so the map ends that file's line with `no reader for: <families>` when the registry has a family the file never reads, and `--json` carries the same list as `gaps`. In such a file a `/vet` mention no longer shows as `*/reviewer`, and `skills/agent-models/` is skipped like the tool it documents. Two review panels, `venue-review-panel` in `agent-pack` and a consumer's local proposal panel, had resolved the Codex, Claude, and Agy rows and never the Grok one, and the old output gave no sign of it. Both now run Grok as a fourth scoring reviewer, and `docs/writing-harness-map.md` lists it.
- `skills/prun/SKILL.md` keeps what a coordinator needs on every run and moves the rest into references, each read on a stated condition. The core drops from 40,768 to 21,628 bytes and lists the references in a Reference Index near the top. Four references are new: `agy-quota-and-models.md` (model and effort overrides, quota, the sandbox), `codex-executor.md`, `state-recovery.md` (`gather`, `report-state`, `snapshot-tail`), and `web-units.md`; `grok-executor.md` gains its read condition. The `/prun` pointer and the Codex wrapper keep the routing rules and point at the index. `tests/test_skill_md_contract.py` fails when a reference file has no index row or a row names a missing file, and the size ceiling drops to the new size.
- `skills/implement-review/SKILL.md` drops from 147,793 to 65,793 bytes. It opens with a Reference Index and a round checklist inside its first 60 lines: two standing rules (the Claude slot when Codex coordinates, and when the loop stops) and twelve steps, each stating its decision once and linking the section that holds the procedure. Plan review, the Codex, Agy, and Claude backend mechanics, failover and recovery, and the health-check table with the Phase 2.5 methods move to six new references (`plan-review.md`, `codex-backend.md`, `agy-backend.md`, `claude-backend.md`, `failover-and-recovery.md`, `health-check.md`), each read on a stated condition, and `review-lenses.md` and `grok-backend.md` gain their read conditions. Windows prose, history that a CHANGELOG already records, and duplicates of a script header are cut. The `/vet` and `/implement-review` pointers say to read `review-lenses.md` each round and any other reference only when its condition holds. The reviewer prompt template now carries three save-contract phrases that used to sit in a coordinator-side copy (plain Markdown, Round 1 `None.`, fenced multi-line rewrites). `tests/test_skill_md_contract.py` routes the implement-review index and checks that the checklist ends within 115 lines, that its standing rules end within 9,500 bytes, and that every step links an existing heading; the Check 8 scan covers the references.
- Contract change: a health-check `WARN` (Check 6, 7, 8, or 9, or a Substance heuristic) no longer asks the user to proceed or downgrade. The coordinator reads what the check flags, records that reading in the round summary, and advances, and asks only when the inspection finds a defect: a tool failure that blocked verification, a truncated or placeholder review, a missing verification, or `missing-dispatch-tail`. Checks 1 to 5 and Check 10 still refuse the review, and `STALL`, `TIMEOUT`, and `REAP-UNKNOWN` keep their checkpoints.
- Contract change: the categorized findings are no longer put to the user for confirmation each round. The coordinator applies Will fix and Still open items, records each Decline as Deferred with its reason, and asks only about Needs discussion, Disagree, and Reopened items.

### Fixed
- The nested `git init` gate in `scripts/guard.py` expands a variable assigned earlier in the same command, with the value it had when assigned, or held in the environment, before it decides where the repository would land, and it does not deny a target that stays unknown, such as a command substitution. Before, `R=/private/tmp/...; git init -q $R` read `$R` as a directory under the cwd and denied it as nested: 11 times in 7 Claude Code sessions and 3 times under Codex since 2026-11-15, each a scratch directory for a `/vet` review repository or a `prun` clone. The shell-write gate shares the assignment reader, so it also keeps a saved value when its source is reassigned later.
- `health-check.py` Check 7 reports line numbers that match the review file: a stripped code span keeps its newlines, so a fence before a flagged phrase no longer shifts every later `lines=` value. It also matches its phrases on word boundaries, with `rate limited`, `rate limiting`, and `rate limits` still caught, so `quota` no longer fires on "quotation" and `i cannot` no longer fires on "CLI cannot"; 12 of 18 sampled Check 7 warnings were such word matches.
- The Agy `prun` dispatcher adopts a result its worker wrote under a mistyped path. If the worker misses its result path, the dispatcher checks the absolute paths and `file://` URLs in its final response. It publishes a non-empty file with the expected basename, written since launch and not registered by another unit, at the result path, keeps the response beside it, and prints `RESULT-RELOCATED`. In one 20-unit run, 4 workers had mistyped the session UUID of their result path, and the dispatcher had published their 1.1 KB closing replies as the results.
- A `/vet` round no longer leaves a copy of the repository in the temp directory. The Agy, Grok, and Claude dispatchers export the whole Git index to `<state-dir>/staged-snapshot`, so that the reviewer can run the repository's own verification, and nothing removed the copy afterwards. Each dispatcher now deletes its snapshot when it exits, whether the round succeeded or failed, and keeps the rest of the state directory for the health check. On 2026-11-22 one machine held 351 snapshots from under two days of reviews, 75 GB in all, nearly all of it from 18 rounds in repositories that track gigabytes of data.
- `health-check.py` Check 5 accepts a bare `Verification notes` line, the form the review request asks for ("Begin with Verification notes listing exact commands and outcomes"). The check wanted a colon, a heading, or bold, and in a consumer `/vet all` it refused a Grok review that labeled its notes with the bare line, although Check 10 already read that line as the label.
- `health-check.py` reads backtick runs whole when it strips code before Checks 7, 8, and 10: a span opened by N backticks closes at the next run of exactly N, and a run with no partner stays text. An inline four-backtick span that quoted a fence used to open a three-backtick block running to the next fence, which removed the `Verification status: VERIFIED` line between them and failed Check 10 on a valid review; an Agy review in a consumer `/vet` run hit it. `dispatch-gemini.py` masks quoted code with the same helper, `code_span_bounds`, before it accepts a review recovered from a backend error, so the two no longer disagree about which lines are quoted; a test keeps the two copies identical, and the helper finds each run's partner in one pass, so the scan stays linear on a long tail.
- The Agy executor of `prun` reaps an idle worker. After `PRUN_STALL_THRESHOLD` seconds (default 600) with no stdout or stderr output, `dispatch-task-agy.py` stops the Agy process and its descendants, appends a `[reaper]` line to the tail, and exits 124 with a `FALLBACK`, keeping a result the worker already wrote, as the Codex and Grok executors do. Before, a stalled unit kept running and spending until the 2,700-second `--print-timeout`. A reaped unit keeps its conversation id, so `--continue-from` can resume it. Its worker preamble also gains the skip-bootstrap statement the Grok preamble carries, so a worker in a clone of a consumer repository does not run bootstrap there.
- `ANTIGRAVITY_DISPATCH_EFFORT` set alone works with the registry's tiered slug. The Agy executor now moves the registry slugs of both quota groups to the requested tier, and when a tier is unlisted the slug floats to `high` and the effort follows it; it used to launch `--model <stem>-high --effort low`, which Agy rejects, so every unit that set only the effort failed.
- `prun`'s `gather` reports a `FALLBACK` result as `FALLBACK <path>`. It used to print `DONE` for any non-empty quiet file, so a failed unit read as finished. It now applies the first-line test `monitor` uses and exits 3 when every file landed and at least one is a `FALLBACK`.
- `prun`'s `monitor` reports a dead dispatcher on the next poll. It checked the dispatcher's PID only after the stall threshold, so a unit whose dispatcher was killed before publishing read as growing or stalled for ten minutes, and an orphaned Codex worker that kept writing the tail kept it from ever failing. A result published between the poll and the probe still counts as finishing.
- `/vet`'s Bash Codex dispatcher starts its stall watcher next to the reviewer launch. Started earlier, the watcher could record the registry resolver as the worker, find nothing alive to reap on a stream death, and publish `stream-reap-complete` while the reviewer still ran, so `await-review` reported DEAD. On a host that is not Windows, a missing `pwsh` no longer prints a warning on every dispatch, and the reviewer is no longer told about Store execution aliases.
- The Claude reviewer of `/vet` is told where supplied inputs are. Its relay states that the staged snapshot holds only the exported index and that a gitignored plan or untracked note arrives in the request under `SUPPLIED INPUT` headings, to be read there and never from the original worktree, as the Agy and Grok relays already say. `references/plan-review.md` names Claude and Grok beside Antigravity as snapshot backends. Script header comments that cited `SKILL.md` sections moved into references now cite the references.
- The Codex executor of `prun` collects results the way the Agy one does. `dispatch-task.{sh,ps1}` prepend the worker preamble, publish the worker's final message (`codex exec --output-last-message`) as the result when the worker writes no file, keep a worker-written file with the message beside it, refuse an existing result path or an unreadable prompt with exit 2, bound the `FALLBACK` to the final message and the last 200 lines of the tail, and exit 70 when codex exits 0 without a usable result, as the Agy executor does. Before, a worker that wrote its result elsewhere left the whole stream as a `FALLBACK`, 976 KB for one unit of the 2026-11-14 audit. It still takes only three arguments, so a Codex unit gets no follow-up turn.
- `/vet` refuses a review that answers the wrong round. When the reviewer's output lacks the current round's marker but carries a standalone marker for another round, `dispatch-gemini.py` and both `dispatch-claude` twins exit 70 and publish nothing, as `dispatch-grok.py` already did. Before, they prepended the current marker, so a Round 1 review returned during round 2 was published as Round 2 and passed the health check.
- The Grok executor of `prun` keeps a result the worker wrote. On a nonzero exit it used to replace that file with a `FALLBACK` record; it now keeps it, as the Agy executor does, and still exits nonzero. It also refuses `--add-dir` with exit 2 before launch: grok 1.0.77 lists the flag but rejects every session created with it (`additionalDirectories is not supported`), which had failed a whole batch.
- The shell-write gate keeps a backslash inside double quotes unless it escapes `$`, a backtick, `"`, or `\`, as bash does, so a quoted Windows path such as a scratch prompt under `%TEMP%` is read whole. CI runs the Python 3.9 floor on `ubuntu-24.04`, since `ubuntu-latest` (26.04) has no 3.9 build, and the PDF recovery test accepts PyMuPDF 2.0, which no longer prints MuPDF messages by default.
- The banned-word gate in `scripts/guard.py` covers prose written through a shell. A `Bash` or `PowerShell` command that writes a prose file through a redirection, `tee`, an in-place `sed` or `perl`, or a PowerShell content cmdlet is denied when its text carries a banned word. Before, a heredoc into a Markdown file passed while the same text through `Write` was denied. Targets come from a small lexer, so a redirection spelled inside quotes, a comment, or a heredoc body is not a write. The target path meets the `Write` scope test, so a scratch `agent-io` path stays exempt. A script that opens the file itself stays unread.
- The style advisory reports the line numbers of the file that was written. Blanking fenced code, inline code, and LaTeX verbatim used to collapse a multi-line span to one space, which moved every later line up. Each blank now keeps the newlines of the span it replaces.

### Removed
- The GitHub Copilot reviewer backend of `/vet`: the `copilot` reviewer token, `dispatch-copilot.{sh,ps1}`, their tests, and the backend's place in the failover queue, which is now Codex, Antigravity, Claude Code. Where a rule fell back to Copilot, it now falls back to Agy.
- The Plugin path of `/vet`, the channel that had the user paste the review prompt into the Codex IDE sidebar, and the `plugin` argument hint. Terminal-relay still takes a review from any tool that honors the `Review-<AgentName>.md` save contract.
- The Codex credit balance in the statusline (`cr`) and in the `agent-quota.py` row. The rate-limit windows stay.
- The weekly spend cap of the Grok dispatchers, `GROK_WEEKLY_BUDGET_USD`. It summed this machine's list-price spend, and the plan meter that `agent-quota.py` and the statusline read from Grok is the accurate figure. Setting the variable now has no effect.

## 2026-04-29

### Changed
- Updated recommended Codex defaults from `gpt-5.4` to `gpt-5.5` to match the maintainer's shipped configuration.
- Added `CLAUDE_AUTOCOMPACT_PCT_OVERRIDE=80` to shared user settings so bootstrapped Claude Code sessions compact later while retaining a context buffer.

## 2026-04-11

### Changed
- Guard hook now shows randomized, attention-grabbing approval messages for destructive git/gh commands (e.g., "WHOA THERE COWBOY! git commit wants to run") to prevent accidental approvals.

## 2026-04-08

### Changed
- Removed MCP path from `implement-review` skill. Terminal copy-paste is now the default Codex channel on all platforms. Plugin path remains as an alternative.

## 2026-04-07

### Fixed
- Standardized all 6 command pointers to dual-path lookup format (`skills/` then `.agent-config/repo/skills/`) so they work in consuming repos.
- Added missing `ci-mockup-figure` to the routing table shared skills section.
- Removed duplicate `.agent-config/` entry from `.gitignore`.
- Fixed bootstrap `.gitignore` check to recognize both legacy `/.agent-config/` and current `.agent-config/` entries, preventing duplicate lines on upgrade.
- Removed `Bash(cat:*)` and `Bash(echo:*)` from shared settings allow list to align with AGENTS.md guidance (use Read/Write tools instead).

### Changed
- Moved `test_guard.py` from `scripts/` to `tests/` and converted from custom runner to unittest so CI discovers it.
- Expanded README Structure section to document all directories (`reference-skills/`, `figure-references/`, `scripts/`, `user/`, `tests/`, `docs/`).
- Moved `CodexReview.md` to `docs/` to reduce root-level clutter.

### Added
- Reference-skills validation tests (structural integrity, markdown link resolution, openai wrapper checks for all 12 reference skills).
- Bootstrap smoke tests now verify user-level files (`scripts/guard.py`, `user/settings.json`) exist in cloned repo.
- Strengthened sparse-checkout test assertion to check full `skills .claude scripts user`.
- Pointer validation test now verifies dual-path format and local-first ordering.

## 2026-04-06

### Added
- `ci-mockup-figure` skill: build interactive HTML mockups and abstract figures (TikZ, skia-canvas, Illustrator ExtendScript) for papers and proposals.
- Abstract figure toolchain section with tool comparison table, arrow routing guidance, and path-specific review criteria.

## 2026-04-05

### Added
- Overleaf merge conflict resolution rules in Submodule Workflow: never use `--theirs` on structurally changed files, inspect co-PI changes via merge-base diff, preserve co-PI content as priority.
- Pre-merge checklist for Overleaf-synced repos.
- Synced 12 reference-skills from NSF-Proposal-Template-Yue.

### Changed
- Polished implement-review skill based on real-session feedback (CodexReview.md root review sink, round history tracking, save instruction contract).

## 2026-04-04

### Added
- `my-router` skill: context-aware dispatcher that detects work type and routes to the right domain skill.
- Task Routing section in AGENTS.md with router integration rules.
- PreToolUse hook guard (`scripts/guard.py`): blocks compound cd commands, gates destructive git/gh operations.
- Bootstrap now deploys guard hook and merges user-level settings from `user/settings.json`.

## 2026-04-03

### Changed
- Split `claude-code-tips.md` into `docs/` directory with separate reference tables (`claude-code-reference.md`) and extras (`claude-code-extras.md`).

## 2026-04-02

### Added
- Shell Command Style rules: avoid compound `cd && cmd` chains, use `git -C` instead.
- Hardened submodule safety: fetch-before-write checks, detached-HEAD awareness, `.gitignore` internal-only file warnings.

### Changed
- Session start check now covers OS detection, Claude Code model/effort preference, and Codex config validation.

## 2026-04-01

### Added
- `implement-review` skill: multi-round review loop with Codex via MCP, terminal, or plugin paths. Content-aware lens selection (code, paper, proposal).
- Review lenses grounded in Google eng-practices, NeurIPS/ICLR/ACL guidelines, NSF Merit Review, and NIH Simplified Peer Review.
- 12 reference-skills for proposals, paper reviews, presentations, CV, and reimbursement.
- Recommended Codex defaults: `gpt-5.4`, `xhigh` effort, `fast` inference tier.

### Fixed
- Windows MCP registration: use bash-compatible path without `.cmd` extension.

## 2026-03-31

### Changed
- Tightened formatting rules: sentence-length limits, dash usage restrictions, varied sentence structure guidance.
- Fixed override-path conflict between `AGENTS.md` and `AGENTS.local.md`.

## 2026-03-26 -- 2026-03-28

### Added
- Submodule Workflow section: safety rules for shared repos, push/pull procedures, `.gitignore` internal-only file handling.
- Claude Code native installer note in Environment Notes.

### Fixed
- Disabled `core.autocrlf` globally in bootstrap to silence CRLF warnings on Windows.

## 2026-03-24

### Added
- Git Safety rule: never run `git commit` or `git push` without explicit user approval.
- Claude Code tips and tricks reference doc.

## 2026-03-22

### Added
- Deep merge for shared Claude settings: arrays of objects are replaced, arrays of strings are deduplicated, project-only keys are preserved.
- Broad shared permissions (web, pip, conda, file operations) in bootstrap.

## 2026-03-21

### Added
- `bibref-filler` skill: safe external citation filling with verification, `working.bib` separation, and visible TODOs.
- `figure-prompt-builder` skill: copy-ready prompts for explanatory figures with bundled reference bank.
- `dual-pass-workflow` skill generalized to support any domain skill as the inner executor.

## 2026-03-20

### Added
- Initial repo: `AGENTS.md` with user profile, writing defaults, formatting rules.
- Bootstrap scripts for PowerShell and bash.
- `dual-pass-workflow` skill (first version).
- CI validation tests on Ubuntu and Windows.
