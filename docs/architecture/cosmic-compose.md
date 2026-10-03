# COSMIC Compose

COSMIC Compose is the declarative category and membership layer for the CT COSMIC
Workspace Manager. It records which named applications belong to operational
categories and which existing workspace profile contains them.

It is configuration metadata and read-only planning tooling, not a second window
manager. `cosmic-wm` remains responsible for launching, matching, and placing
windows.

## Purpose

COSMIC Compose makes category membership explicit and reviewable before
category-scoped workspace synchronization is introduced.

Its design goals are:

- Describe application categories as repository-owned configuration.
- Avoid guessing application intent from process names or desktop entries.
- Preserve the existing full-workspace cold-start workflow.
- Keep browser launch ownership with cold-start profiles.
- Keep the native-only live reroute browser-free.
- Support small, complete, reviewable changesets.

## Categories

The initial category taxonomy is:

| Category | Meaning |
|---|---|
| `terminals` | Interactive terminals, SSH sessions, log consoles, and command-line work surfaces |
| `browsers` | Web browsers and browser-hosted administration tools |
| `communications` | Messaging, mail, video calling, and collaboration clients |
| `git` | Version-control tools and dedicated Git work surfaces |
| `media` | Audio and video playback applications |

A category is intentional metadata. In particular, `communications`, `git`, and
`media` must be defined explicitly; they must not be inferred dynamically by a
shell script.

## Source of truth

The root [`cosmic-compose.yaml`](../../cosmic-compose.yaml) file records category
membership and references an existing workspace profile.

The existing `profiles/sysadmin-wsN.yaml` files remain authoritative for:

- Application launch commands.
- COSMIC workspace assignments.
- Window matching rules.
- COSMIC placement behavior.

COSMIC Compose may record stable match metadata needed to relate a named
application to its workspace profile. It must not duplicate launch commands,
browser state, credentials, cookies, session stores, private URLs, or other
runtime state.

When a workspace declares `scoped_profiles`, those profiles are repository-owned
cold-start definitions. Each scoped profile must have a non-empty application list,
use the workspace number it is declared for, and contain only complete application
mappings from that workspace's full profile. `cosmic-compose validate` verifies
that each scoped app belongs to its claimed category and that every declared
application in that category is represented.

## Initial WS3 inventory

The first Compose-managed workspace is `sysadmin-ws3`, the observability
workspace.

| Application | Category | Stable match |
|---|---|---|
| `workspace-terminal` | `terminals` | `class: me.creativetech.terminal.workspace3` |
| `grafana` | `browsers` | `class: librewolf`, `title: Grafana` |

The `communications`, `git`, and `media` categories are valid but currently have
no declared WS3 membership.

## WS3 scoped cold-start profiles

WS3 currently has two reviewed scoped cold-start profile definitions:

| Category | Profile | Declared applications |
|---|---|---|
| `terminals` | `profiles/sysadmin/sysadmin-ws3-terminals.yaml` | `workspace-terminal` |
| `browsers` | `profiles/sysadmin/sysadmin-ws3-browsers.yaml` | `grafana` |

No scoped profile is declared for `communications`, `git`, or `media`, because WS3
currently has no applications in those categories. A category's existence does not
make it deployable as a scoped profile.

Bootstrap is configured to install the two reviewed WS3 scoped profiles as
user-local symlinks in the COSMIC profile directory. Bootstrap does not infer
additional profile filenames from the Compose manifest; expanding scoped
deployment requires an explicit, reviewed bootstrap change.

## Ownership boundaries

COSMIC Compose must preserve the established separation of responsibilities:

| Operation | Owner | Browser behavior |
|---|---|---|
| Start intended workspace applications | Cold-start profiles | May launch their profile-defined LibreWolf windows |
| Correct an already-open supported native window's workspace | Native-only live reroute snapshot | Must not match, launch, or move LibreWolf windows |
| Classify applications and display declared scoped membership | COSMIC Compose | Reads manifest metadata and validates profiles only; does not touch windows |

A future category-specific command must select an explicit, repository-owned
scoped **cold-start** profile. It must never add category behavior to the native
live-reroute snapshot.

## Current read-only tooling

The repository provides a validation and planning command:

```bash
scripts/bin/cosmic-compose validate
scripts/bin/cosmic-compose plan sysadmin 3
scripts/bin/cosmic-compose plan sysadmin 3 terminals
scripts/bin/cosmic-compose plan sysadmin 3 browsers
scripts/bin/cosmic-compose plan sysadmin 3 media
scripts/bin/cosmic-compose profile sysadmin 3 terminals
scripts/bin/cosmic-compose profile sysadmin 3 browsers
```

`validate` checks:

- Manifest `version: 1`.
- The exact supported category set.
- Non-empty category descriptions.
- The supported WS1–WS6 sysadmin workspace range.
- Referenced full-profile paths.
- Application category membership.
- Non-empty scalar `match` metadata.
- Optional scoped-profile mappings, when declared.
- Scoped-profile paths, YAML structure, canonical names, and non-empty app lists.
- Scoped app workspace assignment and duplicate prevention.
- Exact membership in the full workspace profile.
- Declared category ownership and complete coverage of that category.

`plan` prints declared application membership for the requested workspace and
optional category:

```text
Profile: profiles/sysadmin/sysadmin-ws3.yaml
Scope: terminals
Applications:
  - workspace-terminal
```

A valid category with no declared applications is reported as `none`. An
unsupported category or undefined workspace fails with an explicit error and exit
status `2`.

`profile` resolves a declared scoped cold-start profile path from the Compose
manifest. It prints only the repository-relative path and performs no deployment
or launch action:

```text
profiles/sysadmin/sysadmin-ws3-terminals.yaml
```

If the workspace/category pair has no declared scoped profile, `profile` fails
with exit status `2`. It does not infer a filename or fall back to the full
workspace profile.

The tool is intentionally read-only. It does not:

- Render or modify profiles.
- Invoke `cosmic-wm`.
- Launch, move, close, match, or reroute windows.
- Modify bootstrap state or autostart.
- Modify Git state.
- Change `ws-man`.

`cosmic-compose` is currently invoked from `scripts/bin/`; it is not yet
installed as a `~/bin` compatibility entrypoint.

## Future command model

The current full-profile command remains:

```bash
ws-man sysadmin 3
```

The intended future scoped form is:

```bash
ws-man sysadmin 3 terminals
ws-man sysadmin 3 browsers
ws-man sysadmin 3 communications
ws-man sysadmin 3 git
ws-man sysadmin 3 media
```

A category command is not enabled merely because a category exists in the Compose
manifest or a scoped profile is present. It requires a real scoped profile that has
been authored, reviewed, committed, bootstrapped, and validated. A missing
category profile must fail clearly; it must not silently fall back to the full
workspace profile.

## Delivery sequence

1. Define category membership in `cosmic-compose.yaml`.
2. Validate and plan membership with `scripts/bin/cosmic-compose`.
3. Create and validate reviewed scoped cold-start profiles.
4. Extend `ws-man` to dispatch only to installed scoped profiles.
5. Expand category membership across the remaining managed workspaces.

## Change policy

Each COSMIC Compose change must be a targeted, complete changeset:

1. Make one coherent change.
2. Inspect the working tree and exact diff.
3. Validate syntax and scope.
4. Stage only the files required for that change.
5. Review the staged diff and path list.
6. Commit the complete logical unit.
7. Push the approved commit immediately.
8. Confirm the local branch is synchronized and clean.

## Non-goals

COSMIC Compose does not:

- Dynamically parse or rewrite live COSMIC profiles from Bash.
- Auto-classify arbitrary applications.
- Create scoped profiles without review.
- Alter autostart.
- Replace the established cold-start or native live-reroute workflows.
- Manage WS7, which remains outside the managed WS1–WS6 range.
