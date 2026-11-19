# u1-hydrogen result
Conclusion: Replacing the two `gemini-4-argon` fields (`families.agy.model` and `roles.reviewer.agy.fallback_model`) in `user/agent-models.json` with another valid tierless Gemini stem would not break any test or script, and on a machine running bootstrap it would update `~/.gemini/antigravity-cli/settings.json` (backing it up to `settings.json.agent-models.bak`), shift the interactive/premium Agy target and `/vet` Agy reviewer's primary fallback in banner/doctor/verify/dispatcher checks, and leave `prun-worker`, `worker`, Claude, and Codex configs unchanged.
Files: none
Open items: none
Verification: `git rev-parse --short HEAD` (53f9c17); `grep -rn -i -E "(argon|carbon|hydrogen|neon|flash|gemini-)" --exclude-dir=.git .` (exit 0); `grep -rn -i -E "(carbon|hydrogen|neon)" --exclude-dir=.git .` (0 non-binary hits outside `user/agent-models.json`); Python AST/regex tree scan (exit 0, 214 summary lines); `python3 scripts/agent_models.py show` (exit 0); `python3 scripts/agent_models.py scan .` (exit 1 on allowlisted docs/tests/registry); `python3 -m pytest tests/test_agent_models.py tests/test_dispatch_grok.py tests/test_dispatch_task_grok.py tests/test_render_banner.py -q` (241 passed, 1 skipped, 67 subtests passed); `env -u ANTIGRAVITY_DISPATCH_MODEL -u ANTIGRAVITY_DISPATCH_EFFORT python3 -m pytest tests/test_dispatch_gemini.py tests/test_dispatch_task_agy.py -q` (180 passed, 54 subtests passed); `python3 -m pytest tests/test_repo.py -q` (29 passed, 1 skipped); `git status --short` (clean).

## 1. Hits outside `user/agent-models.json`

There are zero occurrences of `carbon`, `hydrogen`, or `neon` outside `user/agent-models.json`, and zero category **(d)** hard-coded runtime defaults anywhere in the repository.

### (a) Code that reads the registry (docstring examples only)

- `scripts/agent_models.py:18,309` (`gemini-4-argon`, `'Gemini 4 Argon (High)' -> 'gemini-4-argon-high'`) — docstring examples inside the resolver itself (`line 833` is `gemini-5h`, a quota bucket ID rather than a model slug).
- `skills/prun/scripts/dispatch-task-agy.py:642,645` (`gemini-<version>-flash-high`, `Gemini Flash`, `Flash`) — docstring examples for `newest_in_family()` in a module whose defaults come from `user/agent-models.json` via `load_registry_defaults()` (`line 144` is `GEMINI_POOL_PREFIX = "gemini-"`).

*(Note: `skills/implement-review/scripts/dispatch-gemini.py:399,813,979` use `implement-review-gemini-*` temp/lock prefixes, and `skills/implement-review/scripts/style-audit.py:486` matched `jargon` as a substring.)*

### (b) Test fixtures

- `tests/test_agent_models.py`:
  - `argon`/`flash` fixtures and unit samples (20 lines): `796, 797, 800, 801, 802, 803, 804, 806, 811, 812, 814, 815, 816, 820, 825, 826, 914, 915, 916, 918` (`Gemini 4 Argon (High)`, `Gemini 3.8 Flash ...`, `gemini-4-argon*`, `gemini-4-flash-high`, `gemini-4.1-argon-high`, `gemini-4.2-argon-low`, `gemini-5-argon-high`, `gemini-3.8-flash-*`).
  - Synthetic `gemini-*` fixtures (`gemini-9-test*`, `gemini-8-fast*`, `gemini-9-peak*`, `gemini-9-other*`, `gemini-10-test-high`) (67 lines): `50, 52, 61, 153, 154, 155, 160, 167, 169, 174, 175, 177, 184, 192, 196, 197, 202, 207, 212, 220, 272, 367, 431, 441, 620, 621, 626, 627, 630, 635, 822, 853, 854, 855, 856, 857, 858, 948, 952, 955, 1296, 1419, 1420, 1421, 1424, 1427, 1429, 1435, 1438, 1465, 1681, 1684, 1694, 1695, 1697, 1698, 1700, 1701, 1703, 1795, 1797, 1798, 1813, 1814, 1815, 1819, 1821`.
- `tests/test_dispatch_gemini.py`:
  - `argon`/`flash` fixtures and mock CLI defaults (91 lines): `31, 32, 99, 187, 625, 651, 652, 654, 658, 659, 661, 668, 670, 675, 679, 680, 682, 688, 689, 691, 720, 721, 725, 727, 731, 734, 741, 742, 744, 748, 749, 751, 755, 756, 758, 764, 767, 1090, 1135, 1144, 1157, 1185, 1363, 1364, 1365, 1366, 1371, 1372, 1374, 1375, 1379, 1380, 1381, 1384, 1385, 1388, 1389, 1396, 1397, 1407, 1408, 1414, 1421, 1428, 1429, 1430, 1435, 1441, 1442, 1446, 1449, 1457, 1462, 1463, 1534, 1538, 1544, 1631, 1634, 1638, 1639, 1641, 1683, 1685, 1690, 1691, 1695, 1700, 1701, 1716, 1719`.
  - Other `gemini-*` fixtures (`gemini-3.1-pro-high`, `gemini-3.8-pro-high`) (13 lines): `671, 672, 1114, 1115, 1120, 1123, 1431, 1559, 1561, 1566, 1567, 1584, 1586`.
- `tests/test_dispatch_task_agy.py`:
  - `argon`/`flash` fixtures and mock CLI defaults (107 lines): `28, 46, 104, 168, 219, 276, 288, 289, 291, 296, 297, 299, 304, 305, 307, 312, 313, 315, 319, 320, 322, 343, 344, 353, 354, 395, 397, 398, 406, 407, 409, 413, 414, 416, 421, 422, 424, 428, 429, 431, 938, 1161, 1166, 1175, 1186, 1201, 1223, 1246, 1320, 1490, 1491, 1492, 1499, 1500, 1505, 1508, 1513, 1514, 1515, 1517, 1560, 1561, 1562, 1569, 1570, 1573, 1580, 1586, 1597, 1614, 1615, 1624, 1658, 1692, 1693, 1700, 1705, 1711, 1719, 1727, 1732, 1733, 1738, 1745, 1746, 1751, 1752, 1757, 1825, 1830, 1841, 1861, 1869, 1874, 1902, 1921, 1922, 1928, 1933, 1934, 1937, 1940, 1949, 1960, 1964, 1981, 2001`.
  - Other `gemini-*` fixtures (`gemini-9.9-spark*`, `gemini-3.1-pro-high`) (10 lines): `228, 233, 1345, 1772, 1778, 1783, 1787, 1809, 1811, 1816`.
- `tests/test_dispatch_grok.py:354,805` (`gemini-4-argon` in temp registry fixture).
- `tests/test_dispatch_task_grok.py:34,38` (`gemini-4-argon` and `gemini-3.8-flash` in temp registry fixture).
- `docs/followups/2026-09-18-skills-bloat-audit/fixture/tail:1` (`gemini-3.8-flash-high` in archived audit fixture; lines 3-16 are `implement-review-gemini-0000-round1-1-abc` paths).

*(Note: `tests/_quiet_spawn.py:1,33`, `tests/test_bootstrap_preflight.py:310,787` match English "flash/flashed/flashing", and `tests/test_agent_quota_refresh.py:34`, `tests/test_codex_usage.py:754,760` are `gemini-5h`/`gemini-weekly` quota bucket IDs.)*

### (c) Documentation and historical records

- `ONBOARDING.md:172` (`gemini Flash free tier`).
- `docs/mac-mouse-preferences.md:118` (`Gemini 3.8 Flash (High)` recorded machine snapshot).
- `docs/mac-storage-audit.md:108` (`gemini-3.8-flash-high` audit record, tagged `<!-- agent-models: allow -->`).
- `docs/followups/README.md:17` (`Gemini Flash, Gemini Argon`).
- `docs/followups/2026-08-22-grok-fourth-reviewer-evaluation.md:183,541` (`Gemini 2.5 Pro`, `Gemini 2.5 Flash` paper summary).
- `docs/followups/2026-09-18-skills-bloat-audit.md:3` (`Gemini 3.8 Flash`).
- `docs/followups/2026-10-18-harness-slimming-audit.md:9` (`Gemini 3.8 Flash High`).
- `docs/followups/2026-10-25-eu-guidance-pilot.md:26,32,34,40,42,56,60,70,72,78,84` (`Gemini 3.8 Flash Medium`, `Gemini 4 Argon Medium`, `Flash`, `Argon`).
- `docs/followups/2026-10-25-eu-guidance-pilot/scripts/tasks.py:189,282` (`"flash": "gemini-3.8-flash-medium"`, `"argon": "gemini-4-argon-medium"` in historical experiment harness).
- `docs/followups/2026-10-25-eu-guidance-pilot/round1/scores.json` (96 lines: `argon`/`flash` and `gemini-4-argon-medium`/`gemini-3.8-flash-medium` on lines `8, 9, 24, 25, 42, 43, 66, 67, 82, 83, 98, 99, 114, 115, 148, 149, 172, 173, 205, 206, 229, 230, 262, 263, 286, 287, 302, 303, 320, 321, 344, 345, 360, 361, 376, 377, 409, 410, 442, 443, 475, 476, 495, 496, 511, 512, 535, 536, 568, 569, 584, 585, 600, 601, 624, 625, 640, 641, 656, 657, 680, 681, 713, 714, 731, 732, 747, 748, 765, 766, 785, 786, 809, 810, 833, 834, 857, 858, 873, 874, 906, 907, 930, 931, 963, 964, 981, 982, 997, 998, 1015, 1016, 1031, 1032, 1064, 1065`).
- `docs/followups/2026-10-25-eu-guidance-pilot/round2/scores.json` (264 lines: `argon`/`flash` and `gemini-4-argon-medium`/`gemini-3.8-flash-medium` on lines `40, 41, 64, 65, 120, 121, 191, 192, 214, 215, 230, 231, 285, 286, 321, 322, 356, 357, 372, 373, 396, 397, 412, 413, 506, 507, 522, 523, 538, 539, 560, 561, 642, 643, 755, 756, 771, 772, 794, 795, 833, 834, 849, 850, 867, 868, 940, 941, 956, 957, 988, 989, 1004, 1005, 1026, 1027, 1048, 1049, 1084, 1085, 1119, 1120, 1135, 1136, 1240, 1241, 1295, 1296, 1311, 1312, 1329, 1330, 1345, 1346, 1380, 1381, 1396, 1397, 1453, 1454, 1492, 1493, 1514, 1515, 1530, 1531, 1581, 1582, 1603, 1604, 1619, 1620, 1643, 1644, 1659, 1660, 1699, 1700, 1763, 1764, 1808, 1809, 1824, 1825, 1840, 1841, 1864, 1865, 1880, 1881, 1896, 1897, 1918, 1919, 1941, 1942, 1964, 1965, 1999, 2000, 2050, 2051, 2090, 2091, 2112, 2113, 2128, 2129, 2152, 2153, 2200, 2201, 2255, 2256, 2277, 2278, 2293, 2294, 2309, 2310, 2332, 2333, 2367, 2368, 2391, 2392, 2430, 2431, 2446, 2447, 2462, 2463, 2494, 2495, 2518, 2519, 2534, 2535, 2557, 2558, 2581, 2582, 2604, 2605, 2620, 2621, 2643, 2644, 2659, 2660, 2675, 2676, 2697, 2698, 2729, 2730, 2768, 2769, 2791, 2792, 2815, 2816, 2833, 2834, 2849, 2850, 2883, 2884, 2906, 2907, 2922, 2923, 3016, 3017, 3071, 3072, 3110, 3111, 3133, 3134, 3156, 3157, 3172, 3173, 3207, 3208, 3229, 3230, 3269, 3270, 3301, 3302, 3333, 3334, 3372, 3373, 3388, 3389, 3404, 3405, 3420, 3421, 3436, 3437, 3459, 3460, 3494, 3495, 3540, 3541, 3563, 3564, 3581, 3582, 3621, 3622, 3644, 3645, 3691, 3692, 3707, 3708, 3746, 3747, 3769, 3770, 3804, 3805, 3820, 3821, 3836, 3837, 3875, 3876, 3915, 3916, 3931, 3932, 3947, 3948, 3979, 3980, 4018, 4019`).

*(Note: `docs/dgx-spark-setup.md:88` `reflashes` and `docs/followups/2026-09-17-agents-md-diet.md:124` `flashing` are unrelated English words.)*

## 2. Mechanisms forbidding or allowing model literals outside the registry

- **Forbidden by policy and automated drift guard**:
  - `AGENTS.md` (Environment section) and `skills/agent-models/SKILL.md:10,21` forbid naming concrete models or efforts outside `user/agent-models.json`.
  - `scripts/agent_models.py:830-894` (`scan_text`, `scan`, `cmd_scan`, `doctor --scan`) scans source/doc files against `LITERAL_PATTERNS`, including `r"\bgemini-\d+(?:\.\d+)*-[a-z][\w.\-]*"` (`line 835`). Notice that bare prose words without `gemini-<version>-` (like `Gemini Flash` or `Argon` in `ONBOARDING.md:172` and `dispatch-task-agy.py:642,645`) are not matched by `LITERAL_PATTERNS`.
  - `tests/test_agent_models.py:1843-1862` (`DriftGuardTests.test_no_model_or_effort_literal_outside_the_allowlist`) enforces `agent_models.scan(...) == []` across all tracked and untracked non-ignored files outside the allowlist.
  - Per-dispatcher drift tests also run `agent_models.scan_text` directly (for Gemini: `tests/test_dispatch_gemini.py:261-265`).
- **Allowed via explicit allowlist and line marker**:
  - `tests/test_agent_models.py:1592-1607` (`DRIFT_ALLOW_PREFIXES`, `DRIFT_ALLOW_FILES`, `DRIFT_ALLOW_SUFFIXES`) exempts `archive/`, `legacy/`, `docs/followups/`, `tests/`, `user/agent-models.json`, `user/settings.json`, `CHANGELOG.md`, `scripts/agent_models.py`, `docs/mac-mouse-preferences.md`, and image suffixes.
  - `scripts/agent_models.py:91,857-858` (`ALLOW_MARKER = "agent-models: allow"`) exempts individual lines carrying that marker (used in `docs/mac-storage-audit.md:108`).

## 3. Impact of replacing both `gemini-4-argon` fields in `user/agent-models.json`

- **Tests and scripts**:
  - None break as long as the replacement matches `[A-Za-z0-9._:/-]+` without a trailing effort tier (`scripts/agent_models.py:179-199`). `RealRegistryTests` (`tests/test_agent_models.py:466-491`), `test_repo.py:426-440`, and `test_defaults_match_the_live_registry_without_an_override` (`tests/test_dispatch_gemini.py:233-238`) validate against whatever `user/agent-models.json` resolves; all tests asserting `gemini-4-argon` build isolated temp registries via `AGENT_MODELS_FILE`.
  - If an account's `agy models` listing at runtime lacks the new family, `sync_agy` and `dispatch-gemini.py` fall back to `families.agy.fallback_model` (`gemini-4-hydrogen-high`), or skip/fail preflight if neither is listed.
- **On a machine running bootstrap**:
  - `bootstrap/bootstrap.sh:1244-1253` and `bootstrap/bootstrap.ps1:1571-1587` run `agent_models.py sync --quiet` (unless `AGENT_MODELS_SYNC` is disabled).
  - `sync_agy` (`scripts/agent_models.py:712-755`) resolves `agy`/`interactive` (`families.agy.model` + `effort`), queries `agy models`, floats `<new-stem>-high` via `newest_in_family()`, and rewrites `"model"` in `~/.gemini/antigravity-cli/settings.json` to the listed display name (saving the prior file to `settings.json.agent-models.bak`), or uses `gemini-4-hydrogen-high` if the account does not list the new primary family.
  - Updated `.agent-config/repo/user/agent-models.json` also shifts `agy`/`interactive` and `agy`/`premium` expectations in `scripts/render_banner.py`, `agent_models.py doctor`, and `agent_models.py verify`, and changes `/vet` reviewer's primary fallback in `skills/implement-review/scripts/dispatch-gemini.py` (`roles.reviewer.agy.fallback_model`, `fallback_effort: "high"`) while keeping `gemini-4-carbon-medium` as primary and `gemini-4-hydrogen-high` as second fallback.
  - `prun-worker` and `worker` (both pinned to `gemini-4-hydrogen`), Claude (`user/settings.json` / `~/.claude/settings.json`), and Codex (`~/.codex/config.toml`) are unaffected.
