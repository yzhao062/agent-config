# Swarm Report: Neon Audit, Research, and prun Fix

## Task 1

Conclusion: Zero hard-coded runtime defaults bypass `user/agent-models.json` (category `(d)`: 0 hits). Across all tracked files at `HEAD` (`53f9c1735dbd4edb43943dbffdbae15acf5bd042`) outside `user/agent-models.json`, there are 695 matching lines across 19 files naming a Gemini model family or slug: 4 lines in category `(a)` (code that reads the registry, docstring examples only), 310 lines in category `(b)` (test fixtures), 381 lines in category `(c)` (documentation or historical records), and 0 lines in category `(d)` (hard-coded runtime default bypassing the registry). Families `carbon`, `hydrogen`, and `neon` have 0 hits outside `user/agent-models.json` at `HEAD`. Concrete model literals outside `user/agent-models.json` are forbidden by `scripts/agent_models.py` (`LITERAL_PATTERNS` / `scan`), `tests/test_agent_models.py` (`DriftGuardTests`), per-dispatcher literal tests (`tests/test_dispatch_gemini.py`), and CI (`.github/workflows/validate.yml`), except in explicit allowlists and lines marked `agent-models: allow`. Replacing `families.agy.model` and `roles.reviewer.agy.fallback_model` in `user/agent-models.json` with another valid tierless Gemini stem breaks no local test or script; `user/settings.json` stays byte-identical; `scripts/check-parity.sh` requires mirroring `user/agent-models.json` to `anywhere-agents`; and on machines running bootstrap, `agent_models.py sync` backs up and updates `"model"` in `~/.gemini/antigravity-cli/settings.json` to the newest listed display name in the new family (or `gemini-4-hydrogen-high` if unlisted on that account).
Files: None modified (read-only audit of `HEAD` `53f9c17`). Key inspected files: `user/agent-models.json`, `user/settings.json`, `scripts/agent_models.py`, `scripts/render_banner.py`, `scripts/session_bootstrap.py`, `scripts/check-parity.sh`, `bootstrap/bootstrap.sh`, `bootstrap/bootstrap.ps1`, `skills/agent-models/SKILL.md`, `skills/implement-review/scripts/dispatch-gemini.py`, `skills/prun/scripts/dispatch-task-agy.py`, `tests/test_agent_models.py`, `tests/test_dispatch_gemini.py`, `tests/test_dispatch_task_agy.py`, `tests/test_dispatch_grok.py`, `tests/test_dispatch_task_grok.py`, `tests/test_repo.py`, `.github/workflows/validate.yml`, `.githooks/pre-push`, `AGENTS.md`, `ONBOARDING.md`, `docs/mac-mouse-preferences.md`, `docs/mac-storage-audit.md`, and `docs/followups/...`.
Open items: None for the audit. Operational note for any future registry switch: mirror `user/agent-models.json` identically to `anywhere-agents` (`scripts/check-parity.sh:176`) and verify the replacement family appears in `agy models` on signed-in accounts (`skills/agent-models/SKILL.md:107-109`).
Verification: Verified read-only with: (1) `git rev-parse HEAD && git status --short` (exit 0, `HEAD` `53f9c17`); (2) `git show HEAD:user/agent-models.json` (exit 0); (3) full-tree `git grep` and Python scan over `git ls-tree -r --name-only HEAD` / `git show HEAD:<path>` for `gemini-*`, `Gemini <ver> <family>`, `Gemini <family>`, and `\b(argon|carbon|hydrogen|neon|flash)\b` outside `user/agent-models.json` (exit 0, 695 genuine model-family/slug hit lines across 19 files; confirmed 0 hits in `CHANGELOG.md`); (4) `/Users/yzhao062/miniforge3/envs/py312/bin/python scripts/agent_models.py show` (exit 0); (5) `/Users/yzhao062/miniforge3/envs/py312/bin/python scripts/agent_models.py map .` (exit 0); (6) `/Users/yzhao062/miniforge3/envs/py312/bin/python scripts/agent_models.py render --check` (exit 0, `render --check OK`); (7) `/Users/yzhao062/miniforge3/envs/py312/bin/python scripts/agent_models.py scan skills scripts bootstrap AGENTS.md README.md ONBOARDING.md docs/mac-storage-audit.md` (exit 1; only 3 lines flagged, all in `scripts/agent_models.py` at `:18`, `:309`, `:844`, which `DRIFT_ALLOW_FILES` exempts); (8) `/Users/yzhao062/miniforge3/envs/py312/bin/python -m pytest -q tests/test_agent_models.py tests/test_dispatch_gemini.py tests/test_render_banner.py tests/test_repo.py tests/test_check_parity.py` (exit 0, `338 passed, 2 skipped, 114 subtests passed in 37.75s`); (9) `/Users/yzhao062/miniforge3/envs/py312/bin/python -m pytest -q tests/test_dispatch_grok.py tests/test_dispatch_task_grok.py` (exit 0, `38 passed, 19 subtests passed in 17.14s`); (10) read-only in-memory simulation replacing `families.agy.model` and `roles.reviewer.agy.fallback_model` with `"gemini-4-neon"` (exit 0; `agent_models.validate()` passed and `rendered_settings()` for `user/settings.json` remained byte-identical).

### 1. Complete `path:line` Classification Table at `HEAD` (`53f9c17`)

Legend: **(a)** code that reads the registry, **(b)** test fixture, **(c)** documentation or historical record, **(d)** hard-coded runtime default bypassing the registry.

#### Category (a): Code that reads the registry (4 lines across 2 files; docstring examples only)

| path:line | Class | Context |
|---|---|---|
| `scripts/agent_models.py:18` | (a) | CLI docstring example: `a family stem such as gemini-4-argon; --field slug gives the Agy slug` |
| `scripts/agent_models.py:309` | (a) | `display_to_slug` docstring example: `"""'Gemini 4 Argon (High)' -> 'gemini-4-argon-high'."""` |
| `skills/prun/scripts/dispatch-task-agy.py:642` | (a) | `newest_in_family` docstring example: `` `gemini-<version>-flash-high` is Gemini Flash. `` |
| `skills/prun/scripts/dispatch-task-agy.py:645` | (a) | `newest_in_family` docstring example: `different name is a different family: no lite or pro variant joins Flash.` |

At `HEAD`, `skills/implement-review/scripts/dispatch-gemini.py` reads `agy/reviewer` through `scripts/agent_models.py` at lines `47-80` and contains 0 Gemini model family or slug literals. `skills/prun/scripts/dispatch-task-agy.py` reads `agy/prun-worker` through `scripts/agent_models.py` at lines `86-127` and contains only the two docstring lines above.

#### Category (b): Test fixtures (310 lines across 6 files)

- `docs/followups/2026-09-18-skills-bloat-audit/fixture/tail:1` — `(b)` audit fixture init event (`"model": "gemini-3.8-flash-high"`).
- `tests/test_dispatch_grok.py:354, 805` — `(b)` temporary registry fixture (`"agy": {"model": "gemini-4-argon", "effort": "high"}`).
- `tests/test_dispatch_task_grok.py:34, 38` — `(b)` temporary registry fixture (`"agy": {"model": "gemini-4-argon", ...}` and `prun-worker.agy` `"gemini-3.8-flash"`).
- `tests/test_agent_models.py` (87 lines, all `(b)`):
  - `:50, :52, :61`: `FIXTURE` registry placeholders (`gemini-9-test`, `gemini-8-fast`).
  - `:153, :154, :155, :160, :167, :169, :174, :175, :177, :184, :192, :196, :197, :202, :207, :212, :220, :272`: `ResolveTests` assertions on placeholder stems (`gemini-9-test`, `gemini-8-fast`, `gemini-9-peak`).
  - `:367, :431, :441`: `ValidateTests` invalid stem and advisor cases (`gemini-8-fast-high`, `gemini-9-test`, `gemini-9-test-{tier}`).
  - `:620, :621, :626, :627, :630, :635`: `SetTests` role fallback tests (`gemini-9-peak`, `gemini-9-test`, `gemini-9-other`, `gemini-8-fast-high`).
  - `:796, :797, :800, :801, :802, :803, :804, :806, :811, :812, :814, :815, :816, :820, :822, :825, :826`: `AgySlugTests` (`Gemini 4 Argon (High)`, `Gemini 3.8 Flash (Low)`, `gemini-4-argon-*`, `gemini-4.1-argon-high`, `gemini-4.2-argon-low`, `gemini-4-5-argon-high`, `gemini-5-argon-high`, `gemini-4-flash-high`, `gemini-3.8-flash-high`, `gemini-9-test-high`).
  - `:853, :854, :855, :856, :857, :858`: `MatchesTests` (`gemini-9-test*`, `gemini-9.2-test-high`, `gemini-10-test-high`, `gemini-9-other-high`).
  - `:914, :915, :916, :918, :948, :952, :955`: `ActualReaderTests` (`gemini-4-argon-high`, `Gemini 3.8 Flash (Medium)`, `Gemini 4 Argon (High)`, `Gemini 9.2 Test (High)`, `gemini-9-test-high`, `gemini-9.2-test-high`).
  - `:1296`: `ScanTests` sample (`"slug gemini-9-test-high"`).
  - `:1419, :1420, :1421, :1424, :1427, :1429, :1435, :1438`: `SyncTests` mock `agy_listing` (`gemini-9-test-high`, `gemini-9.1-test-high`, `gemini-8-fast-high`, and display names).
  - `:1465`: `DoctorTests` mock settings (`"Gemini 9 Test (High)"`).
  - `:1681, :1684, :1694, :1695, :1697, :1698, :1700, :1701, :1703, :1795, :1797, :1798, :1813, :1814, :1815, :1819, :1821`: `ConfigEditSafetyTests` (`gemini-8-fast-*`, `gemini-9-test-*`, `gemini-9.2-test-high`, `Gemini 8 Fast`).
- `tests/test_dispatch_gemini.py` (102 lines, all `(b)`):
  - `:31, :32, :99, :187`: fixture constants (`FIXTURE_STEM = "gemini-4-argon"`, `FIXTURE_FALLBACK_STEM = "gemini-3.8-flash"`) and mock `agy` defaults (`gemini-4-argon-high`, `gemini-3.8-flash-high`).
  - `:625`: streaming init event fixture (`gemini-3.8-flash-high`).
  - `:651, :652, :654, :658, :659, :661, :668, :670, :671, :672, :675, :679, :680, :682, :688, :689, :691, :720, :721, :725, :727, :731, :734, :741, :742, :744, :748, :749, :751, :755, :756, :758, :764, :767`: `newest_in_family` unit test cases (`gemini-3.8-flash-high`, `gemini-3.9-flash-*`, `gemini-3.10-flash-high`, `gemini-4-flash-high`, `gemini-3.7-flash-high`, `gemini-1.0-flash-high`, `gemini-3-8-flash-high`, `gemini-3.8-flash-lite-high`, `gemini-3.8-pro-high`, `gemini-3.1-pro-high`, `gemini-flash`).
  - `:1090, :1114, :1115, :1120, :1123, :1135, :1144, :1157, :1185`: integration runs and error/override cases (`gemini-4-argon-high`, `gemini-3.1-pro-high`, `gemini-3.8-flash-high`).
  - `:1363, :1364, :1365, :1366, :1371, :1372, :1374, :1375, :1380, :1381, :1384, :1385, :1388, :1389, :1396, :1397, :1407, :1408, :1414, :1421, :1428, :1429, :1430, :1431, :1435, :1441, :1442, :1446, :1449, :1457, :1462, :1463`: preflight float, fallback, pin, and preflight-off tests (`gemini-4-argon-*`, `gemini-4.1-argon-*`, `gemini-3.8-flash-high`, `gemini-3.9-flash-*`, `gemini-3.1-pro-high`).
  - `:1534, :1538, :1544, :1559, :1561, :1566, :1567, :1584, :1586`: model-actual verification and env override tests (`gemini-4.1-argon-high`, `Gemini 3.8 Flash (High)`, `Gemini 4 Argon (Low)`, `gemini-3.1-pro-high`).
  - `:1631, :1634, :1639, :1641, :1683, :1685, :1690, :1691, :1695, :1700, :1701, :1716, :1719`: `--print-model` tests (`gemini-4-argon-*`, `gemini-4.1-argon-high`, `gemini-3.8-flash-high`, `gemini-3.9-flash-high`).
- `tests/test_dispatch_task_agy.py` at `HEAD` `53f9c17` (116 lines, all `(b)`):
  - `:28, :46, :104, :168`: temporary registry defaults (`worker_model="gemini-3.8-flash"`, `families.agy.model="gemini-4-argon"`) and mock `agy` defaults (`gemini-3.8-flash-high`).
  - `:219, :228, :233, :276`: registry-load and `model_pool` tests (`gemini-3.8-flash-high`, `gemini-9.9-spark`, `gemini-9.9-spark-low`).
  - `:288, :289, :291, :296, :297, :299, :304, :305, :307, :312, :313, :315, :319, :320, :322, :343, :344, :353, :354, :395, :397, :398, :406, :407, :409, :413, :414, :416, :421, :422, :424, :428, :429, :431`: `newest_in_family` unit tests (`gemini-3.8-flash-*`, `gemini-3.8.1-flash-high`, `gemini-3-8-flash-high`, `gemini-3.9-flash-*`, `gemini-3.10-flash-high`, `gemini-3.7-flash-high`, `gemini-4-flash-high`, `gemini-3.8-flash-lite-high`, `gemini-3.1-pro-high`).
  - `:938, :1161, :1166, :1175, :1186, :1201, :1223, :1246, :1320, :1345`: quota balancing and dispatch tests (`gemini-3.8-flash-high`, `gemini-3.1-pro-high`).
  - `:1490, :1491, :1492, :1499, :1500, :1505, :1508, :1514, :1515, :1517, :1560, :1561, :1562, :1569, :1570, :1573, :1580, :1586, :1597, :1614, :1615, :1624, :1658, :1692, :1693, :1700, :1705, :1711, :1719, :1727, :1732, :1733, :1738, :1745, :1746, :1751, :1752, :1757, :1772, :1778, :1783, :1787, :1809, :1811, :1816, :1825, :1830, :1841, :1861, :1869, :1874, :1902`: preflight float, fallback, tier, and override tests (`gemini-4-argon-high`, `gemini-4.1-argon-high`, `gemini-3.8-flash-*`, `gemini-3.9-flash-*`, `gemini-9.9-spark*`; comment at `:1514-1515` explains why unpinned units do not fall back to Argon).
  - `:1921, :1922, :1928, :1933, :1934, :1937, :1940, :1949, :1960, :1964, :1981, :2001`: `model-actual` verification tests (`gemini-3.8-flash-high`, `gemini-3.9-flash-high`, `gemini-4-argon-high`, `Gemini 4 Argon (High)`, `Gemini 3.8 Flash*`).

#### Category (c): Documentation or historical records (381 lines across 11 files)

| path:line | Class | Context |
|---|---|---|
| `ONBOARDING.md:172` | (c) | External repo workflow note: `$0 (gemini Flash free tier)` |
| `docs/mac-mouse-preferences.md:118` | (c) | Machine config snapshot: `` `Gemini 3.8 Flash (High)` `` in `~/.gemini/antigravity-cli/settings.json` |
| `docs/mac-storage-audit.md:108` | (c) | Historical audit record: `` `gemini-3.8-flash-high` `` (`<!-- agent-models: allow -->`) |
| `docs/followups/README.md:17` | (c) | Pilot index summary: `(Gemini Flash, Gemini Argon, Claude Sonnet, all Medium)` |
| `docs/followups/2026-08-22-grok-fourth-reviewer-evaluation.md:183` | (c) | SWR-Bench citation: `Gemini 2.5 Pro` and `Gemini 2.5 Flash` |
| `docs/followups/2026-08-22-grok-fourth-reviewer-evaluation.md:541` | (c) | SWR-Bench reference table: `Gemini 2.5 Pro`, `Gemini 2.5 Flash` |
| `docs/followups/2026-09-18-skills-bloat-audit.md:3` | (c) | Audit record: `(Gemini 3.8 Flash through prun, 5 to 10 minutes each)` |
| `docs/followups/2026-10-18-harness-slimming-audit.md:9` | (c) | Audit record: `Fifteen Agy units (Gemini 3.8 Flash High, prun)` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:26` | (c) | Pilot methods: `Gemini 3.8 Flash Medium and Gemini 4 Argon Medium` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:32` | (c) | Pilot table header: `Errors, Flash \| Errors, Argon \| ... (Flash / Argon)` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:34` | (c) | Pilot table row: `Flash declined F1 ... Argon's hook denied malformed input` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:40` | (c) | Pilot analysis: `Argon declined P3 ...` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:42` | (c) | Pilot analysis: `Argon's hook failed closed ...` / `Flash` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:56` | (c) | Pilot analysis: `one round-1 Argon README` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:60` | (c) | Pilot table caption: `Flash and Argon ran the round-1 tasks` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:70` | (c) | Pilot analysis: `Flash and Argon declined P3` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:72` | (c) | Pilot analysis: `Argon's hook failed closed ... Flash declined` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:78` | (c) | Pilot table header: `Mean lines per open coding unit \| Flash \| Argon \| Sonnet` |
| `docs/followups/2026-10-25-eu-guidance-pilot.md:84` | (c) | Pilot analysis: `shortest code with Argon ... shortened Flash ... lengthened Argon's` |
| `docs/followups/2026-10-25-eu-guidance-pilot/scripts/tasks.py:189` | (c) | Archived pilot experiment subjects: `MODELS = {"flash": "gemini-3.8-flash-medium", "argon": "gemini-4-argon-medium"}` |
| `docs/followups/2026-10-25-eu-guidance-pilot/scripts/tasks.py:282` | (c) | Archived pilot round-2 subjects: `MODELS2 = {"flash": "gemini-3.8-flash-medium", "argon": "gemini-4-argon-medium", ...}` |
| `docs/followups/2026-10-25-eu-guidance-pilot/round1/scores.json` (96 lines: 48 pairs `8-9, 24-25, 42-43, 66-67, 82-83, 98-99, 114-115, 148-149, 172-173, 205-206, 229-230, 262-263, 286-287, 302-303, 320-321, 344-345, 360-361, 376-377, 409-410, 442-443, 475-476, 495-496, 511-512, 535-536, 568-569, 584-585, 600-601, 624-625, 640-641, 656-657, 680-681, 713-714, 731-732, 747-748, 765-766, 785-786, 809-810, 833-834, 857-858, 873-874, 906-907, 930-931, 963-964, 981-982, 997-998, 1015-1016, 1031-1032, 1064-1065`) | (c) | Historical round-1 score records: paired `"model": "flash"\|"argon"` and `"model_ran": "gemini-3.8-flash-medium"\|"gemini-4-argon-medium"` |
| `docs/followups/2026-10-25-eu-guidance-pilot/round2/scores.json` (264 lines: 132 pairs `40-41, 64-65, 120-121, 191-192, 214-215, 230-231, 285-286, 321-322, 356-357, 372-373, 396-397, 412-413, 506-507, 522-523, 538-539, 560-561, 642-643, 755-756, 771-772, 794-795, 833-834, 849-850, 867-868, 940-941, 956-957, 988-989, 1004-1005, 1026-1027, 1048-1049, 1084-1085, 1119-1120, 1135-1136, 1240-1241, 1295-1296, 1311-1312, 1329-1330, 1345-1346, 1380-1381, 1396-1397, 1453-1454, 1492-1493, 1514-1515, 1530-1531, 1581-1582, 1603-1604, 1619-1620, 1643-1644, 1659-1660, 1699-1700, 1763-1764, 1808-1809, 1824-1825, 1840-1841, 1864-1865, 1880-1881, 1896-1897, 1918-1919, 1941-1942, 1964-1965, 1999-2000, 2050-2051, 2090-2091, 2112-2113, 2128-2129, 2152-2153, 2200-2201, 2255-2256, 2277-2278, 2293-2294, 2309-2310, 2332-2333, 2367-2368, 2391-2392, 2430-2431, 2446-2447, 2462-2463, 2494-2495, 2518-2519, 2534-2535, 2557-2558, 2581-2582, 2604-2605, 2620-2621, 2643-2644, 2659-2660, 2675-2676, 2697-2698, 2729-2730, 2768-2769, 2791-2792, 2815-2816, 2833-2834, 2849-2850, 2883-2884, 2906-2907, 2922-2923, 3016-3017, 3071-3072, 3110-3111, 3133-3134, 3156-3157, 3172-3173, 3207-3208, 3229-3230, 3269-3270, 3301-3302, 3333-3334, 3372-3373, 3388-3389, 3404-3405, 3420-3421, 3436-3437, 3459-3460, 3494-3495, 3540-3541, 3563-3564, 3581-3582, 3621-3622, 3644-3645, 3691-3692, 3707-3708, 3746-3747, 3769-3770, 3804-3805, 3820-3821, 3836-3837, 3875-3876, 3915-3916, 3931-3932, 3947-3948, 3979-3980, 4018-4019`) | (c) | Historical round-2 score records: paired `"model": "flash"\|"argon"` and `"model_ran": "gemini-3.8-flash-medium"\|"gemini-4-argon-medium"` |

#### Category (d): Hard-coded runtime defaults bypassing the registry

None (0 hits).

### 2. Mechanisms Forbidding or Allowing Model Literals Outside `user/agent-models.json`

1. **Shared rules and skill contract**: `AGENTS.md:175` (generated into `CLAUDE.md:193`) makes `user/agent-models.json` the sole registry ("Name no model or effort level anywhere else."). `skills/agent-models/SKILL.md:10, 20-21, 117, 121` enforces the same rule, documents `agent-models: allow`, and permits finished-run data records and model-subject experiments.
2. **Scanner (`scripts/agent_models.py`)**: `ALLOW_MARKER = "agent-models: allow"` (`:91`); `LITERAL_PATTERNS` (`:830-850`, with `:835` matching `r"\bgemini-\d+(?:\.\d+)*-[a-z][\w.\-]*"` and excluding quota bucket IDs like `gemini-5h` at `:833-834`); `scan_text` (`:855-861`) skips any line carrying `agent-models: allow` (used at `docs/mac-storage-audit.md:108`); `scan` and `doctor --scan` (`:878-894, 1556-1561`) exit `1` on any unexempted hit. Note that the regex catches versioned hyphenated slugs (`gemini-4-argon`, `gemini-3.8-flash-high`), not prose display names (`Gemini 3.8 Flash`) or placeholders (`gemini-<version>-flash-high`).
3. **Automated test gates (run in CI via `.github/workflows/validate.yml:75-76`)**:
   - `tests/test_agent_models.py:1591-1607, 1624-1629, 1843-1862` (`DriftGuardTests.test_no_model_or_effort_literal_outside_the_allowlist`) runs `agent_models.scan()` across all tracked and non-ignored worktree files and fails on any hit outside `DRIFT_ALLOW_PREFIXES` (`archive/`, `legacy/`, `docs/followups/`, `tests/`), `DRIFT_ALLOW_FILES` (`user/agent-models.json`, `user/settings.json`, `CHANGELOG.md`, `scripts/agent_models.py`, `docs/mac-mouse-preferences.md`), and `DRIFT_ALLOW_SUFFIXES` (image suffixes).
   - `tests/test_dispatch_gemini.py:261-265` (`test_no_model_or_effort_literal_in_the_dispatcher`) runs `agent_models.scan_text()` directly on `skills/implement-review/scripts/dispatch-gemini.py` (with parallel tests for Claude and Codex dispatchers; `dispatch-task-agy.py` is covered by `DriftGuardTests`).
4. **Hooks and parity**: `scripts/guard.py` does not check model literals, and `.githooks/pre-push` runs `scripts/pre-push-smoke.sh` rather than `agent_models.py scan`. `scripts/check-parity.sh:175-176` enforces STRICT byte-identical parity of `scripts/agent_models.py` and `user/agent-models.json` between `agent-config` and `anywhere-agents`.

### 3. Impact of Replacing `families.agy.model` and `roles.reviewer.agy.fallback_model`

- **Would any test or script break?** No local test or script breaks, provided the replacement is a valid tierless Agy stem matching `[A-Za-z0-9._:/-]+` without a trailing tier (`-low`, `-medium`, `-high`, `-xhigh`, `-max`, `-thinking`) per `scripts/agent_models.py:179, 194-199`. Unit and integration tests isolate themselves with temporary `AGENT_MODELS_FILE` registries; tests that read the live registry (`tests/test_agent_models.py:465-491`, `tests/test_dispatch_gemini.py:233-238`, `tests/test_repo.py:426-440`) assert dynamically against `agent_models.resolve(...)` or `render --check`. `user/settings.json` only mirrors Claude keys (`scripts/agent_models.py:558-575`), so `render --check` stays green. Runtime resolution updates cleanly: `agy/interactive` and `agy/premium` resolve to `<new-stem>-high` (fallback `gemini-4-hydrogen-high`), `agy/reviewer` (`dispatch-gemini.py`) keeps primary `gemini-4-carbon-medium` with `fallback_slugs = ["<new-stem>-high", "gemini-4-hydrogen-high"]`, and `agy/worker` / `agy/prun-worker` (`dispatch-task-agy.py`) stay on `gemini-4-hydrogen` (`fallback_model: null`). Cross-repo parity (`scripts/check-parity.sh:176`) will fail until `user/agent-models.json` is mirrored to `anywhere-agents`.
- **What else would change on a machine that runs bootstrap?**
  1. Consumer repo copy `.agent-config/repo/user/agent-models.json` updates to the new registry.
  2. Unless `AGENT_MODELS_SYNC` is disabled (`off|0|false|no|disabled`) or `~/.gemini/antigravity-cli` does not exist, `bootstrap/bootstrap.sh:1244-1253` and `bootstrap/bootstrap.ps1:1571-1586` run `agent_models.py sync --quiet`. `sync_agy` (`scripts/agent_models.py:712-755`) detects that `"model"` in `~/.gemini/antigravity-cli/settings.json` no longer matches `agy_family_state == "primary"`, calls `agy models`, picks the newest listed slug in the new primary family at tier `high` (falling back to `gemini-4-hydrogen-high` if the account lacks the new family, or skipping without failing bootstrap if neither is listed), backs up the previous file to `~/.gemini/antigravity-cli/settings.json.agent-models.bak`, atomically writes the new display name to `"model"`, and records the update in the bootstrap ledger (`bootstrap.sh:1250-1251`, `bootstrap.ps1:1584-1585`).
  3. SessionStart banner (`scripts/render_banner.py:575, 705-712` via `scripts/session_bootstrap.py:156-177, 478`) and `agent_models.py doctor`/`verify` expect the new primary family (reporting drift if `~/.gemini/antigravity-cli/settings.json` was not synced).
  4. `~/.claude/settings.json`, `~/.codex/config.toml`, `~/.grok/`, `prun` worker default (`gemini-4-hydrogen-high`), and `/vet` Agy reviewer primary (`gemini-4-carbon-medium`) remain unchanged.

---

## Task 2

Conclusion: Gemini 4 Neon (`gemini-4-neon`) launched on November 18, 2026 across the Gemini API, Google Cloud Gemini Enterprise Agent Platform, the Gemini app, and Google Antigravity (desktop app, `agy` CLI, and IDE extensions). In Antigravity, it is included on Google AI Ultra, paid Google AI Pro, eligible premium-device Pro trials, and Gemini Enterprise (excluded from Free, Google AI Plus, and standard Pro trials), supports up to a 512K-token context window in Antigravity (1,048,576 unified tokens in the Gemini API), offers four thinking levels (`low`, `medium`, `high` default, `xhigh`), and pairs with Gemini 4 Hydrogen in `Orchestrator (Neon)` (Pro and Ultra only, not Enterprise). Standard Gemini API pricing is flat across the full 1M context window at $3.00 input, $0.15 implicit cached input, and $15.00 output per 1M tokens (Paid tier only). No first-party Google statement declares Gemini 4 Argon retired, deprecated, or replaced; official docs list `gemini-4-argon` as active GA with no shutdown date announced (and Cloud retirement on October 13, 2027 or later).
Files: None modified (read-only public web research).
Open items: (1) Full `agy` CLI slug list for Neon: public first-party Antigravity documentation explicitly prints `gemini-4-neon`, `gemini-4-neon-xhigh`, and `"Orchestrator (Neon)"`, and instructs users to run `agy models` for the complete account-specific list; standalone suffixed slugs `gemini-4-neon-low`, `gemini-4-neon-medium`, and `gemini-4-neon-high` are not enumerated verbatim on public pages. (2) Consumer Gemini app picker status for Argon: third-party press (9to5Google) reports that Neon replaces Argon in the consumer Gemini app picker, but no first-party Google help page or release note on `support.google.com` or `gemini.google/release-notes/` was found confirming removal of Argon from the consumer app.
Verification: Verified all cited public URLs via read-only HTTP `HEAD` (`curl -sI`), redirect-following `HEAD` (`curl -sIL`), and `GET` reads via Python `urllib.request`. Every cited URL returned HTTP 200 on both initial and final `HEAD` (no redirects, no 4xx/5xx errors, no CAPTCHA or anti-bot blocks). For Google AI Studio docs, both the client-side rendered HTML URLs (`https://aistudio.google.com/docs/...`, HTTP 200) and Google's official Markdown endpoints (`https://aistudio.google.com/docs/...md`, HTTP 200, `text/markdown; charset=utf-8`) were verified.

### Sourced Findings (Items 1–7)

#### 1. Release Date
- **November 18, 2026** (general availability for `gemini-4-neon` in the Gemini API and Google Cloud Gemini Enterprise Agent Platform; rollout beginning the same day in Google Antigravity desktop app, Antigravity CLI, and IDE extensions):
  - Google Blog ("Introducing Gemini 4 Neon", `Nov 18, 2026`): `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` (HTTP 200)
  - Antigravity Blog ("Gemini 4 Neon in Google Antigravity", `Nov 18, 2026`): `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity` (HTTP 200)
  - Antigravity Changelog (`Model launch · November 18, 2026`, under both Antigravity App and Antigravity CLI): `https://antigravity.google/docs/changelog/` (HTTP 200)
  - Google AI Developers Forum official announcement (`November 18, 2026`): `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200)
  - Gemini API Release Notes (`November 18, 2026`, "`gemini-4-neon` generally available (GA)"): `https://aistudio.google.com/docs/changelog.md` (HTTP 200; HTML: `https://aistudio.google.com/docs/changelog`, HTTP 200)
  - Google Cloud Gemini 4 Neon model page (`Launch stage: GA`, `Release date: November 18, 2026`): `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon` (HTTP 200)
  - Google DeepMind Model Card (`Published 18 November 2026`): `https://deepmind.google/models/model-cards/gemini-4-neon/` (HTTP 200)

#### 2. Which Google AI Plans Get It in Antigravity and Which Do Not
Sources: `https://antigravity.google/docs/models/` (HTTP 200), `https://antigravity.google/docs/enterprise/` (HTTP 200), `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200), `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity` (HTTP 200), and `https://antigravity.google/docs/plans/` (HTTP 200).

| Plan / Tier | Gemini 4 Neon | Orchestrator (Neon) |
|---|---|---|
| Free | Not included | Not included |
| Google AI Plus | Not included | Not included |
| Google AI Pro (standard trial) | Not included | Not included |
| Google AI Pro (trial with eligible premium devices) | Included (`†`) | Included (`†`) |
| Google AI Pro (paid) | Included (`†`) | Included (`†`) |
| Google AI Ultra | Included | Included |
| Enterprise (Gemini Enterprise / Gemini for business) | Included | Not included |

- Footnote `†` verbatim (`https://antigravity.google/docs/models/`, HTTP 200): `"Available with paid Google AI Pro plans or on trial with eligible premium devices."`
- Default selection (`https://antigravity.google/docs/models/`, HTTP 200): Gemini 4 Neon appears at the top of the model selector on every plan that includes it and becomes the default for new conversations if the user has not chosen a model (existing user selections are preserved).
- Workspace note (`https://antigravity.google/docs/plans/`, HTTP 200): Personal plans apply to personal Google Accounts; Google Workspace plans do not include Antigravity plans or higher rate limits (teams use Gemini Enterprise under Google Cloud terms).

#### 3. CLI Model Slugs, Thinking Levels, and Default Level
- **Thinking levels**: Four levels: UI labels `Low`, `Medium`, `High`, and `Extra`; `agy` CLI effort values `low`, `medium`, `high`, and `xhigh` (`Extra High` reasoning budget). Sources: `https://antigravity.google/docs/models/` (HTTP 200), `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200), `https://antigravity.google/docs/cli/commands/effort/` (HTTP 200). In the Gemini API, `thinking_level` accepts `LOW`, `MEDIUM`, `HIGH`, and `XHIGH`; `MINIMAL` and `thinking_budget` return HTTP 400 (`https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon`, HTTP 200; `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md`, HTTP 200).
- **Default thinking level**: `High` (`high` in CLI and API). Sources: `https://antigravity.google/docs/models/` (HTTP 200), `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md` (HTTP 200), `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon` (HTTP 200).
- **CLI model identifiers / slugs explicitly documented on public first-party pages**:
  - `gemini-4-neon`: listed under `CLI / API Identifier` for Gemini 4 Neon on `https://antigravity.google/docs/enterprise/` (HTTP 200), combined with `--effort <level>` or `/effort <level>` (`agy` v1.2.11+).
  - `gemini-4-neon-xhigh`: documented verbatim as `--model gemini-4-neon-xhigh` (or `--effort xhigh`) on `https://antigravity.google/docs/models/` (HTTP 200) and `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200).
  - `"Orchestrator (Neon)"`: documented verbatim as `agy --model "Orchestrator (Neon)"` (fixed configuration; `--effort` and `/effort` do not apply) on `https://antigravity.google/docs/models/` (HTTP 200).
  - Account-specific slug discovery: `https://antigravity.google/docs/models/` (HTTP 200), `https://antigravity.google/docs/cli/reference/` (HTTP 200), and `https://antigravity.google/docs/cli/headless/` (HTTP 200) direct users to run `agy models` to list every model identifier available on their account.

#### 4. Context Window (Antigravity vs. Gemini API)
- **In Google Antigravity**: Up to **512K tokens**. Sources: `https://antigravity.google/docs/models/` (HTTP 200: `"Context window: Up to 512K tokens."`), `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200: `"Context window of up to 512K tokens in Antigravity."`).
- **In the Gemini API (Google AI Studio and Google Cloud Gemini Enterprise Agent Platform)**: **1,048,576 tokens (1M tokens)** unified context window shared across input, thinking, function calls, and output tokens. Default synchronous max output is **65,536 tokens (64K)**; long decode output supports up to **1,048,576 tokens minus input tokens** (via `background=true` on Interactions API or `continuation_token` on `GenerateContent` `v1beta1` / Interactions API). Sources: `https://aistudio.google.com/docs/models/gemini-4-neon.md` (HTTP 200; HTML: `https://aistudio.google.com/docs/models/gemini-4-neon`, HTTP 200), `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md` (HTTP 200; HTML: `https://aistudio.google.com/docs/whats-new-gemini-4-neon`, HTTP 200), `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon` (HTTP 200), `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/` (HTTP 200).

#### 5. API Price per Million Tokens
- **Prompt-length tier thresholds**: None. Pricing is flat across the full 1M context window (`"It uses flat pricing across the full 1M context window"`, `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md`, HTTP 200). Paid tier only (not available on the Free API tier). All processed tokens, including thinking tokens and internal grounding declarations, are billed.
- **Caching**: Implicit caching only (4,096-token minimum, 95% discount on cache reads); explicit context caching is not supported (`https://aistudio.google.com/docs/pricing.md`, HTTP 200; `https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-neon`, HTTP 200). On Google Cloud, cache write pricing (`1.25x` input price) takes effect January 12, 2027 (`https://cloud.google.com/model-garden/pricing`, HTTP 200).
- **Gemini Developer API (Google AI Studio)** (`https://aistudio.google.com/docs/pricing.md`, HTTP 200; HTML: `https://aistudio.google.com/docs/pricing`, HTTP 200; `https://blog.google/innovation-and-ai/models-and-research/gemini-models/introducing-gemini-4-neon/`, HTTP 200):
  - **Standard (Paid)**: $3.00 input | $0.15 cached input | $15.00 output (including thinking) per 1M tokens.
  - **Batch (Paid)**: $1.50 input | $0.075 cached input | $7.50 output per 1M tokens.
  - **Flex (Paid)**: $1.50 input | $0.075 cached input | $7.50 output per 1M tokens.
  - **Priority (Paid)**: $5.40 input | $0.27 cached input | $27.00 output per 1M tokens.
- **Google Cloud (Gemini Enterprise Agent Platform / Model Garden)** (`https://cloud.google.com/model-garden/pricing`, HTTP 200):
  - **Standard PayGo**: Global $3.00 input / $0.15 cache read / $3.75 cache write (effective Jan 12, 2027) / $15.00 output; Non-global (`us`/`eu`, +10%) $3.30 input / $0.165 cache read / $4.125 cache write (effective Jan 12, 2027) / $16.50 output.
  - **Priority PayGo**: Global $5.40 input / $0.27 cache read / $6.75 cache write (effective Jan 12, 2027) / $27.00 output; Non-global $5.94 input / $0.297 cache read / $7.425 cache write (effective Jan 12, 2027) / $29.70 output.
  - **Batch**: Global $1.50 input / $0.075 cache read / $1.875 cache write (effective Jan 12, 2027) / $7.50 output; Non-global $1.65 input / $0.0825 cache read / $2.0625 cache write (effective Jan 12, 2027) / $8.25 output.

#### 6. What "Orchestrator (Neon)" Is
Sources: `https://antigravity.google/docs/models/` (HTTP 200), `https://antigravity.google/blog/gemini-4-neon-in-google-antigravity` (HTTP 200), `https://discuss.ai.google.dev/t/gemini-4-neon-and-orchestrator-neon-are-now-available-in-google-antigravity/202301` (HTTP 200), `https://antigravity.google/docs/enterprise/` (HTTP 200).

- A model-selector option in Google Antigravity (alongside `Orchestrator (Carbon)` and `Orchestrator (Argon)`) that pairs **Gemini 4 Neon** as planner and reviewer with **Gemini 4 Hydrogen** as the fast implementation model inside a single conversation and single agent loop.
- Rather than routing a prompt once up front to a single model, both models collaborate within the same task and hand control back and forth automatically inside one response: (1) Neon runs a read-only planning phase to explore the codebase, resolve ambiguities, and draft a plan with re-planning triggers (or answers directly if no code edits are needed); (2) Hydrogen executes file edits, writes code, updates packages, and runs builds and tests; (3) if Hydrogen hits friction (such as a verification step failing twice, an unexpected interface, or an unsettled design choice), control returns to Neon to inspect conversation state, repair the plan, and hand execution back; (4) on longer tasks or mid-task user messages, Hydrogen reports back to Neon to verify progress, wrap up, continue, or revise the plan.
- Configuration is fixed (`--effort` and `/effort` do not apply). Available on Google AI Ultra and paid Google AI Pro (plus eligible premium-device Pro trials); not available on Free, Google AI Plus, or Enterprise.

#### 7. Gemini 4 Argon Retirement, Deprecation, or Replacement Status
- **First-party Google statements**: **No first-party Google statement exists stating that Gemini 4 Argon is retired, deprecated, or replaced.** Official first-party Google documentation lists `gemini-4-argon` as active GA with no deprecation, shutdown, or replacement announced:
  - Gemini API Deprecations (`https://aistudio.google.com/docs/deprecations.md`, HTTP 200; HTML: `https://aistudio.google.com/docs/deprecations`, HTTP 200) under `## Gemini 4 models`: Model `` `gemini-4-argon` `` | Release date: `October 13, 2026` | Shutdown date: `"No shutdown date announced"` | Recommended replacement: blank.
  - Google Cloud Model Versions and Lifecycle (`https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/model-versions`, HTTP 200) under `"Models available for at least 12 months after release"`: Model ID `gemini-4-argon` | Release date: `October 13, 2026` | Retirement date: `"October 13, 2027 or later"` | Replacement model ID: blank.
  - Google Cloud Gemini 4 Argon model page (`https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/gemini/4-argon`, HTTP 200): verbatim `"Launch stage: GA"`, `"Release date: October 13, 2026"`, `"Retirement date † : October 13, 2027 or later"`.
  - Google Antigravity Docs (`https://antigravity.google/docs/models/`, HTTP 200; `https://antigravity.google/docs/enterprise/`, HTTP 200): `Gemini 4 Argon` (`gemini-4-argon`) and `Orchestrator (Argon)` remain listed as active available models alongside Gemini 4 Neon.
  - Google AI Studio Models catalog (`https://aistudio.google.com/docs/models.md`, HTTP 200; `https://aistudio.google.com/docs/models/gemini-4-argon.md`, HTTP 200): lists `gemini-4-argon` as `Stable`. (`https://aistudio.google.com/docs/choosing-a-model.md`, HTTP 200, and `https://aistudio.google.com/docs/latest-model.md`, HTTP 200, feature Carbon, Neon, and Hydrogen without listing Argon, and `https://aistudio.google.com/docs/whats-new-gemini-4-neon.md`, HTTP 200, includes an optional `"Migrate from Gemini 4 Carbon, Argon, or Hydrogen"` section; none declare Argon deprecated, retired, or replaced.)
  - Google Cloud Model Garden Pricing (`https://cloud.google.com/model-garden/pricing`, HTTP 200): continues to publish active `Gemini 4 Argon` pricing through November 30, 2026 and starting December 1, 2026 ($4.00 input / $20.00 output Global).
- **Third-party claims (separate from first-party statements)**:
  - 9to5Google (`https://9to5google.com/2026/11/18/gemini-4-neon-announcement/`, HTTP 200) reports regarding the consumer Gemini app picker: `"As such, Neon is available in the Gemini app for AI Pro (and AI Ultra) subscribers, with 3.1 Pro finally going away. Neon also replaces Argon."` This is a third-party press report about the consumer Gemini app UI, not a first-party Google retirement, deprecation, or replacement notice.

---

## Task 3

Conclusion: Implemented preamble trimming in `skills/prun/scripts/dispatch-task-agy.py` and added matching unit and integration tests in `tests/test_dispatch_task_agy.py`. When the worker writes no result file itself and exits cleanly, if the stripped final response contains an exact `# <unit-id> result` line after other text, the dispatcher publishes from that first matching line onward to `result_path` and stores the full response beside it via `response_path_for(result_path)` (`<stem>.response<suffix>`). When the header is absent or already on the first line (including after leading blank lines), the dispatcher publishes unchanged and writes no extra file. Worker-written results and FALLBACK paths are unchanged. Independently verified by the `verifier` worker; all 101 tests (42 subtests) pass, and no commits or pushes were made.
Files: `skills/prun/scripts/dispatch-task-agy.py` (+37/-2), `tests/test_dispatch_task_agy.py` (+114/-0).
Open items: None.
Verification: Verified by `verifier` and coordinator: `git status --short` shows only `M skills/prun/scripts/dispatch-task-agy.py` and `M tests/test_dispatch_task_agy.py` (no untracked files); `git log -n 1 --oneline` confirms `HEAD` remains `53f9c17`; `/Users/yzhao062/miniforge3/envs/py312/bin/python -m pytest -q tests/test_dispatch_task_agy.py` exited 0 with `101 passed, 42 subtests passed in 18.59s` (`verifier`) and `101 passed, 42 subtests passed in 19.01s` (`agy-coder`).

### `git diff --stat`

```text
 skills/prun/scripts/dispatch-task-agy.py |  39 ++++++++++-
 tests/test_dispatch_task_agy.py          | 114 +++++++++++++++++++++++++++++++
 2 files changed, 151 insertions(+), 2 deletions(-)
```

### Pytest Output

```text
.....................................................................................................  [100%]
101 passed, 42 subtests passed in 18.59s
```

### Key Hunks (`skills/prun/scripts/dispatch-task-agy.py`)

```diff
@@ -1007,12 +1007,31 @@ def atomic_publish(path: Path, text: str, nonce: str) -> None:
 
 
 def response_path_for(result_path: Path) -> Path:
-    """Sibling path for the final response when the worker wrote the result itself."""
+    """Sibling path for the full final response beside the published result."""
     return result_path.with_name(
         f"{result_path.stem}.response{result_path.suffix}"
     )
 
 
+def trim_response_preamble(response: str, unit_id: str) -> tuple[str, bool]:
+    """Strip leading narration before an exact ``# <unit_id> result`` line.
+
+    Returns ``(text, trimmed)`` after stripping surrounding whitespace. When
+    the exact header line appears after other text, returns the response from
+    the first matching line onward and ``True``. When the header is absent or
+    already on the first line, returns the cleaned response and ``False``.
+    """
+    cleaned = response.strip()
+    header = f"# {unit_id} result"
+    lines = cleaned.splitlines(keepends=True)
+    for index, line in enumerate(lines):
+        if line.rstrip("\r\n") == header:
+            if index == 0:
+                return cleaned, False
+            return "".join(lines[index:]), True
+    return cleaned, False
+
+
 def publish_fallback(
     result_path: Path,
     unit_id: str,
@@ -1520,11 +1539,27 @@ def main(argv: list[str] | None = None) -> int:
             exit_code = 70
             reason = "Agy returned an implausibly short final response"
         else:
+            full_response = response.strip()
+            body, trimmed = trim_response_preamble(full_response, args.unit_id)
             try:
-                atomic_publish(result_path, response.strip() + "\n", nonce)
+                atomic_publish(result_path, body + "\n", nonce)
             except OSError as exc:
                 exit_code = 70
                 reason = f"could not publish result atomically: {exc}"
+            else:
+                if trimmed:
+                    try:
+                        atomic_publish(
+                            response_path_for(result_path),
+                            full_response + "\n",
+                            nonce,
+                        )
+                    except OSError as exc:
+                        print(
+                            f"dispatch-task-agy: published trimmed result; could not store "
+                            f"full response beside it: {exc}",
+                            file=sys.stderr,
+                        )
 
     if exit_code != 0:
         publish_fallback(
```

### Tests Added (`tests/test_dispatch_task_agy.py`)

- `DispatchTaskAgyUnitTests`:
  - `test_trim_response_preamble_strips_narration_before_exact_header`: covers LF, CRLF, and repeated header lines.
  - `test_trim_response_preamble_leaves_header_first_and_no_header_alone`: covers header-first, header-only, leading whitespace prefix, header-first with later repeat, no-header, and near-misses (prefix with extra text, trailing spaces, indented header, wrong unit ID).
- `DispatchTaskAgyIntegrationTests`:
  - `test_narration_before_header_publishes_from_header_and_keeps_full_response`: verifies `.md` and `.txt` results publish from `# <unit-id> result` onward and write full response to `<stem>.response<suffix>`.
  - `test_header_first_response_publishes_unchanged_without_extra_file`: verifies header-first responses (with and without leading blank lines) publish unchanged with no `.response.` sibling.
  - `test_response_without_header_publishes_unchanged_without_extra_file`: verifies responses with no header or near-miss prefix publish unchanged with no `.response.` sibling.
  - `test_error_status_with_narration_and_header_still_publishes_fallback`: confirms ERROR status responses carrying narration plus header still publish FALLBACK with no `.response.` sibling.
