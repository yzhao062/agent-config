---
name: implement-review
description: Review loop for staged changes. Detects content type, prepares a review request for Codex (MCP, terminal, or plugin), categorizes feedback, revises, and iterates. Works for code, papers, proposals, or any text-based output.
---

# Implement-Review

## Overview

A review loop for staged changes. Claude Code detects the content type, sends the changes to Codex for review, categorizes the feedback, revises, and iterates. Works through three Codex channels: MCP (macOS/Linux default), terminal relay (Windows default), or IDE plugin.

## Codex Channels

Three paths to Codex are supported. The skill picks the best available path automatically.

### MCP path (macOS / Linux default)

Codex is registered as an MCP server (`codex` and `codex-reply` tools available). Claude Code calls `codex` directly with the review request and reads the response as a tool result. No user relay needed.

### Plugin path (IDE sidebar)

Codex runs as an IDE plugin with direct access to the repo. The user tells Codex to review in the plugin sidebar (e.g., "review the staged changes"). Codex can see the working tree and run `git diff` itself, so no diff needs to be copy-pasted. The user relays Codex's feedback back to Claude Code.

### Terminal path (Windows default)

The user has a Codex interactive terminal window open alongside Claude Code. Claude Code prepares a copy-pasteable review prompt (summary, diff, lens, round number) and presents it as a fenced text block. The user copies it into the Codex terminal, then relays the feedback back to Claude Code. This avoids the MCP approval-prompt and Bitdefender friction on Windows.

### Path selection

1. **Windows**: default to the terminal path. If the `codex` MCP tool is available and the user explicitly asks to use MCP, use it instead.
2. **macOS / Linux**: check whether the `codex` MCP tool is available. If yes, default to MCP. If not, fall back to the plugin or terminal path.
3. The user can override at any time (e.g., "use MCP", "use the plugin", "use the terminal").

## Prerequisites

At skill start, check for staged changes (`git diff --cached`). If nothing is staged but unstaged or untracked changes exist, list them and ask the user whether to stage all (`git add -A`), stage specific files, or abort. Do not auto-stage without confirmation — untracked files may be sensitive or unrelated. If there are no changes at all, there is nothing to review -- inform the user and stop.

## Phase 1: Prepare and Send Review

### 1a. Detect content type

Inspect the file extensions in the staged diff to classify the change:

| Extensions | Content type |
|---|---|
| `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.c`, `.cpp`, `.h`, `.sh`, `.yaml`, `.json`, `.toml` | `code` |
| `.tex`, `.bib` (in a paper or manuscript directory) | `paper` |
| `.tex`, `.bib` (in a proposal or grant directory) | `proposal` |
| `.md`, `.rst`, `.txt` (in a proposal or grant directory) | `proposal` |
| Everything else or mixed | `general` |

If the diff spans multiple types, pick the dominant one. The user can override by saying, e.g., "review this as a proposal." For proposals, also ask which agency lens to apply (NSF or NIH) since they use different evaluation frameworks.

### 1b. Build the review context

Prepare a review request with:

1. **Summary** -- one to three sentences on what changed and why.
2. **Diff scope** -- `git diff --cached`. For large diffs (over 200 lines), summarize the changes and list affected files instead of including the raw diff.
3. **Review lens** -- the content-type-specific criteria from [references/review-lenses.md](references/review-lenses.md).
4. **Round number** -- which iteration this is (starting at 1).

### 1c. Send to Codex

All review prompts sent to Codex (regardless of channel) must include a save instruction **at the very top of the prompt, before the summary or diff**, so Codex sees it first. This lets Claude Code read the feedback directly from the file, and lets the user read or forward it without copy-pasting from chat. The save instruction is:

> IMPORTANT: Save your complete review to `CodexReview.md` in the repository root. Overwrite any existing content. Use plain Markdown. Start the file with a `<!-- Round N -->` comment (matching the round number below) so the reader can verify freshness. Then include the file/diff scope, review lens, findings in priority order, and concrete recommended changes. Do not skip this step.

**MCP path**: Call the `codex` MCP tool with the review request (including the `CodexReview.md` instruction above).

- If the call succeeds and returns a non-empty response, proceed to Phase 2.
- If the call fails (error, timeout, empty response, or the user denies the tool call), do **not** silently continue. Instead:
  1. Report the failure clearly, including the error message if one was returned.
  2. Ask the user whether to retry via MCP, fall back to the terminal or plugin path, or abort.
  3. Do not guess or fabricate a review response.

**Terminal path**: Present a copy-pasteable review prompt as a fenced text block. Include all context inline so the user can paste it directly into the Codex terminal window without modification:

````
IMPORTANT: Save your complete review to CodexReview.md in the repository root. Overwrite any existing content. Use plain Markdown. Start the file with a <!-- Round N --> comment (matching the round number below). Then include the file/diff scope, review lens, findings in priority order, and concrete recommended changes. Do not skip this step.

Review the staged changes in <repo path>. Round <N>.

Summary: <one to three sentences>

Diff:
```diff
<git diff --cached output, or summary for large diffs>
```

Review lens (<content type>):
<numbered criteria from review-lenses.md>
````

Then wait for the user to relay Codex's feedback or confirm that Codex has finished (see Phase 2 for how Claude Code picks up the review).

**Plugin path**: Tell the user the changes are ready for review and suggest what to tell Codex in the plugin, e.g.:
> "Review the staged changes (round N). Focus on [detected lens]. Save your complete review to `CodexReview.md` in the repo root. Start the file with `<!-- Round N -->`. Include the diff scope, review lens, findings in priority order, and concrete recommended changes."

Then wait for the user to relay Codex's feedback or confirm that Codex has finished.

## Phase 2: Intake Feedback

Codex is instructed to write its review to `CodexReview.md` in the repository root. When the user says Codex is done (or after an MCP call returns), read `CodexReview.md` to pick up the full feedback. Before trusting the file, verify that its `<!-- Round N -->` comment matches the current round number.

If the file is missing, empty, or carries a stale round marker:
1. **MCP path**: send a `codex-reply` follow-up: "You did not write CodexReview.md. Please save your review now to CodexReview.md in the repo root, starting with `<!-- Round N -->`."
2. **Terminal / plugin path**: present a short follow-up prompt the user can paste into Codex: `Save your review to CodexReview.md in the repo root. Start with <!-- Round N -->. Overwrite any existing content.`
3. If the file is still missing, empty, or stale after the follow-up, fall back to the MCP tool result or ask the user to paste the feedback directly.

- When feedback arrives (from `CodexReview.md`, MCP response, or relayed by the user), acknowledge each point.
- Categorize each point as:
  - **Will fix** -- clear, actionable, and correct.
  - **Needs discussion** -- ambiguous or potentially wrong; ask the user before acting.
  - **Disagree** -- explain why and let the user decide.
- Present the categorized list and confirm with the user before making changes.
- If using MCP, use `codex-reply` for follow-up questions within the same review round.

## Root Review Sink

When a review produces substantial written feedback, save the latest review to `CodexReview.md` in the repository root in addition to replying in chat. Treat this file as a reusable scratch file for the current review round, not as a permanent archive. By default, overwrite the file completely on each new saved review rather than creating per-directory review files or appending multiple rounds, unless the user explicitly asks to preserve history.

The purpose of `CodexReview.md` is to let the user read, reuse, and forward the latest review without copy-pasting from chat. Keep the file in plain Markdown and make it directly useful on its own. Include:

- a `<!-- Round N -->` HTML comment on the first line (used by Phase 2 to verify freshness)
- the file or diff scope reviewed
- the review lens or context
- the main findings in priority order
- concrete recommended changes, with exact values when relevant

Do not stage, commit, or move `CodexReview.md` unless the user explicitly asks. Before the first review round, check whether `CodexReview.md` is excluded from git. Look in `.gitignore` and `.git/info/exclude`. If it is not excluded anywhere, append `CodexReview.md` to `.git/info/exclude` (a local, untracked ignore file) so that `git add -A` during the revision flow does not accidentally stage the scratch file. Do not edit `.gitignore` for this purpose, as that would introduce a tracked side-effect inside the review loop.

## Phase 3: Revise

- Address all "will fix" points and any "needs discussion" points the user approved.
- Stage the revised changes.
- Return to Phase 1 with an incremented round number.

## Phase 4: Conclude

The loop ends when:
- The user says the review is done or approved.
- Codex's feedback has no actionable issues.
- The user decides to stop iterating.
- **MCP mode only**: The round count reaches 3. After 3 rounds, stop iterating and present the remaining feedback for the user to decide. This prevents infinite fix-and-challenge loops. The user can explicitly say "continue" to allow more rounds.

At conclusion, present a short summary: total rounds, key changes made, and any unresolved points from the last review.

## When Not To Use

- Trivial changes where review adds no value (typo fixes, config tweaks).
- Changes that require running tests or builds to validate -- run those first, then review.
- When the user wants a single-shot review with no revision loop; just ask Codex directly.
