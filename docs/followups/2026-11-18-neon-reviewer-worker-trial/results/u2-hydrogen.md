# u2-hydrogen result
Conclusion: Gemini 4 Neon launched on November 18, 2026 (512K context in Antigravity, 1M unified context at $3.00/$0.15/$15.00 per 1M tokens in the Gemini API, paired with Hydrogen in Orchestrator (Neon)), while Google has made no first-party statement retiring, deprecating, or replacing Gemini 4 Argon in Antigravity, the Gemini app, or the API.
Files: none
Open items: none
Verification: Verified all facts directly against fetched public web pages via `curl` (HTTP statuses recorded below) and `search_web` queries on 2026-11-18.

---

## 1. Release date of Gemini 4 Neon
* **November 18, 2026**
  * **Sources:**
    * https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/ (dated `Nov 18, 2026`; "Gemini 4 Neon is rolling out today")
    * https://antigravity.google/blog/gemini-4-neon-in-google-antigravity (dated `Nov 18, 2026`; "Today, we’re rolling out Gemini 4 Neon inside Google Antigravity.")
    * https://deepmind.google/models/model-cards/gemini-4-neon/ (`Published 18 November 2026`)
    * https://aistudio.google.com/docs/changelog (under `November 18, 2026`)
    * https://aistudio.google.com/docs/deprecations (`gemini-4-neon` Release date: `November 18, 2026`)

## 2. Google AI plans that get Neon in Antigravity (and which do not)
Per https://antigravity.google/docs/models/, https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301, https://antigravity.google/pricing/, and https://antigravity.google/docs/enterprise/:
* **Included:**
  * **Google AI Ultra:** Includes both **Gemini 4 Neon** and **Orchestrator (Neon)**.
  * **Google AI Pro (paid):** Includes both **Gemini 4 Neon** and **Orchestrator (Neon)**.
  * **Google AI Pro (trial with eligible premium devices):** Includes both **Gemini 4 Neon** and **Orchestrator (Neon)** (marked `†`: "Available with paid Google AI Pro plans or on trial with eligible premium devices").
  * **Gemini Enterprise (Gemini for business):** Includes **Gemini 4 Neon**, but **not** `Orchestrator (Neon)`.
* **Not included:**
  * **Free** plan (neither Gemini 4 Neon nor Orchestrator (Neon)).
  * **Google AI Plus** plan (neither Gemini 4 Neon nor Orchestrator (Neon)).
  * **Google AI Pro (standard trials without eligible premium devices)** (excluded by the `†` condition).

## 3. Antigravity CLI model slugs for Neon, thinking levels, and default level
Per https://antigravity.google/docs/cli/headless/, https://antigravity.google/docs/models/, https://antigravity.google/docs/cli/commands/effort/, and https://antigravity.google/docs/enterprise/:
* **CLI model slugs (`agy --model <slug>`):**
  * `gemini-4-neon-low` — Gemini 4 Neon (Low)
  * `gemini-4-neon-medium` — Gemini 4 Neon (Medium)
  * `gemini-4-neon-high` — Gemini 4 Neon (High)
  * `gemini-4-neon-xhigh` — Gemini 4 Neon (XHigh)
  * Base/Enterprise CLI identifier: `gemini-4-neon` (effort can also be passed separately with `--effort` / `/effort`).
  * Orchestrator (Neon) CLI slug: `gemini-pro-orchestrator-neon` (and `--model "Orchestrator (Neon)"` is also shown in https://antigravity.google/docs/models/).
* **Thinking / effort levels:** `Low` (`low`), `Medium` (`medium`), `High` (`high`), and `Extra` (`xhigh` in the CLI).
* **Default thinking level:** **High** (`high`). (In Antigravity, Gemini 4 Neon is also the default model for new conversations on plans that include it if no model has been chosen yet.)

## 4. Context window in Antigravity vs. Gemini API
* **In Antigravity:** **Up to 512K tokens**
  * Sources: https://antigravity.google/docs/models/ ("Context window: Up to 512K tokens."), https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301 ("Context window of up to 512K tokens in Antigravity.")
* **In the Gemini API:** **1 million tokens (`1,048,576` tokens)** unified input and output context window, with `65,536` default synchronous max output tokens and up to `1,048,576` output tokens via long decode (`background=true` or continuation).
  * Sources: https://aistudio.google.com/docs/models/gemini-4-neon, https://aistudio.google.com/docs/whats-new-gemini-4-neon, https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/, https://deepmind.google/models/model-cards/gemini-4-neon/

## 5. Gemini API price per million tokens (input, cached input, output)
Per https://aistudio.google.com/docs/pricing#gemini-4-neon, https://aistudio.google.com/docs/whats-new-gemini-4-neon, and https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/:
* **Free Tier:** Not available.
* **Standard Paid Tier (per 1M tokens, USD):**
  * **Input:** **$3.00**
  * **Cached input (Context caching):** **$0.15** (95% discount; implicit caching only—explicit caching is not supported)
  * **Output (including thinking tokens):** **$15.00**
* **Other API service tiers on https://aistudio.google.com/docs/pricing:**
  * **Batch / Flex:** $1.50 input / $0.075 cached input / $7.50 output per 1M tokens.
  * **Priority:** $5.40 input / $0.27 cached input / $27.00 output per 1M tokens.

## 6. What "Orchestrator (Neon)" is
Per https://antigravity.google/docs/models/, https://antigravity.google/blog/gemini-4-neon-in-google-antigravity, and https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301:
* **Orchestrator (Neon)** is an Antigravity model-selector configuration that pairs two Gemini 4 models inside a single conversation—**Gemini 4 Neon** as the **planner/reviewer** and **Gemini 4 Hydrogen** as the fast **implementation/executor**—handing control back and forth automatically within a turn rather than routing an entire prompt upfront:
  1. **Planning:** Gemini 4 Neon begins with a read-only planning phase to explore the codebase, resolve ambiguities, and write an implementation plan (including re-planning triggers), or answers questions/reviews directly if no edits are needed.
  2. **Execution:** Gemini 4 Hydrogen performs file edits, writes code, updates packages, runs builds and tests, and verifies results against the plan.
  3. **Handoff back & progress review:** If Hydrogen hits friction (e.g., a verification step failing twice, unexpected interface behavior, or an unsettled design choice), it returns control to Neon to inspect conversation state, repair the plan, and resume execution. On longer tasks or when the user sends a message mid-run, Hydrogen reports progress to Neon to review and wrap up, continue, or revise the plan.
* It runs with a **fixed configuration** (thinking level / `--effort` and `/effort` are not adjustable for Orchestrator).

## 7. Status of Gemini 4 Argon (retired, deprecated, or replaced?)
* **First-party Google status:** **No first-party Google statement exists** saying that Gemini 4 Argon is retired, deprecated, or replaced in Antigravity, the Gemini app, or the Gemini API.
  * **Gemini API (`https://aistudio.google.com/docs/deprecations`):** `gemini-4-argon` is listed in the active `Gemini 4 models` table with Release date `October 13, 2026`, Shutdown date `No shutdown date announced`, and an empty `Recommended replacement` field. (While `https://aistudio.google.com/docs/choosing-a-model` spotlights Carbon, Neon, Hydrogen, and 3.5 Flash-Lite in its comparison table, `gemini-4-argon` remains an active model in `https://aistudio.google.com/docs/models`, `https://aistudio.google.com/docs/models/gemini-4-argon`, and `https://aistudio.google.com/docs/pricing`.)
  * **Google Antigravity (`https://antigravity.google/docs/models/`, `https://antigravity.google/docs/enterprise/`, `https://antigravity.google/docs/cli/headless/`, `https://antigravity.google/pricing/`):** Both **Gemini 4 Argon** (`gemini-4-argon-high`, `gemini-4-argon-medium`) and **Orchestrator (Argon)** (`gemini-pro-orchestrator-argon`) remain actively listed and supported on Google AI Pro (paid or eligible-device trial), Google AI Ultra, and Gemini Enterprise (Gemini 4 Argon). The November 18, 2026 removal footnote on `antigravity.google/docs/models/` (`* Will be removed on November 18, 2026.`) applies only to Claude Sonnet 4.6 (thinking), Claude Opus 4.6 (thinking), and GPT-OSS-120b, not Gemini 4 Argon.
  * **Gemini app (`https://gemini.google/release-notes/`, `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/`):** Neither page states that Gemini 4 Argon is retired, deprecated, or replaced in the Gemini app. (Google's `introducing-gemini-4-neon` blog post mentions Gemini 4 Argon only in an example of building a 3D lab bench visualizing the model names.)
* **Third-party claims (kept separate from first-party statements):**
  * **9to5Google (third-party news):** https://9to5google.com/2026/11/18/gemini-4-neon-announcement/ claims regarding the Gemini app: *"As such, Neon is available in the Gemini app for AI Pro (and AI Ultra) subscribers, with 3.1 Pro finally going away. Neon also replaces Argon."* — **Unconfirmed by any first-party Google page.**
  * **GitHub Blog (third-party platform changelog):** https://github.blog/changelog/2026-11-13-upcoming-deprecation-of-selected-github-copilot-models-in-december/ announces a **GitHub Copilot** model deprecation (not a Google Antigravity, Gemini app, or Gemini API retirement): *"We will deprecate the following models across all GitHub Copilot experiences (including Copilot Chat, inline edits, ask and agent modes, and code completions) on December 14, 2026:"* listing `Gemini 4 Argon` (`2026-12-14`, suggested alternative `Gemini 4 Carbon`).

---

## Fetched URLs and HTTP Statuses

### First-party URLs fetched
* `https://antigravity.google/docs/models/` — **HTTP 200**
* `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity` — **HTTP 200**
* `https://antigravity.google/docs/cli/commands/effort/` — **HTTP 200**
* `https://antigravity.google/docs/cli/headless/` — **HTTP 200**
* `https://antigravity.google/docs/cli/reference/` — **HTTP 200**
* `https://antigravity.google/docs/cli/using/` — **HTTP 200**
* `https://antigravity.google/docs/cli/prompting/` — **HTTP 200**
* `https://antigravity.google/docs/cli/best-practices/` — **HTTP 200**
* `https://antigravity.google/docs/plans/` — **HTTP 200**
* `https://antigravity.google/docs/enterprise/` — **HTTP 200**
* `https://antigravity.google/pricing/` — **HTTP 200**
* `https://antigravity.google/docs/changelog` (and `https://antigravity.google/changelog` redirecting to `/docs/changelog`) — **HTTP 200**
* `https://antigravity.google/blog/changes-to-antigravity-plans/` — **HTTP 200**
* `https://antigravity.google/docs/sdk/local-models/` — **HTTP 200**
* `https://antigravity.google/llms.txt` — **HTTP 200**
* `https://antigravity.google/sitemap.xml` — **HTTP 200**
* `https://antigravity.google/docs/resources/plans/` — **HTTP 404**
* `https://antigravity.google/docs/cli/commands/` — **HTTP 404**
* `https://antigravity.google/docs/cli/commands/model/` — **HTTP 404**
* `https://antigravity.google/docs/models/index.md` — **HTTP 404**
* `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` — **HTTP 200**
* `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` — **HTTP 200**
* `https://deepmind.google/models/model-cards/gemini-4-neon/` — **HTTP 200**
* `https://aistudio.google.com/docs/models/gemini-4-neon` — **HTTP 200**
* `https://aistudio.google.com/docs/whats-new-gemini-4-neon` — **HTTP 200**
* `https://aistudio.google.com/docs/models/gemini-4-argon` — **HTTP 200**
* `https://aistudio.google.com/docs/whats-new-gemini-4-argon` — **HTTP 200**
* `https://aistudio.google.com/docs/whats-new-gemini-4-carbon` — **HTTP 200**
* `https://aistudio.google.com/docs/whats-new-gemini-4-hydrogen` — **HTTP 200**
* `https://aistudio.google.com/docs/pricing` (also `https://ai.google.dev/gemini-api/docs/pricing` -> HTTP **200** final `https://aistudio.google.com/docs/pricing`) — **HTTP 200**
* `https://aistudio.google.com/docs/deprecations` (also `https://ai.google.dev/gemini-api/docs/deprecations` -> HTTP **200** final `https://aistudio.google.com/docs/deprecations`) — **HTTP 200**
* `https://aistudio.google.com/docs/changelog` — **HTTP 200**
* `https://aistudio.google.com/docs/choosing-a-model` — **HTTP 200**
* `https://aistudio.google.com/docs/latest-model` — **HTTP 200**
* `https://aistudio.google.com/docs/models` (also `https://ai.google.dev/gemini-api/docs/models` -> HTTP **200** final `https://aistudio.google.com/docs/models`) — **HTTP 200**
* `https://gemini.google/release-notes/` — **HTTP 200**
* `https://gemini.google.com/updates` — **HTTP 200**

### Third-party URLs fetched
* `https://9to5google.com/2026/11/18/gemini-4-neon-announcement/` — **HTTP 200**
* `https://github.blog/changelog/2026-11-13-upcoming-deprecation-of-selected-github-copilot-models-in-december/` — **HTTP 200**

### Additional candidate URLs considered (resolved via grounding redirects, not parsed in full)
* `https://antigravity.google/blog/gemini-4-argon-in-google-antigravity/` (HTTP 200 on redirect resolution)
* `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-argon/` (HTTP 200 on redirect resolution)
* `https://discuss.ai.google.dev/t/gemini-4-argon-ultra/188901` (HTTP 200 on redirect resolution)
* `https://discuss.ai.google.dev/t/using-antigravity-with-gemini-4-argon-medium/190052` (HTTP 200 on redirect resolution)
* `https://cloud.google.com/model-garden/pricing` (HTTP 200 on redirect resolution)
