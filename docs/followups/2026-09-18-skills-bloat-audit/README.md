# Reviewer I/O classifier

`classify_reviewer_io.py` measures what a dispatched reviewer read during one review round: one row per tool event with a class (coordinator skill, rules, diff, source, review sink, tests and builds, other), a label (required, avoidable, unresolved), and the decoded bytes the model received, then totals by class and by label. Prompt and injected bytes are reported separately. It is the acceptance instrument for Milestone A of `PLAN-skills-diet.md` (the reviewer contract): the same ordinary code change is reviewed before and after the contract change, and the avoidable classes must go to zero while required reads stay.

The module docstring carries the byte convention and the label rules; `--help` prints it. The rules in one line: the diff is judged by its transport, an exact repeat is avoidable whatever the scope says, a first read inside the review scope or with a recorded verification reason is required, a first read of an instruction file that was not supplied is required, a coordinator-skill read outside the scope is avoidable (full file or example review) or unresolved (targeted range), and everything else is required on first use. Unresolved events are listed for adjudication by hand and are never folded into the other two totals.

## Invocation

```
python docs/followups/2026-09-18-skills-bloat-audit/classify_reviewer_io.py --input <rollout.jsonl | tail> --round <round.json> [--json report.json] [--prompt-relay <path>]
```

A Codex rollout is the `rollout-*.jsonl` file under `~/.codex/sessions/<date>/` that the dispatched `codex exec` wrote (the record whose text starts with `# AGENTS.md instructions for` is the injection; tool outputs are `CommandExecution` items). An Antigravity input is the `tail` in the round's state directory; `prompt-relay` beside it splits the prompt into preamble, request, and embedded diff. `round.json` states what the reviewer was given:

```json
{"backend": "codex", "supplied_instruction_files": ["AGENTS.md"], "review_scope": ["src/module.py"], "diff_transport": "command", "verification_reasons": {"c5": "why this out-of-scope read answered a verification question"}}
```

The fixture under `fixture/` is the hand-labeled contract: one synthetic rollout and one synthetic tail with the eight cases the plan names (a first read of an unsupplied `AGENTS.local.md`; the coordinator skill under review; two ranges of one file; an out-of-scope lens read with a reason; a second diff obtain; a re-read of a supplied rule; an example review with no reason; a targeted skill read with no reason) plus an exact-repeat case, an embedded-transport diff, two different files read under the same shell wrapper, a coordinator script that is executed rather than read, two ranges of one instruction file, and a mixed event whose one output covers an in-scope read and a supplied-rule re-read. `tests/test_classify_reviewer_io.py` runs it; `expected.json` holds the labels and totals, and a change to the rules updates both.

Known limits: a Codex shell event is the payload the shell wrapper ran, and a command that reads several files is one event with one output, classed by its most consequential read, or unresolved when it mixes an in-scope read with a read that would be avoidable alone; an operand a command executes (`python x.py`) is not a read; a here-string or heredoc body is dropped as data only when it is literal (a single-quoted here-string or a quoted heredoc delimiter) and the whole event is positively recognized as storage (assigned to a variable, piped into Set-Content, Out-File, Add-Content, or tee, or redirected into a file, and nothing else); an expandable body (`@"..."@`, or a heredoc with a bare delimiter) is always kept because `$(...)` runs during expansion, while both bash quote styles suppress it; source passed inline with `-c` or `-Command` is a body too; in every other event the body is kept, and when it names a rule file, a coordinator file, a review sink, or a diff, the event is unresolved, because no shell is interpreted here; a search is identified by its literal command, so a different pattern, context option, or whitespace inside the pattern is a different read and only an identical command is a repeat; a `run_command` whose output the tail did not record counts 0 bytes and is marked; Antigravity `view_file` bytes come from the CLI's `N lines, M bytes` summary, which is the payload the model received, so they exceed the literal `output` string.

Acceptance procedure. The labels narrow what a person has to read; they do not replace reading it. A compound command whose inline source is followed by another statement (`python -c "..."; Write-Output 'done'`) keeps its outer quotes and can leave an inner path invisible, so it is reported required. Before claiming zero avoidable reads, inspect every shell and script event of the measured rounds, not only the unresolved list, and record any corrected label with the byte total it moves. The required column needs inspection too. A `-TotalCount` range over a file the same session already read whole is labelled required, and the 2026-09-18 measurement below found 9,376 such bytes outside the flagged events.

## The acceptance measurement (2026-09-18)

This is an observational check of Milestone A on ordinary review work. The paper comparison holds the document, the coordinator, and the reviewer model fixed: rounds 7 to 9 ran before the contract, round 10 after it. One unrelated consumer round joins the after side. The paired acceptance procedure of `PLAN-skills-diet.md` is not complete, because it wants a pair on both backends and no Antigravity round has run in a consumer.

Before: the eleven `fire-ai-bench` rollouts of 2026-09-18 that the audit sampled, under the old contract. After: four consumer rollouts that began at 19:22 or later. The contract was committed at 18:34 and reached those two consumers when they re-bootstrapped, at 18:51 and 18:55. Three of the four cover `fire-ai-bench` round 10, a 48-page paper and its code repository, reviewed by a root reviewer and two sub-agents. The fourth covers `trading-doc` round 3. Classification uses one shared `PAPER_SCOPE` for every paper session and `crypto` for the trading round, as `measure_acceptance.py` records.

Two byte conventions appear below. Raw bytes are the classifier's `aggregated_output`, which is what the command produced. Delivered bytes are Codex's `formatted_output`, which is what reached the model once a long response was truncated. The after sample is 1,251,797 raw bytes against 853,920 delivered. Raw bytes are what the table below reports, because the classifier counts them.

| | tool output | avoidable | unresolved | coordinator_skill | rules |
|---|---:|---:|---:|---:|---:|
| Before, 11 rounds | 7,872,334 | 2,405,335 (30.6%) | 1,586,748 | 1,832,635 | 555,949 |
| After, 4 rounds | 1,251,797 | 109,165 (8.7%) | 18,159 | **0** | 63,189 |

**The coordinator-skill class is zero in all four after rollouts**, against 1.83 MB across the eleven before them. That class holds `SKILL.md`, its references, and its example reviews. A reviewer read those to learn a workflow and a response format that its own prompt already carried. No event in the after sample opens one.

### The avoidable column, adjudicated

That column does not survive event-by-event reading, and no corrected share replaces it here. Reading only the flagged events would not have been enough either: two of the corrections below move bytes the classifier had called required.

| Event | Bytes | Classifier | Reading of the record |
|---|---:|---|---|
| root `c2` | 59,723 | avoidable | Required. A second `git diff --cached`, run in the paper repository after `git -C ...\fire-bench diff --cached` ran against the code repository. Two repositories, two diffs. |
| root `c3` | 420 | avoidable | Required. `Get-Content AGENTS.md,AGENTS.local.md` in `fire-bench`, exit 1. Neither file exists there, so the 420 bytes are two PowerShell errors and no rule text was re-read. |
| root `c45`, `c49`, `c60` | 57 | avoidable | Required. `git diff --cached --check` and `git diff --name-only`, a lint and a file list. The 57 bytes are one `rg` hit in `main.log`. |
| trading `c5` | 277 | avoidable | Required. `New-Item`, `git ls-files`, `--check`, and `git status --short`: setup and metadata. |
| trading `c4` | 32,413 | avoidable | Mixed. Lines 56 to 500 of a plan and 1 to 128 of the prior review, read after `c3` was truncated from 60,742 raw bytes to 40,108 delivered. Source-position matching puts 11,671 bytes as already delivered and 20,742 as recovered; the line heuristic below counts 10,933. |
| root `c52`, `c53` | 9,376 | required | Avoidable. `-TotalCount 55` and `-TotalCount 40` over two findings files this reviewer had already read whole at `c46` and `c50`, neither of which was truncated. Both outputs are exact substrings of those. The line heuristic below counts 9,213. |
| root `c54` | 6,799 | avoidable | Avoidable. The tail after line 55 exactly repeats content delivered at `c46`. |
| root `c55` | 9,476 | avoidable | Mixed. The tail after line 40 carries a new 525-byte replacement paragraph alongside content delivered at `c50`, so the whole output is not avoidable. |
| root `c42` | 7,405 | unresolved | Mixed. Two tail reads, `-Skip 86` and `-Skip 130`. The sweep note supplies new context; the `figstyle.py` tail repeats 161 bytes that `c11` delivered whole. |
| sub-a `c12` | 1,407 | unresolved | Required. A script run whose log tail was printed; the interpreter path parsed as a read. |
| sub-a `c18` | 7,177 | unresolved | Required. Lines 112 to 238 and 469 to 500, printed with numbers. Its two matching lines are `parser.parse_args()` and the `__main__` guard, which other files carry too. |
| sub-b `c2` | 1,674 | unresolved | Required. A changed-prose style check over the saved diff. |
| trading `c12`, `c13` | 496 | unresolved | Required. The scripts that validated and published the review. |

### A second measurement, without adjudication

Count, for each command event in order, the raw output bytes on lines that an earlier event in the same session already delivered. Comparing against delivered bytes rather than raw ones keeps recovery after a truncation from counting as repetition. A line matches only when twelve or more significant characters remain after a `NNN: ` prefix and surrounding whitespace come off, and it contributes its own bytes including its terminator. What this measures is repeated text. It counts output a command produced as readily as a file a reviewer opened, and it misses repetition that rewrapped or that arrived outside a command.

| | raw bytes | delivered bytes | already delivered | share of raw |
|---|---:|---:|---:|---:|
| Before, 11 rounds | 7,872,334 | 5,086,800 | 677,105 | 8.6% |
| After, 4 rounds | 1,251,797 | 853,920 | 85,829 | 6.9% |

Repetition barely moved, from 8.6 percent to 6.9, inside a per-round spread of 1.2 to 16.6 percent before and 2.1 to 10.9 after. Coordinator-skill reads are gone from the after sample; repeated reads of a reviewer's own working files are not. The single largest after-side entry is not a read at all: two identical `pdflatex` runs, 15,009 bytes each, of which 29,670 bytes repeat. A second LaTeX pass is how the build works, and both sides of this comparison contain builds. The rest is two sub-agent findings files read whole and then again in halves, and one reviewer going back over a plan and a prior review. A reviewer is already told not to read the same content twice, and all four after rollouts received that instruction. These sessions show incomplete compliance with it.

### The round that reviewed this record

Both backends reviewed this staged record under the contract, which supplies the Antigravity data point the sample above lacks.

| | tool output | coordinator_skill | rules | avoidable |
|---|---:|---:|---:|---:|
| Codex | 1,207,851 | **0** | 1,230 | 12,902 |
| Antigravity | 373,645 | **0** | 1,507 | 183,811 |

Neither reviewer opened a coordinator skill file. Each read `AGENTS.local.md` once, which the contract allows for an applicable instruction file that was not supplied. The Codex total is dominated by a single 1.05 MB verification script that the reviewer wrote and ran, so it measures its own work more than its reading. Its whole avoidable figure is one event that reads a test file alongside `git status --short` and `git diff --cached --check`, which is the misclassification the ledger above corrects twice.

The Antigravity row is the sharper result. Its trace records three `view_file` calls for `scripts/guard.py`, each summarized as 2,055 lines and 89,220 bytes. The reviewer was working out which style detectors this project runs. For the two repeat calls the classifier assigns 178,440 bytes, most of its 183,811. Because the tail records those summaries rather than the payloads, it does not settle whether the whole file reached the model each time.

### Limits

Five, and they bound what this record claims. No Antigravity round has run in a consumer under the contract, so that side rests on the Milestone A rounds, the ARM64 smoke, and the source-repo round above. The four after rollouts are two review rounds rather than four independent ones, and three of them belong to a single round. Neither side follows a sampling rule: the before rollouts are the ones the audit sampled, the after ones are whatever ran next. Only the after side was adjudicated by hand, while the before side keeps 1,586,748 unresolved bytes at their classifier labels. The two sides also differ in size and task mix. These totals describe these sessions; they do not isolate what the contract caused.

### Reproducing it

`corpus-manifest.json` states the cohort: all eighteen inputs by session stem and SHA-256, which eleven of the fourteen before rollouts the table counts, and why the other three do not. The three are setup probes that produced no reviewer tool output.

The measurement resolves every stem under one corpus root, `~/.codex/sessions` by default, or a frozen copy named with `--corpus-dir <path>` or `ACCEPTANCE_CORPUS_DIR`. Any missing, ambiguous, or hash-mismatched input ends the run with exit 2 and names each problem. Should a classifier change move a round across the zero-output boundary, the run ends with exit 3, because the manifest's membership and its stated reason would then disagree.

That replaces the original recipe, which globbed a session scratchpad for the before cohort and took the first timestamp-prefix match for the after one. A scratchpad does not outlive its session. The two dates hold 108 sessions: fourteen before rollouts, four after rollouts, and ninety outside both cohorts, so no date glob over the session store separates the two cohorts. Worse, a missing input printed one line and carried on to a table that was quietly short, with exit 0. Verification used a frozen copy held outside both the scratchpad and the session store: the tables above reproduce byte for byte, and each of the three rejection paths exits non-zero.

The raw rollouts are about 78 MB and are not committed. `tests/test_classify_reviewer_io.py` covers the manifest's shape and the three rejections with synthetic inputs, so it needs neither.

Six classifier accuracy items surfaced during this adjudication and are recorded in anywhere-agents#60. Diff identity needs a repository dimension. Metadata-only diff commands need their own treatment. Commands that read a diff from a temp file are classified by another path they name. A `-TotalCount` range that repeats an earlier whole-file read is labelled required. Executed interpreter paths can still parse as reads. Finally, `Select-Object -Skip N` without `-First` matches no range pattern, so a tail read is treated as a full read, which is what mislabelled `c42` here. None of them is a one-line fix: `c55` shows that a file can change between two reads, so a later range is not waste by construction.

## The audit sample, recomputed with these labels

Fourteen Codex rollouts (three probes and eleven reviewer sessions of three multi-agent rounds) and twelve Antigravity rounds from the 2026-09-18 audit, run with `supplied_instruction_files: ["AGENTS.md"]` and command transport for Codex, nothing supplied and embedded transport for Antigravity, and an empty scope on both, because the audit sample does not record what each round reviewed. Three of the Codex rollouts reviewed this very plan, so their coordinator-skill reads were legitimate subject reads and show here as avoidable or unresolved; the acceptance measurement records the scope and does not have that ambiguity.

| round | tool output | required | avoidable | unresolved | coordinator_skill | rules | top avoidable targets |
|---|---:|---:|---:|---:|---:|---:|---|
| Codex R01 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Codex R02 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Codex R03 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Codex R04 | 846,202 | 576,951 | 107,605 | 161,646 | 124,813 | 184,373 | diff:unt 70; Get-ChildItem -Name *tool*; git  49,926; diff:r7.tmp.md; git diff --name-only; git dif 22,724; diff:ts.py | Select-Object -Skip 123 -First 2 15,676 |
| Codex R05 | 329,292 | 175,366 | 7,156 | 146,770 | 146,770 | 28,525 | other::closest|402|25,722|SmokeBench' sections 7,156 |
| Codex R06 | 605,024 | 267,858 | 105,428 | 231,738 | 64,115 | 26,105 | diff: -n 'paper|ARR|lens|Phase 1b' .agent-con 40,424; diff:site-packages\agent_style'; $p='sections 31,002; diff:lPath $p | ForEach-Object { $n++; if ($n 20,724 |
| Codex R07 | 538,721 | 220,023 | 95,183 | 223,515 | 223,515 | 10,571 | diff:e-src/make_calibration.py figure-src/mak 81,422; diff:eight Errors|Every model ran|same output 11,370; diff:diff --cached --name-only -- sections/A- 2,391 |
| Codex R08 | 1,157,660 | 493,536 | 583,846 | 80,278 | 244,983 | 103,670 | diff:ults.tex sections/D-benchmark-detail.tex 191,029; coordinator_skill:.claude/skills/implement-review/SKILL.md 137,207; rules:AGENTS.md 103,670 |
| Codex R09 | 259,789 | 117,271 | 0 | 142,518 | 142,518 | 64,562 |  |
| Codex R10 | 793,967 | 272,465 | 225,243 | 296,259 | 296,259 | 10,627 | diff:git diff --cached -- sections 88,188; diff:git diff --cached -- sections 88,188; diff:ontent sections/07-benchmark-design.tex  40,602 |
| Codex R11 | 1,075,377 | 614,751 | 294,756 | 165,870 | 161,775 | 0 | diff: 'AGENTS.local.md missing' }; git diff - 86,121; diff:harmProjects/internal-writing/.claude/sk 71,579; diff:d -- sections/00-abstract.tex sections/0 54,427 |
| Codex R12 | 577,263 | 168,701 | 312,476 | 96,086 | 265,121 | 56,387 | coordinator_skill:.claude/skills/implement-review/SKILL.md 169,035; diff:evqa.pdf,'C:/Users/yuezh/PycharmProjects 86,532; rules:AGENTS.md 56,387 |
| Codex R13 | 897,875 | 651,067 | 246,808 | 0 | 0 | 14,110 | diff:ached -- sections/D-benchmark-detail.tex 123,143; diff:-results.tex sections/10-limitations.tex 59,021; diff:-ge 110 -and $line -le 142) { '{0}: {1}' 54,655 |
| Codex R14 | 791,164 | 322,262 | 443,882 | 25,020 | 162,766 | 57,019 | coordinator_skill:.claude\skills\implement-review\SKILL.md 137,746; diff:x sections/F-terms-directions-limits.tex 128,086; diff:ied=0 -- sections/D-benchmark-detail.tex 95,732 |
| Agy 462f56d2 | 2,670 | 2,670 | 0 | 0 | 0 | 0 |  |
| Agy 5362dc32 | 1,722,625 | 655,364 | 1,067,261 | 0 | 5,057 | 8,755 | source:hot\packages\pypi\anywhere_agents\cli.py 156,595; source:hot\packages\pypi\anywhere_agents\cli.py 156,595; source:hot\packages\pypi\anywhere_agents\cli.py 156,595 |
| Agy aa7bb0c9 | 910,417 | 551,411 | 359,006 | 0 | 3,694 | 313,347 | rules:l-writing\papers\fire-ai-bench\AGENTS.md 102,540; rules:l-writing\papers\fire-ai-bench\AGENTS.md 102,540; source:snapshot\sections\D-benchmark-detail.tex 82,221 |
| Agy aa7bb0c9 | 1,324,865 | 786,862 | 531,614 | 6,389 | 13,366 | 74,213 | source:c\.system_generated\steps\134\content.md 93,929; source:snapshot\sections\D-benchmark-detail.tex 83,314; source:snapshot\sections\D-benchmark-detail.tex 83,314 |
| Agy aa7bb0c9 | 569,759 | 304,999 | 264,760 | 0 | 554 | 64,184 | review_sink:ing\papers\fire-ai-bench\Review-Codex.md 70,897; rules:charmProjects\internal-writing\AGENTS.md 55,803; source:snapshot\sections\D-benchmark-detail.tex 44,443 |
| Agy c5f709c1 | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Agy e9286c4f | 0 | 0 | 0 | 0 | 0 | 0 |  |
| Agy fd68ae96 | 90,887 | 27,534 | 63,353 | 0 | 0 | 0 | source:af\.system_generated\steps\22\content.md 18,504; source:af\.system_generated\steps\22\content.md 18,504; source:af\.system_generated\steps\22\content.md 18,504 |
| Agy fd68ae96 | 69,348 | 32,340 | 37,008 | 0 | 0 | 0 | source:775\.system_generated\steps\8\content.md 18,504; source:775\.system_generated\steps\8\content.md 18,504 |
| Agy fd68ae96 | 106,585 | 65,379 | 41,206 | 0 | 0 | 0 | source:6de\.system_generated\steps\8\content.md 18,512; source:6de\.system_generated\steps\8\content.md 18,512; source:6de\.system_generated\steps\8\content.md 4,182 |
| Agy fd68ae96 | 89,254 | 52,230 | 37,024 | 0 | 0 | 0 | source:988\.system_generated\steps\8\content.md 18,512; source:988\.system_generated\steps\8\content.md 18,512 |
| Agy fd68ae96 | 9,746 | 7,891 | 1,855 | 0 | 0 | 0 | source:myviterbi-profile-draft.md 1,562; source:myviterbi-profile-draft.md 293 |
| **Codex total (14)** | **7,872,334** | **3,880,251** | **2,422,383** | **1,569,700** | **1,832,635** | **555,949** | |
| **Agy total (12)** | **4,896,156** | **2,486,680** | **2,403,087** | **6,389** | **22,671** | **460,499** | |

Codex: 7.87 MB of tool output over the sample, 2.42 MB avoidable and 1.57 MB unresolved under an unknown scope; the coordinator-skill class alone is 1.83 MB and the rules class 0.56 MB. Antigravity: 4.90 MB, 2.40 MB avoidable, nearly all of it repeated source reads and the rules hunt (0.46 MB), with the coordinator skill at 23 KB. The totals agree with the U5 and U6 unit totals that the audit note cites; the labels are a demonstration under assumed metadata (unknown scope, no recorded verification reasons), not a verified estimate of historical waste and not the acceptance measurement. An Antigravity `view_file` call records no line range, so a file the model viewed several times counts as several full reads at the CLI's reported size; whether the CLI paginates such reads is unknown, and the acceptance measurement adjudicates those rows by hand.
