# ws-man Operations Guide

`ws-man` is the operator-facing command for the CT sysadmin COSMIC workspace
layout. It supports a full-layout reconciliation decision, individual workspace
re-sync, live native-window reroute, serial cold start, safe window purge, and
read-only status inspection.

> **Beta safety boundary:** Test this tooling in a non-production COSMIC session
> before operational use. Run `--dry-run` before every workflow that can launch,
> move, or close windows. Save work before `ws-man purge --yes`; applications
> can prompt for unsaved data or decline a normal close request. This project
> does not replace backups or desktop-session recovery procedures.

## Quick reference

```bash
ws-man sysadmin --dry-run
ws-man sysadmin
ws-man sysadmin 3 --dry-run
ws-man sysadmin --cold --dry-run
ws-man sysadmin --reroute --dry-run
ws-man purge --dry-run
ws-man status
```

## Sysadmin reconciliation

```bash
ws-man sysadmin
```

With no workspace number, `ws-man` chooses a mode from the current native
window inventory:

- **Reroute** when it detects a supported managed native application.
- **Cold start** when it finds no supported managed native application.

Use `--dry-run` to print the selected mode and underlying COSMIC command:

```bash
ws-man sysadmin --dry-run
```

Force a mode when operational intent is known:

```bash
ws-man sysadmin --cold
ws-man sysadmin --reroute
```

Target one workspace only:

```bash
ws-man sysadmin 1
ws-man sysadmin 2
ws-man sysadmin 3
ws-man sysadmin 4
ws-man sysadmin 5
ws-man sysadmin 6
```

The compatibility commands remain supported:

```bash
ws-man start
ws-man reroute
```

`start` performs the serial cold start. `reroute` invokes the approved native
live-reroute snapshot.

## Cold-start behavior

Cold start processes `sysadmin-ws1` through `sysadmin-ws6` serially:

| Scope | Default timeout |
|---|---:|
| Workspace 1–5 | 90 seconds |
| Workspace 6 | 180 seconds |

Preview before launching anything:

```bash
ws-man sysadmin --cold --dry-run
```

The installed `start-sysadmin-cold` launcher is symlink-safe: it resolves its
real repository path before delegating to `ws-man start`.

## Live reroute boundaries

Live reroute uses:

```text
cosmic-wm restore --timeout 30 sysadmin-live-reroute
```

The approved session handles supported native applications only. It does not
create, close, match, move, restore, or otherwise alter LibreWolf/browser
windows or browser state. It does not restore tiling geometry, split ratios,
stacks, window sizes, or affect workspace 7.

## Purge visible windows

`ws-man purge` is separate from reroute. It is intended for a controlled reset
before a deliberate cold start.

It inventories full window identities from:

```bash
cos-cli info --json
```

and closes eligible windows one at a time with their current `cos-cli` index.
It refreshes inventory before every close selection, so it does not rely on an
index retained after a previous window disappears.

Always inspect the plan first:

```bash
ws-man purge --dry-run
```

After saving work, execute:

```bash
ws-man purge --yes
```

By default, purge preserves these terminal identities:

```text
com.system76.CosmicTerm
me.creativetech.terminal.workspace2
me.creativetech.terminal.workspace3
me.creativetech.terminal.workspace4
```

Optional behavior:

```bash
ws-man purge --yes --keep-spotify
ws-man purge --yes --include-terminal
ws-man purge --yes --max-attempts 5
```

- `--keep-spotify` preserves Spotify.
- `--include-terminal` also permits closure of COSMIC and managed CT terminals.
  Use it from a TTY or a disposable terminal because it can end the invoking
  terminal session.
- `--max-attempts COUNT` sets the maximum close requests for one stable
  `(app_id, title)` identity; the default is 3.
- If an app remains after the retry limit, purge reports it as unresolved and
  exits nonzero rather than looping forever.

Purge requests normal application closure through `cos-cli close --index`. It
does not kill processes, delete configuration, alter profile YAML, or launch
applications. Applications can still prompt for unsaved work or decline a
close request.

A clean rebuild sequence is:

```bash
ws-man purge --dry-run
ws-man purge --yes --include-terminal
ws-man sysadmin --cold --dry-run
ws-man sysadmin --cold
```

## Read-only operations

```bash
ws-man status
ws-man terminal-font status
ws-man terminal-font plan --size 14 --target wezterm
ws-man terminal-font plan --size 14 --all
```

Terminal-font commands inspect and plan only; they do not write terminal
configuration.

## Bash completion

The Bash completion definition is repository-managed at:

```text
completions/bash/ws-man
```

It completes `ws-man` subcommands, workspace numbers, supported flags, and
terminal-font targets.

Install it for the current user:

```bash
mkdir -p ~/.local/share/bash-completion/completions

ln -sfn \
  ~/Projects/ct/cosmic-wm-workspace-steward/completions/bash/ws-man \
  ~/.local/share/bash-completion/completions/ws-man
```

Load it in the current Bash shell:

```bash
source ~/Projects/ct/cosmic-wm-workspace-steward/completions/bash/ws-man
```

Useful completion points:

```bash
ws-man <Tab><Tab>
ws-man sysadmin <Tab><Tab>
ws-man purge --<Tab><Tab>
ws-man terminal-font plan --target <Tab><Tab>
```
