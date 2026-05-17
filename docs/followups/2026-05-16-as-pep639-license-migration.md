# agent-style: PEP 639 license metadata migration (hard deadline 2027-02-18)

**Status**: open. **Source**: `agent-style/TODO.md:155-188` (carried from v0.3.4). **Target**: before **2027-02-18** when setuptools deprecates the legacy license-classifier metadata form.

## Why this file exists

The full action plan lives in `agent-style/TODO.md:155-188`, where the maintainer correctly tracked it at v0.3.4. This local file is not a duplicate; it is a maintainer-visible-from-ac surfacing of the **hard external deadline** so the cliff is not missed. PyPI and setuptools deprecation cliffs do not announce themselves loudly at the threshold; missing the date means agent-style upload breaks until migrated.

Most agent-style TODO.md items stay in agent-style (per `docs/followups/README.md` convention). This one promotes because of the hard external deadline, which the convention's exception clause should cover.

## Symptom

`agent-style/packages/pypi/pyproject.toml:14` currently uses the deprecated table form for license metadata: `license = { text = "MIT AND CC-BY-4.0" }`. Setuptools now expects a PEP 639 SPDX license expression as a string in `project.license`, plus `project.license-files` for bundled license files. Future setuptools releases will stop supporting the table form.

## Suggested approach

Per the plan in `agent-style/TODO.md:155-188`, three edits:

1. `agent-style/packages/pypi/pyproject.toml`: replace the table license with the PEP 639 form:
   ```toml
   license = "MIT AND CC-BY-4.0"
   license-files = ["agent_style/data/LICENSES/*.txt"]
   ```
   Path is relative to `packages/pypi/pyproject.toml` (the build root); the bundled license files at `agent_style/data/LICENSES/{MIT,CC-BY-4.0}.txt` are what setuptools should glob.
2. Verify with `python -m build && twine check dist/*`. The build should no longer emit the `project.license` table-form deprecation warning, and both the wheel and sdist should include the license files.
3. Bump the agent-style version for the release and add the CHANGELOG note.

## When to pull in

**Latest sensible window**: 2026-12 to 2027-01, two to three months before the 2027-02-18 setuptools removal cliff. Earlier is fine. Tie to the next routine agent-style release if one is happening in that window.

**Trigger condition for earlier action**: a future twine release that stops accepting the table form (twine 6.x notes a "stricter validation" intent; check release notes before each agent-style ship).

## Effort estimate

1-2 hours: 1 pyproject.toml edit + 1 dist + twine verification + bump-version + tag + push + CHANGELOG note.

## Cross-references

- `agent-style/TODO.md:155-188`: original plan with full deadline rationale and fix sketch
- PEP 639 reference: https://peps.python.org/pep-0639/
- setuptools deprecation timeline: https://setuptools.pypa.io/en/latest/userguide/pyproject_config.html#configuring-metadata
