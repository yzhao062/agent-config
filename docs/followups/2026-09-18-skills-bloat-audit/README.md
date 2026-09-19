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

Acceptance procedure. The labels narrow what a person has to read; they do not replace reading it. A compound command whose inline source is followed by another statement (`python -c "..."; Write-Output 'done'`) keeps its outer quotes and can leave an inner path invisible, so it is reported required. Before claiming zero avoidable reads, inspect every shell and script event of the measured rounds, not only the unresolved list, and record any corrected label with the byte total it moves.

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
