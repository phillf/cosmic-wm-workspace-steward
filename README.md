# COSMIC Workspace Steward

## Development disclosure

This project was developed with substantial assistance from AI coding tools
("vibe coding"). AI-generated changes are reviewed and validated by the
maintainer, but this software is provided as-is and may contain defects.

Review scripts and configuration before use, test changes in a non-production
desktop session where practical, and keep backups of workspace-related
configuration. Do not rely on this project as the sole recovery mechanism for
critical desktop state.

A YAML-driven workspace profile and session stewardship project for COSMIC Desktop.
The current implementation is a CT-specific reference deployment operated through
`ws-man` and backed by `cosmic-wm`.

> Unofficial community tooling. COSMIC Workspace Steward is not affiliated with,
> endorsed by, or maintained by System76 or the COSMIC Desktop project.

## Current implementation

The current reference deployment provides:

- `ws-man start` for the canonical serial CT sysadmin cold start.
- `ws-man sysadmin NUMBER` for installed CT sysadmin workspace profiles.
- `ws-man reroute` for the approved native-only CT live-reroute session.
- `ws-man status` for inspecting active COSMIC application and workspace state.
- A bootstrap script that deploys declared CT profiles, sessions, wrappers, and
  optional autostart assets as symlinks.

It does not yet provide generic profile/session discovery, arbitrary profile or
session selection, import, promotion, migration, package installation, or a
general-purpose interactive installer.

## Generic evolution
The generic architecture is documented in
[`docs/design/cosmic-workspace-steward-design.md`](docs/design/cosmic-workspace-steward-design.md).

An initial generic, non-mutating Python core is implemented. It resolves
user-owned XDG artifact roots and safely loads non-empty YAML mappings. It does
not yet provide generic `ws-man` commands, artifact discovery, COSMIC adapter
probing, dry-run planning, import, migration, apply, restore, or desktop
mutation.

For executable non-production checks and the current capability boundary, see
the [Beta 2 operator test matrix](docs/operations/beta-2-operator-test-matrix.md).
## Scope

WS1 through WS6 are the managed operational workspace range. WS7 is a protected
assistant/control workspace and remains outside managed cold-start and live-reroute
operations.

The repository supports two separate workflows:

| Workflow | Purpose | Browser behavior |
|---|---|---|
| Cold start | Start the normal WS1–WS6 managed workspace set serially | Launches profile-defined LibreWolf windows |
| Native live reroute | Correct placement of already-open supported native windows | Browser-free; must not launch, match, or move LibreWolf |

These workflows are not interchangeable.

## Quick start

### Start the managed workspace set

```bash
ws-man start
```

This starts `sysadmin-ws1` through `sysadmin-ws6` serially, using 90-second
timeouts for WS1–WS5 and 180 seconds for WS6. Use it after a controlled login
or when intended profile-defined applications, including managed browser windows,
need to be launched.

Preview the complete plan without launching or moving windows:

    ws-man start --dry-run

Override every profile timeout intentionally when needed:

    ws-man start --timeout 180

`~/.local/bin/start-sysadmin-cold` remains available as the desktop and
graphical-login-autostart-compatible wrapper around `ws-man start`.

### Correct an already-open native window

Use the independent `ws-man reroute` operation to route already-open supported
native windows through the approved live-reroute session:

```bash
ws-man reroute
```

The reroute default timeout is 30 seconds. Override it for one operation when
needed:

```bash
ws-man reroute --timeout 45
```

Enable COSMIC debug output:

```bash
ws-man reroute --debug
```

Preview the resolved command without moving windows:

```bash
ws-man reroute --timeout 45 --debug --dry-run
```

`ws-man reroute` is independent of workspace profiles. It uses only the approved
installed `sysadmin-live-reroute` session, which contains exactly ten native rules:

- WS1: Spotify
- WS2–WS4: dedicated workspace terminals
- WS5: Visual Studio Code
- WS6: Discord, Slack, Mattermost, Signal, and GitKraken

It excludes all browser windows and WS7. It does not launch missing applications,
create browser windows, restore browser state, or restore tile order, geometry,
sizes, split ratios, stacks, or tab groups.

The equivalent lower-level command is:

```bash
cosmic-wm restore \
  --timeout 30 \
  --debug \
  sysadmin-live-reroute
```

### Refresh one workspace profile

```bash
ws-man sysadmin 3
```

This re-synchronizes the existing `sysadmin-ws3` profile with the default
180-second application/window matching timeout.

Preview a refresh without launching applications or moving windows:

```bash
ws-man sysadmin 3 --dry-run
```

## Supported behavior

| Capability | Result |
|---|---|
| Start WS1–WS6 cold-start profiles serially | Supported |
| Launch profile-defined LibreWolf windows during cold start | Supported |
| Refresh one existing sysadmin profile with `ws-man` | Supported |
| Route the ten supported native rules to WS1–WS6 | Supported |
| Keep WS7 outside the approved native reroute input | Supported |
| Use native reroute to create missing browser windows | Not supported |
| Restore browser tabs, page identity, or browser placement | Not supported |
| Restore in-workspace tile order | Not supported |
| Restore sizes, split ratios, or geometry | Not supported |
| Restore stacks or tab groups | Not supported |

## Repository structure

```text
cosmic-compose.yaml  Declarative COSMIC Compose category metadata
profiles/            Canonical WS1–WS6 cold-start profile definitions
sessions/            Approved native-only live-reroute snapshot
scripts/             Launchers, desktop assets, autostart source, and bootstrap tooling
docs/                Architecture, operations, troubleshooting, and references
```

## Read next

- [Workspace model](docs/architecture/workspace-model.md)
- [COSMIC Compose](docs/architecture/cosmic-compose.md)
- [Launch ownership](docs/architecture/launch-ownership.md)
- [Browser boundaries](docs/architecture/browser-boundaries.md)
- [Cold-start procedure](docs/operations/cold-start.md)
- [Live-reroute procedure](docs/operations/live-reroute.md)
- [Recovery procedure](docs/operations/recovery.md)
- [Beta 2 operator test matrix](docs/operations/beta-2-operator-test-matrix.md)
- [Canonical commands](docs/reference/canonical-commands.md)
- [Expected workspace windows](docs/reference/expected-workspace-windows.md)
- [Legacy tool inventory](docs/reference/legacy-tool-inventory.md)

## Deployment

The repository is the source of truth. The bootstrap deploys repository-managed
assets as user-local links after reviewing its planned changes:

```bash
./scripts/bootstrap.sh --dry-run --force
./scripts/bootstrap.sh --force
```

Use `--install-autostart` only when intentionally deploying the tracked
graphical-login autostart entry.

The installed profile chooser is expected to resolve as:

```text
~/.local/share/applications/ct-workspace-profile.desktop
  -> scripts/desktop/ct-workspace-profile.desktop
  -> ~/bin/launch-workspace-profile
  -> scripts/bin/launch-workspace-profile
```

Selecting `sysadmin` in that chooser invokes `~/.local/bin/start-sysadmin-cold`.

After running `./scripts/bootstrap.sh --force`, the repository also installs the
managed command path:

```text
~/bin/ws-man
  -> scripts/bin/ws-man
```

## Safety

- Do not use live reroute to start missing applications or browser windows.
- Do not add LibreWolf matchers or generic browser commands to the native
  reroute snapshot.
- Do not use `pkill librewolf` for selective browser cleanup.
- Do not commit credentials, browser profiles, cookies, session stores, private
  URLs, or local runtime state.
- Review every deployment and Git diff before applying it.

## `ws-man` command library

```bash
# Cold-start WS1 through WS6 serially: WS1–WS5 use 90 seconds; WS6 uses 180.
ws-man start

# Preview the six cold-start commands without launching applications or moving windows.
ws-man start --dry-run

# Apply one intentional timeout to every cold-start profile.
ws-man start --timeout 180

# Re-sync one existing sysadmin workspace.
ws-man sysadmin 1
ws-man sysadmin 6

# The default profile timeout is 180 seconds; override it when needed.
ws-man sysadmin 3 --timeout 45
ws-man sysadmin 6 --timeout 300

# Preview a profile refresh without launching applications or moving windows.
ws-man sysadmin 4 --dry-run

# Route already-open supported native windows with a 30-second default.
ws-man reroute

# Preview a reroute without moving windows.
ws-man reroute --timeout 45 --debug --dry-run

# Show current COSMIC application-to-workspace assignments.
ws-man status
```

`ws-man` supports serial cold start, full-profile synchronization, approved
native live reroute, and status. Managed window cleanup and category-scoped
synchronization will be
added separately after their manifests and scoped profiles are repository-owned,
reviewed, and bootstrap-managed.

## COSMIC Compose

[COSMIC Compose](docs/architecture/cosmic-compose.md) is the repository's
declarative category and workspace-membership model. Its initial metadata
inventory is in [`cosmic-compose.yaml`](cosmic-compose.yaml).

The initial category taxonomy is:

- `terminals`
- `browsers`
- `communications`
- `git`
- `media`

COSMIC Compose currently documents WS3 application membership and provides
read-only validation and planning:

```bash
scripts/bin/cosmic-compose validate
scripts/bin/cosmic-compose plan sysadmin 3
scripts/bin/cosmic-compose plan sysadmin 3 terminals
scripts/bin/cosmic-compose plan sysadmin 3 browsers
scripts/bin/cosmic-compose plan sysadmin 3 media
scripts/bin/cosmic-compose profile sysadmin 3 terminals
scripts/bin/cosmic-compose profile sysadmin 3 browsers
```

The tool validates the manifest and any explicitly declared scoped cold-start
profiles, then prints declared membership only. Scoped profiles are verified as
complete category-specific subsets of their full workspace profile; they are not
rendered or deployed by this command. It does not modify bootstrap behavior,
change `ws-man`, alter autostart, modify COSMIC profile deployment, or launch or
move windows.

`cosmic-compose profile` resolves a declared scoped profile path only. It does
not install that profile, invoke `cosmic-wm`, or enable category dispatch in
`ws-man`.

WS3 currently has reviewed scoped cold-start definitions for `terminals` and
`browsers`. Bootstrap is configured to install those two reviewed WS3 scoped
profiles as user-local symlinks. Their presence does not yet enable
`ws-man sysadmin 3 <category>`; category dispatch remains a separate change.

Future category-scoped synchronization will use explicit, reviewed cold-start
profiles and will preserve the browser-free native live-reroute boundary.
