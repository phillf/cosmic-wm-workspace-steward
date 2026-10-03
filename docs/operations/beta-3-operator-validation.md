# Beta 3 Operator Validation

## Release candidate

- Release: `2026.9.1-beta.3`
- Candidate branch: `develop`
- Candidate commit: `ddb1cccb7e67b8ada5d4e6cda43025d939f8b582`
- GitLab pipeline: [6208](https://git.creativetech.me/pjfernandes/cosmic-wm-workspace-steward/-/pipelines/6208)
- Pipeline jobs: `validate` and `test` succeeded
- Local validation environment: Python 3.12.3
- Local test result: 115 passed

## Validated checks

The following checks passed for the release candidate:

```bash
bash -n scripts/bin/ws-man
bash -n scripts/bootstrap.sh
bash -n completions/bash/ws-man
python scripts/ws_man_policy.py validate
git diff --check HEAD^ HEAD
python -m pytest -q
```

The GitLab pipeline uses Python 3.12, installs the editable project with
`python3 -m pip install -e '.[test]'`, runs the same repository validation
checks, and invokes tests with `python3 -m pytest -q`.

## Operator safety boundary

- Test this beta in a non-production COSMIC session before operational use.
- Run `--dry-run` before every workflow that can launch, move, or close windows.
- Run `ws-man purge --dry-run` before considering `ws-man purge --yes`.
- Save work before purge. Purge submits normal application-close requests;
  applications can prompt for unsaved work or decline to close.
- Keep backups of workspace-related configuration. This tooling is not a
  replacement for desktop-session recovery procedures.
- Validate behavior against the installed COSMIC desktop environment before
  relying on the tooling for an operational workflow.

## Explicit non-goals

The beta does not guarantee restoration or control of:

- LibreWolf/browser state, tabs, or page identity
- Browser-window creation or placement through native live reroute
- Tile order, geometry, sizes, split ratios, stacks, or tab groups
- Workspace 7, which remains outside the managed WS1–WS6 scope

## Merge controls

The `develop` branch is protected:

- Direct pushes are disabled.
- Merges are limited to maintainers.
- Force pushes are disabled.
- Successful GitLab pipelines are required before merge.
- Source branches are deleted automatically after merge.

## Versioning

Git tags are the authoritative release identifiers for this repository. The
internal Python package remains at version `0.0.0` because it is not published
as an independently versioned distribution.

The project uses calendar versioning:

```text
YYYY.MM.REVISION[-PRERELEASE.N]
```

- `YYYY` is the release-train year.
- `MM` is the release-train month.
- `REVISION` increments for materially distinct releases in that month and
  resets when the month changes.
- `-beta.N` identifies an unstable beta in that monthly release train.
- A release can be tagged shortly after month end when completing the prior
  month's documented release train.

`2026.9.1-beta.3` is the September 2026 release closeout. New work beginning
in October belongs to `2026.10.0` or a later October release milestone.
