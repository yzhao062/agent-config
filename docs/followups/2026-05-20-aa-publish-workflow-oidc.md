# FOLLOW-UP: aa publish.yml (PyPI + npm OIDC, removes manual upload chore)

**Status**: Open. Not part of any current release.
**Driver**: v0.7.0 release on 2026-05-19 hit an expired npm token during `npm publish` (E401), then a non-Bypass-2FA token (EOTP) on retry. The local `twine upload` + `npm publish` step is the only manual chore left in the release pipeline and is the most likely place for a release to stall on credential rot.
**Owner**: Yue (driver) + Claude (implementer).

## Purpose

Replace the manual `twine upload` + `npm publish` step in `RELEASING.md` with a GitHub Actions workflow that fires on release-published and pushes both packages without any locally-managed credentials. The human gate stays the "Publish release" click in the GitHub UI; everything after that is automatic.

## Today (manual)

Per `RELEASING.md` § "Release sequence" steps 7-8:

1. Maintainer runs `python -m build` locally.
2. `python -m twine check` + `twine upload` to PyPI (needs `~/.pypirc` PyPI API token).
3. `npm publish packages/npm` (needs `~/.npmrc` Bypass-2FA Automation token).
4. `gh release create v0.7.0` to fire the post-publish `package-smoke.yml` + `real-agent-smoke.yml`.

Failure modes observed on v0.7.0:
- Expired PyPI token: would block step 2. (Did not hit; PyPI uploaded fine.)
- Expired npm token (E401): blocked step 3 on 2026-05-19.
- Non-Bypass-2FA npm token (EOTP): blocked step 3 on the first retry; needs either a Granular Access Token with "Bypass 2FA" enabled or an interactive browser-auth round-trip.

## Proposed (OIDC-based, no maintainer-side credentials)

### `.github/workflows/publish.yml` sketch

```yaml
name: Publish

on:
  release:
    types: [published]

jobs:
  pypi:
    runs-on: ubuntu-latest
    environment: release  # optional GitHub Environment + required reviewer
    permissions:
      id-token: write      # OIDC token for PyPI Trusted Publishing
      contents: read
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: "3.12"
      - name: Build sdist + wheel
        run: |
          python -m pip install --upgrade build
          python -m build packages/pypi --outdir dist
      - name: Publish to PyPI (Trusted Publishing OIDC)
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: dist

  npm:
    runs-on: ubuntu-latest
    environment: release
    permissions:
      id-token: write      # OIDC token for npm trusted publishing (2025+) + provenance
      contents: read
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v5
        with:
          node-version: "20"
          registry-url: "https://registry.npmjs.org"
      - name: Publish to npm with provenance
        working-directory: packages/npm
        run: npm publish --provenance --access public
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}  # only if OIDC trusted publishing not yet enabled
```

### One-time setup

**PyPI Trusted Publishing**:
1. https://pypi.org/manage/account/publishing/ -> "Add a new pending publisher".
2. Fields: project name `anywhere-agents`, owner `yzhao062`, repo `anywhere-agents`, workflow `publish.yml`, environment `release` (optional but recommended).
3. After the first run lands, PyPI converts the pending publisher into a permanent trusted publisher. No API token in `~/.pypirc` or GitHub secrets is involved.

**npm Trusted Publishing (preferred, 2025+)**:
1. https://www.npmjs.com/package/anywhere-agents/access -> "Trusted Publishers" tab.
2. Add a GitHub Actions publisher: owner `yzhao062`, repo `anywhere-agents`, workflow `.github/workflows/publish.yml`, environment `release`.
3. Drop `NPM_TOKEN` from the workflow env once OIDC is verified working.

**npm token fallback (until OIDC is enabled on the package)**:
1. Generate a Granular Access Token with read+write on `anywhere-agents` AND "Bypass Two-Factor Authentication" checked.
2. Add as a repo secret `NPM_TOKEN` in https://github.com/yzhao062/anywhere-agents/settings/secrets/actions.
3. The workflow above already references `${{ secrets.NPM_TOKEN }}`; remove the line once OIDC is live.

**GitHub Environment (optional, recommended)**:
1. https://github.com/yzhao062/anywhere-agents/settings/environments -> "New environment" named `release`.
2. Add a "Required reviewers" rule listing the maintainer. This re-introduces a click-to-confirm gate between "Publish release" and the actual upload, so the maintainer can abort if anything looks off on the release page.

### Trigger choice (release-published vs tag push)

The sketch above uses `on: release: types: [published]`, which means:
- Tagging + pushing the tag alone does NOT trigger publish.
- The maintainer creates a GitHub Release (via `gh release create` or the UI) - this IS the human gate.
- Publish fires after the release is marked published, and the existing `package-smoke.yml` + `real-agent-smoke.yml` (already release-published-triggered) run in parallel to verify the post-publish state.

Alternative: `on: push: tags: [v*]` - simpler but loses the "Publish release" click as a human gate. Not recommended unless paired with a GitHub Environment that requires reviewer approval.

## Non-goals

- **Spark dual-OS test integration**: `RELEASING.md` § "Dual-OS local test" runs the suite on the maintainer's ARM64 Linux box (DGX Spark). That step is NOT moved into CI as part of this follow-up because it requires a self-hosted runner on Spark. The Spark test stays a manual pre-release item; the Ubuntu + Windows CI legs in `validate.yml` cover the x86_64 portion.
- **Removing local twine/npm tooling**: `RELEASING.md` continues to document the manual fallback for situations where the GH Actions runner is unavailable (npm outage, PyPI outage, OIDC misconfiguration). The maintainer's local `~/.pypirc` + `~/.npmrc` setup is no longer the default path, but it remains the documented fallback.
- **Bumping versions automatically**: This workflow only publishes. The version-bump commit and the `gh release create` step stay manual so the maintainer keeps full control of what gets released.
- **OIDC for agent-config or agent-style**: Out of scope. The aa repo is the only one with PyPI + npm distribution; `agent-config` and `agent-style` ship via different mechanisms.

## Regression and failure analysis

| Risk | Mitigation |
|---|---|
| OIDC misconfigured on first run -> publish fails | Trusted-publishing setup is reversible; the first failed run leaves the package untouched. The fallback path (manual `twine upload`) is documented in `RELEASING.md`. |
| Workflow drift from `bootstrap.sh`'s sparse-clone (the bootstrap fetches `bootstrap.sh` via curl, not via npm/pip) | None - bootstrap.sh delivery is independent of PyPI/npm. The publish workflow only ships the wheel + npm package, not bootstrap.sh. |
| GitHub Environment review gate is bypassed | The `release` environment + required-reviewer rule are the gate. If skipped, publish fires immediately on release-published; abort via deleting the release before the workflow finishes (race-y; the required-reviewer rule is the real backstop). |
| Wrong content uploaded (e.g., dirty checkout, untracked files) | The workflow checks out the tagged ref via `actions/checkout@v5` on the `release` event payload, so only committed content ships. Local maintainer disk state cannot leak. |
| Provenance attestation rejected by npm | `--provenance` is opt-in and additive; rejection would mean npm provenance is misconfigured for the package, not that the publish fails. Can omit `--provenance` if it ever blocks. |
| PyPI Trusted Publishing token leaked via workflow misuse | OIDC tokens are short-lived (minutes) and scoped to the workflow run; even if a workflow log is captured, the token is already invalid by then. Far safer than the long-lived API tokens in `~/.pypirc`. |

## Validation plan

1. Land `.github/workflows/publish.yml` in a separate PR with the OIDC setup completed in advance (so the workflow can fire successfully on the first release after merge).
2. Pre-release on `v0.7.1` (or whatever the next version is): run a release-candidate flow:
   - Tag a pre-release like `v0.7.1rc1` to the repo.
   - `gh release create v0.7.1rc1 --prerelease` -> verify publish.yml fires + uploads to PyPI's pre-release channel + npm with `rc1` dist-tag.
   - `pip install anywhere-agents==0.7.1rc1` + `npm install anywhere-agents@rc1` -> verify install works.
3. After RC validation, do the real `v0.7.1` release the new way and confirm:
   - PyPI publish via OIDC: no `~/.pypirc` involvement.
   - npm publish via OIDC: no `~/.npmrc` involvement.
   - `package-smoke.yml` + `real-agent-smoke.yml` fire in parallel and pass.
4. Update `RELEASING.md` to point at the new workflow and demote the manual `twine upload` / `npm publish` steps to a "fallback" subsection.

## Effort

- Workflow file: 30 min (~40 lines + comments).
- PyPI Trusted Publishing setup: 10 min via the web UI.
- npm Trusted Publishing setup: 10 min via the web UI (once enabled on `anywhere-agents`).
- Optional GitHub Environment + reviewer rule: 5 min.
- Doc updates to `RELEASING.md`: 30 min.
- One RC release to validate end-to-end: ~30 min of wall time (mostly waiting on workflow runs).

Total: about half a day of focused work, ships as a normal patch alongside the next aa release.
