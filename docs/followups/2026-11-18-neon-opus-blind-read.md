# Gemini 4 Neon against Claude Opus 5.5: two blind reads, 2026-11-18

Google released Gemini 4 Neon on 2026-11-18, and word went around that it writes well. Does it write a paper or proposal section better than Opus 5.5 at xhigh, the Claude setting the maintainer drafts with? Two rounds ran that day. In the first, each model reworded a fact sheet of one section. The maintainer found those drafts too alike to tell apart, so in the second, each model drafted a section from the rest of its document. Round 1 reused the design of an earlier read, on 2026-11-10, that compared Opus 5.5 with Fable 5.2. That read is recorded nowhere else, so its result is summarized below.

## Round 1 Design

- **Material.** Ten sections in progress, all written after July 2026 and none used in an earlier read. The five paper sections are a survey abstract, the opening of an introduction, the definition at the center of a framework, a results subsection, and the motivation of a workshop proposal. On the proposal side come the summary of a university seed-grant proposal, a research plan and a related-work subsection from a young-investigator proposal, the deployment section of a foundation proposal, and an NSF Intellectual Merit statement. They run from about 180 to 390 words.
- **Fact sheets.** Codex, at high effort, turned each section into a fact sheet. Each sheet keeps every claim of the section in the section's order and copies no phrase of five or more words. A count found no shared five-word sequence.
- **Writers.** Each run started in a fresh workspace holding the consumer rules (`AGENTS.md`, an identical `CLAUDE.md`, and `AGENTS.local.md`), the `author-voice` skill, and the fact sheet. Both writers got the same prompt: the section to write, a target length equal to the original's, and the names of the rule files and the skill.
  - Opus 5.5 ran at xhigh through `claude -p`, with user settings, hooks, and MCP servers off and Bash limited to `voice_check` and `wc`.
  - Gemini 4 Neon ran at xhigh through `agy -p` in accept-edits mode. Like Claude, it read the rule files and the skill and ran `voice_check`. Beyond those, Neon ran the `agent-style` checker, which Claude's limited Bash could not, so the setup gave Neon an extra style check.
- **Checks before the read.**
  - Each run's model came from the CLI's own record: the result JSON for Claude, and Agy's log label "Gemini 4 Neon (XHigh)".
  - Every draft fell within 0.85 to 1.1 times its target length and named no model.
  - Outside its workspace, Neon touched only the Python interpreter, `agent-style`, and its own Agy scratch directory.
- **Judging.**
  - The maintainer read the two drafts of each section on a blind page, with the labels X and Y shuffled per section, and picked one or called a tie.
  - Codex judged accuracy against the fact sheet, under labels A and B from a separate shuffle. It listed unsupported claims, changed facts, and dropped qualifiers for each draft.
  - The metrics stayed closed until the picks were in.
- **One display fix.** The fact sheet for the workshop section carried a placeholder in place of a symbol in a benchmark name. Both drafts copied it, and the blind page restored the symbol in both.

## Round 1 Results

In the maintainer's picks, Opus won six sections, Neon one, and three were ties. By document type, the papers split three, one, and one, and the proposals three, none, and two. On the seven decided sections, a two-sided sign test gives p of about 0.13. The maintainer noted that the read was quick.

The maintainer's notes give reasons for three of the Opus picks. Its bold leads in the results subsection read more clearly. Neon's workshop motivation carried too many specific figures, a pattern the House Style rules out. Opus's research plan had the better structure.

| Measure | Opus 5.5 xhigh | Gemini 4 Neon xhigh |
|---|---|---|
| Accuracy issues (unsupported / changed / dropped) | 2 / 1 / 1 | 0 / 0 / 1 |
| Sections where Codex found the draft more accurate (7 ties) | 0 | 3 |
| Median time per section | 217 s | 493 s |
| Median output tokens per section, mostly thinking | 23,000 | 54,000 |
| Cost of the ten runs at API prices | $13.86 | $13.66 |

Each of Opus's four issues added a relation or a scope that the fact sheet did not state:

- a motive for proposing the workshop;
- an open-ended date range in place of a closed one;
- a source attributed to a cited work;
- two claims about faithfulness merged into one.

Neon's one issue turned several named problems with evaluations into a general claim that evaluations are unreliable.

Claude Code reports the Opus cost. For Neon, Agy's token counts were priced at the published API rates: $3 per million input tokens, $0.15 per million cached, and $15 per million output. Both figures are API equivalents, since the runs drew on the Claude subscription and on the Agy pool, which are separate allowances.

## The 2026-11-10 Read

That read used the same design on ten other sections. In the maintainer's picks, Fable 5.2 at high effort won five, Opus 5.5 at xhigh two, and three were ties. Codex counted accuracy issues (unsupported / changed / dropped) of 2 / 6 / 0 for Opus and 0 / 3 / 1 for Fable. Those numbers come from that session's report, and its run files were not kept.

## Limitation of Round 1: The Writers Had Little Freedom

To the maintainer, the two drafts of a section read too alike, and the design explains why. It fixed three things:

- content: every claim of the original, and nothing more;
- order: the original's;
- length: the original's.

The two writers also shared one voice skill and its exemplars. What was left to the writer was the wording of each sentence. Round 1 and the 2026-11-10 read therefore measure how well a model rewords an ordered list of facts in the maintainer's voice. They do not test drafting: what to include, how to structure it, and how to frame it. That narrow range may explain the ties, and it may hide a real gap between models in exactly the choices a draft depends on.

## Round 2 Design

Round 2 gave each writer the rest of the document in place of a fact sheet, and a word limit in place of a target.

- **Material.** Ten new sections whose work is selection and framing. The papers supplied three abstracts and two conclusions, one from a research paper and one from a survey. On the proposal side came the overview of one NSF project summary and the Intellectual Merit statement of another, the opening objectives of a young-investigator proposal, the closing impact section of a young-investigator white paper, and the fit-with-mission section of a university seed-grant proposal. Four of the ten documents had supplied a different section to round 1.
- **Source.** Each writer got the document's main text, before any appendix, with the target section removed and the headings kept as Markdown. For a project summary, the source was the project description. Macros that name methods were expanded and inline math kept, so the source read as the document does. Sources ran from about 1,900 to 10,000 words.
- **Prompt.** It named the section, capped its length at the original's rounded up to a multiple of ten words, and said: "What to include, in what order, and how to frame it are your decisions." Caps ran from 140 to 460 words. Workspaces, rule files, the skill, models, and effort were as in round 1.
- **Checks.** The model checks of round 1 held for every run, and every draft came within its limit. Outside its workspace, Neon again touched only the Python interpreter, `agent-style`, and its own scratch directory.
- **Judging.** The maintainer read on the same blind page with a fresh shuffle. Codex judged accuracy against the whole source, under its own shuffle. It counted claims the source does not support, changed facts, and dropped qualifiers on claims a draft makes, but not facts a draft left out, since choosing them was the writer's job.

## Round 2 Results

In the maintainer's picks, Opus won seven sections and Neon three, with no tie. Papers split four to one and proposals three to two. A two-sided sign test gives p of about 0.34. Neon won one paper abstract, the NSF overview, and the seed-grant section. The maintainer's one note praised Opus's statement of objectives for describing each research thrust in one bold sentence.

The round-2 drafts shared far less wording. Between the two drafts of a section, the median Jaccard overlap of three-word sequences fell from 0.39 in round 1 to 0.09, and that of word sets from 0.81 to 0.40.

| Measure | Opus 5.5 xhigh | Gemini 4 Neon xhigh |
|---|---|---|
| Accuracy issues (unsupported / changed / dropped) | 1 / 1 / 13 | 1 / 5 / 24 |
| Sections where Codex found the draft more accurate (no ties) | 9 | 1 |
| Median time per section | 344 s | 651 s |
| Median output tokens per section, mostly thinking | 37,000 | 76,000 |
| Cost of the ten runs at API prices | $17.29 | $21.83 |

Accuracy reversed from round 1. With a whole document to compress, both writers dropped qualifiers, and Neon dropped almost twice as many. Six of its drops fell in the statement of objectives and five in the Intellectual Merit statement. Two of its five changed facts gave a subset the total of a whole study or collection, and the other three broadened what the source claims. One conclusion, for instance, extended a finding to four settings where the source reports exceptions in two. Opus's unsupported claim and changed fact both came in the seed-grant section, which named a kind of record the source does not test and changed the unit the team codes. In three sections the two drafts had the same number of issues, and Codex still judged Opus more accurate.

Neon's time and output tokens were again about twice Opus's, and at the API rates given under round 1 its runs cost about a quarter more.

## Both Rounds

Over twenty sections, the maintainer picked Opus thirteen times and Neon four, with three ties. On the seventeen decided sections, a two-sided sign test gives p of about 0.05. The rounds differ in design, and four documents contributed to both, so the pooled figure is only a rough summary. Codex's verdicts split by round: Neon was the more accurate writer when the content was fixed, and Opus when the writer chose the content. Each section ran once per model, one reader picked, one model judged accuracy, and Neon had the extra `agent-style` check in both rounds.

## Status

No change. Opus 5.5 stays the drafting model: it won both rounds of the maintainer's read and, in the drafting round, Codex's accuracy check. Neon as an Agy `/vet` reviewer and `prun` worker is the subject of a separate trial of the same date, `2026-11-18-neon-reviewer-worker-trial.md`.
