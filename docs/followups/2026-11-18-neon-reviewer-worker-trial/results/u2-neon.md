# u2-neon result
Conclusion: Gemini 4 Neon launched on November 18, 2026 across Antigravity (512K context; Ultra, paid Pro, eligible premium-device Pro trials, and Enterprise), the Gemini API (1M unified context; $3/$0.15/$15 per 1M input/cached/output tokens), and the Gemini app; no first-party Google statement declares Gemini 4 Argon retired, deprecated, or replaced in Antigravity, the Gemini app, or the API (though 9to5Google reports Neon replaces Argon in the Gemini app picker—unconfirmed by first-party pages).
Files: none
Open items: Unconfirmed from first-party Google pages whether Gemini 4 Argon has been removed from the consumer Gemini app model picker (only reported by third-party coverage; `gemini.google/release-notes/` has not yet posted a November 18, 2026 entry).
Verification: Web searches via `search_web` plus direct HTTP fetches (`curl` / Python `urllib.request`) of 36 candidate URLs across `blog.google`, `antigravity.google`, `discuss.ai.google.dev`, `ai.google.dev`, `aistudio.google.com`, `deepmind.google`, `gemini.google`, `support.google.com`, `9to5google.com`, and `reddit.com`.

---

## Findings (First-Party Sources)

### 1. Release date of Gemini 4 Neon
- **November 18, 2026** (general availability / rollout start across Google Antigravity, Gemini API / Google AI Studio, Gemini for business, and the Gemini app).
- **Sources:**
  - `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` (dated `Nov 18, 2026`)
  - `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity/` (dated `Nov 18, 2026`)
  - `https://antigravity.google/docs/changelog/` (`Model launch · November 18, 2026`)
  - `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (posted `November 18, 2026`)
  - `https://deepmind.google/models/model-cards/gemini-4-neon/` (`Published 18 November 2026`)
  - `https://aistudio.google.com/docs/deprecations.md` and `https://aistudio.google.com/docs/changelog.md` (`November 18, 2026`, `gemini-4-neon` GA)

### 2. Which Google AI plans get Neon in Antigravity, and which do not
- **Included (get Gemini 4 Neon in Antigravity):**
  - **Google AI Ultra** — included (also includes Orchestrator (Neon)).
  - **Google AI Pro (paid)** — included (also includes Orchestrator (Neon)).
  - **Google AI Pro (trial) with eligible premium devices** — included only on trials tied to eligible premium devices (also includes Orchestrator (Neon)).
  - **Enterprise (Gemini Enterprise / Gemini for business)** — standalone Gemini 4 Neon is included; **Orchestrator (Neon) is not included** on Enterprise.
- **Not included (do NOT get Gemini 4 Neon in Antigravity):**
  - **Free** plans.
  - **Google AI Plus** plans.
  - **Google AI Pro (trial)** plans *without* an eligible premium device (users on such trials must switch to a paid Google AI Pro plan).
  - *(Note: Standard Google Workspace plans do not include Antigravity plans or higher rate limits; organizational access is via Gemini Enterprise / Gemini for business.)*
- **Sources:**
  - `https://antigravity.google/docs/models/` (reasoning model & Orchestrator plan availability tables)
  - `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` ("Who gets what" table)
  - `https://antigravity.google/docs/enterprise/` (Enterprise supported models table)
  - `https://antigravity.google/docs/plans/` (Workspace note)

### 3. Antigravity CLI model slugs for Neon, thinking levels, and default level
- **Per-level Antigravity CLI model slugs** (documented verbatim under `agy models`):
  - `gemini-4-neon-low` — Gemini 4 Neon (Low)
  - `gemini-4-neon-medium` — Gemini 4 Neon (Medium)
  - `gemini-4-neon-high` — Gemini 4 Neon (High)
  - `gemini-4-neon-xhigh` — Gemini 4 Neon (XHigh) *(labeled **Extra** in the UI model selector)*
- **Base model identifier & effort flag:**
  - Base CLI / API identifier: `gemini-4-neon` (listed in the Enterprise CLI/API table; CLI also supports selecting effort via `--effort <level>` or `/effort <level>` with `low`, `medium`, `high`, `xhigh`, e.g., `--model gemini-4-neon-xhigh` or `--effort xhigh`).
- **Orchestrator (Neon) CLI slug:**
  - `gemini-pro-orchestrator-neon` — Orchestrator (Neon) (also selectable via `--model "Orchestrator (Neon)"`; fixed configuration where `--effort` / `/effort` do not apply).
- **Default thinking level:**
  - **`high`** (`High` / `gemini-4-neon-high`).
- **Sources:**
  - `https://antigravity.google/docs/cli/headless/` (`agy models` slug list)
  - `https://antigravity.google/docs/models/` (thinking levels, default `High`, CLI `low`/`medium`/`high`/`xhigh`, `--model gemini-4-neon-xhigh`, `--model "Orchestrator (Neon)"`)
  - `https://antigravity.google/docs/enterprise/` (`gemini-4-neon` base CLI/API identifier)
  - `https://antigravity.google/docs/cli/commands/effort/` (`/effort` and `--effort` behavior)
  - `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301`

### 4. Neon's context window in Antigravity vs. Gemini API
- **Google Antigravity:** **Up to 512K tokens**.
  - Sources: `https://antigravity.google/docs/models/`, `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301`
- **Gemini API (and Google AI Studio):** **1,048,576 tokens (1M tokens) unified context window** (shared across input, thinking, and output tokens; default synchronous max output is 65,536 tokens / 64K, extendable up to 1,048,576 tokens via long decode).
  - Sources: `https://aistudio.google.com/docs/models/gemini-4-neon.md`, `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md`, `https://deepmind.google/models/model-cards/gemini-4-neon/`, `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/`

### 5. Gemini API price per million tokens (input, cached input, output)
Gemini 4 Neon (`gemini-4-neon`) is **not available on the Free tier** and has no introductory promotional pricing. Paid tier pricing per 1M tokens (USD):

| Tier | Input | Cached input (implicit only; explicit caching not supported) | Output (including thinking tokens) |
| :--- | :--- | :--- | :--- |
| **Standard** | **$3.00** | **$0.15** (95% discount) | **$15.00** |
| **Batch** | $1.50 | $0.075 | $7.50 |
| **Flex** | $1.50 | $0.075 | $7.50 |
| **Priority** | $5.40 | $0.27 | $27.00 |

- **Sources:**
  - `https://aistudio.google.com/docs/pricing.md` (canonical target of `https://ai.google.dev/gemini-api/docs/pricing.md.txt`)
  - `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/`
  - `https://aistudio.google.com/docs/choosing-a-model.md` ("Neon has no introductory price.")

### 6. What "Orchestrator (Neon)" is
- **Orchestrator (Neon)** is a model selector option in Google Antigravity (`gemini-pro-orchestrator-neon` in the CLI) that pairs **two Gemini 4 models within a single conversation / single agent**: **Gemini 4 Neon** as the planner/reviewer and **Gemini 4 Hydrogen** as the fast implementation executor.
- It is **not** a one-shot prompt router; both models hand control back and forth within each turn:
  1. **Planning:** Gemini 4 Neon starts with a read-only planning phase to explore the codebase, resolve ambiguities, and write a concrete implementation plan (including re-planning triggers). For pure questions/explanations/reviews, Neon answers directly.
  2. **Execution:** Gemini 4 Hydrogen takes over to apply file edits, write code, update packages, run builds/tests, and verify results against the plan.
  3. **Escalation & review:** If Hydrogen hits friction (e.g., a verification step failing twice, unexpected interface behavior, or an unsettled design choice), it hands control back to Neon to inspect conversation state, repair the plan, and resume on Hydrogen. On longer tasks or mid-run user messages, Hydrogen reports progress to Neon to review, continue, or revise.
- It uses a **fixed configuration** (thinking level / `--effort` / `/effort` cannot be adjusted), runs a single agent in the conversation (unlike parallel multi-agent features such as subagents, `/swarm`, `/boost`, or `/teamwork`), and is available on Google AI Ultra, paid Google AI Pro, and eligible premium-device Pro trials (not Free, Plus, non-eligible trials, or Enterprise).
- **Sources:**
  - `https://antigravity.google/docs/models/`
  - `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity/`
  - `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301`

### 7. Status of Gemini 4 Argon (retired, deprecated, or replaced?)

#### First-party Google statements
**No first-party Google statement exists saying that Gemini 4 Argon is retired, deprecated, or replaced in Google Antigravity, the Gemini API, or the Gemini app.**

- **Google Antigravity:** Still listed as an active, supported model.
  - On `https://antigravity.google/docs/models/`, **Gemini 4 Argon** (`Low`, `Medium`, `High`) and **Orchestrator (Argon)** remain active in the model availability table (Argon: `✅ †` Pro, `✅` Ultra, `✅` Enterprise; Orchestrator (Argon): `✅ †` Pro, `✅` Ultra).
  - On `https://antigravity.google/docs/cli/headless/`, `agy models` still includes `gemini-4-argon-high`, `gemini-4-argon-medium`, and `gemini-pro-orchestrator-argon`.
  - The only models marked for removal on `https://antigravity.google/docs/models/` are Claude Sonnet 4.6 (thinking), Claude Opus 4.6 (thinking), and GPT-OSS-120b (`* Will be removed on November 18, 2026.`).
  - Neon does become the default for new conversations where no model was previously chosen ("it becomes the default model for new conversations on plans that include it" — `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301`), but Google does not state Argon is retired, deprecated, or removed.
- **Gemini API:** Not deprecated, retired, or assigned a replacement.
  - `https://aistudio.google.com/docs/deprecations.md` (canonical target of `https://ai.google.dev/gemini-api/docs/deprecations.md.txt`) lists `gemini-4-argon` in the active **Gemini 4 models** table with Release date `October 13, 2026`, Shutdown date **`No shutdown date announced`**, and an empty **Recommended replacement** cell.
  - `https://aistudio.google.com/docs/models.md`, `https://aistudio.google.com/docs/models/gemini-4-argon.md`, and `https://aistudio.google.com/docs/pricing.md` all still list `gemini-4-argon` as an active Stable model (with its scheduled transition from introductory $2/$10/$0.10 pricing to $4/$20/$0.20 on December 1, 2026).
  - *(Contextual observation, not a deprecation statement: Google's curated comparison pages `https://aistudio.google.com/docs/latest-model.md` and `https://aistudio.google.com/docs/choosing-a-model.md` currently highlight Carbon, Neon, Hydrogen, and Gemini 3.5 Flash-Lite without listing Argon, and `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md` includes a "Migrate from Gemini 4 Carbon, Argon, or Hydrogen" subsection, but none of these pages state that Argon is deprecated, retired, or replaced.)*
- **Gemini app:** No first-party statement found.
  - `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` mentions Argon only in a Blender MCP demo caption and says nothing about retiring or replacing Argon in the Gemini app.
  - `https://gemini.google/release-notes/` (latest entry `2026.11.17`) has no November 18, 2026 Neon entry and no statement retiring/replacing Argon.
  - Whether Argon was removed from the Gemini app model picker is **unconfirmed** from first-party Google pages.

#### Third-party claims (separate from first-party sources)
- **9to5Google** (`https://9to5google.com/2026/11/18/gemini-4-neon-announcement/`, Abner Li, Nov 18, 2026) claims regarding the **Gemini app** model picker: *"As such, Neon is available in the Gemini app for AI Pro (and AI Ultra) subscribers, with 3.1 Pro finally going away. Neon also replaces Argon."* and describes the updated Gemini app picker as Auto, Everyday help (4 Hydrogen), Deeper analysis (4 Neon), and Code & complex work (4 Carbon). **Unconfirmed from first-party pages.**
- **Reddit** (`https://www.reddit.com/r/GeminiAI/comments/1xzq3hn/google_just_released_gemini_4_neon_nearcarbon/`, returned HTTP 403 on direct fetch; surfaced in search summaries) contains community discussion claiming Neon supersedes/replaces Argon in model pickers. **Unconfirmed from first-party pages.**

---

## Candidate URLs Considered & HTTP Fetch Status

### First-party URLs fetched
| URL | HTTP Status | Notes / Final URL |
| :--- | :--- | :--- |
| `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` | 200 | Primary Google launch blog post |
| `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-hydrogen/` | 200 | Resolved via `curl -I` |
| `https://deepmind.google/models/model-cards/gemini-4-neon/` | 200 | Official Gemini 4 Neon Model Card |
| `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` | 200 | Official Antigravity team announcement post |
| `https://discuss.ai.google.dev/t/4-out-of-4-gemini-4-models-blocked-now-including-gemini-4-neon-another-claude-4-6-extension-to-nov-30-stop-treating-jio-google-ai-pro-users-like-we-don-t-exist/202287` | 200 | Community forum thread (resolved via `curl -I`) |
| `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity/` | 200 | Official Antigravity Neon blog post |
| `https://antigravity.google/blog/gemini-4-argon-in-google-antigravity/` | 200 | Official Antigravity Argon blog post |
| `https://antigravity.google/blog/` | 200 | Antigravity blog index |
| `https://antigravity.google/docs/models/` | 200 | Official Antigravity model & plan matrix + Orchestrator docs |
| `https://antigravity.google/docs/features/` | 200 | Antigravity features page |
| `https://antigravity.google/docs/plans/` | 200 | Antigravity plans & quotas page |
| `https://antigravity.google/docs/enterprise/` | 200 | Antigravity Enterprise supported models & CLI/API IDs |
| `https://antigravity.google/changelog/` | 200 | HTML redirect to `/docs/changelog` |
| `https://antigravity.google/docs/changelog/` | 200 | Antigravity changelog (Nov 18, 2026 Neon launch entry) |
| `https://antigravity.google/docs/cli/reference/` | 200 | Antigravity CLI flags & settings reference |
| `https://antigravity.google/docs/cli/commands/effort/` | 200 | Antigravity CLI `/effort` and `--effort` docs |
| `https://antigravity.google/docs/cli/using/` | 200 | Antigravity CLI usage docs |
| `https://antigravity.google/docs/cli/headless/` | 200 | Antigravity CLI headless docs (contains exact `agy models` slug list) |
| `https://ai.google.dev/gemini-api/docs/models` | 200 | Redirects to `https://aistudio.google.com/docs/models` |
| `https://ai.google.dev/gemini-api/docs/models/gemini-4-neon.md.txt` | 200 | Redirects to `https://aistudio.google.com/docs/models/gemini-4-neon.md` |
| `https://ai.google.dev/gemini-api/docs/pricing` | 200 | Redirects to `https://aistudio.google.com/docs/pricing` |
| `https://ai.google.dev/gemini-api/docs/pricing.md.txt` | 200 | Redirects to `https://aistudio.google.com/docs/pricing.md` |
| `https://ai.google.dev/gemini-api/docs/deprecations` | 200 | Redirects to `https://aistudio.google.com/docs/deprecations` |
| `https://ai.google.dev/gemini-api/docs/deprecations.md.txt` | 200 | Redirects to `https://aistudio.google.com/docs/deprecations.md` |
| `https://aistudio.google.com/docs/models.md` | 200 | Gemini API models catalog |
| `https://aistudio.google.com/docs/models/gemini-4-neon` | 200 | SPA shell; markdown fetched at `.md` |
| `https://aistudio.google.com/docs/models/gemini-4-neon.md` | 200 | Full Gemini 4 Neon API specification |
| `https://aistudio.google.com/docs/models/gemini-4-argon` | 200 | SPA shell; markdown fetched at `.md` |
| `https://aistudio.google.com/docs/models/gemini-4-argon.md` | 200 | Full Gemini 4 Argon API specification |
| `https://aistudio.google.com/docs/pricing` | 200 | SPA shell; markdown fetched at `.md` |
| `https://aistudio.google.com/docs/pricing.md` | 200 | Full Gemini API pricing tables (Neon & Argon) |
| `https://aistudio.google.com/docs/deprecations` | 200 | SPA shell; markdown fetched at `.md` |
| `https://aistudio.google.com/docs/deprecations.md` | 200 | Official Gemini API deprecations & shutdown tracker |
| `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md` | 200 | Gemini 4 Neon API guide & migration notes |
| `https://aistudio.google.com/docs/choosing-a-model.md` | 200 | Gemini API model selection guide |
| `https://aistudio.google.com/docs/latest-model.md` | 200 | Latest Gemini models comparison |
| `https://aistudio.google.com/docs/changelog.md` | 200 | Gemini API release notes |
| `https://gemini.google/release-notes/` | 200 | Gemini app release notes (latest entry `2026.11.17`) |
| `https://support.google.com/gemini/answer/16275805` | 200 | Gemini Help Center article (no Neon/Argon mention) |

### Third-party URLs considered / fetched (checked only to separate third-party Argon claims)
| URL | HTTP Status | Notes |
| :--- | :--- | :--- |
| `https://9to5google.com/2026/11/18/gemini-4-neon-announcement/` | 200 | Third-party article claiming Neon replaces Argon in the Gemini app picker |
| `https://www.reddit.com/r/GeminiAI/comments/1xzq3hn/google_just_released_gemini_4_neon_nearcarbon/` | 403 | Blocked on direct fetch; surfaced in search results |

*(Additional third-party search candidates considered and not relied upon because primary first-party sources were available: `artificialanalysis.ai`, `vals.ai`, `openrouter.ai`, `unite.ai`, `felloai.com`, `codedtx.com`, `ai-tldr.dev`, `cellcog.ai`, `neuraltrust.ai`, `thedefiant.io`, `cloudinsight.cc`, `github.blog`, `youtube.com`, `note.com`, `theaiconsultinglab.com`.)*
