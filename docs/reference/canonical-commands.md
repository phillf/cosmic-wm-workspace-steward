# Canonical Commands

> **Current CT reference deployment:** These commands document the currently
> implemented CT-specific wrapper, profiles, session assets, and launch paths.
> They are not the future generic COSMIC Workspace Steward CLI contract.


## Cold start

Start the complete managed WS1–WS6 set:

    ws-man start

Use cold start when intended profile-defined applications or managed LibreWolf
windows need to be launched. The default serial policy is 90 seconds for WS1
through WS5 and 180 seconds for WS6.

Preview the complete plan without launching or moving windows:

    ws-man start --dry-run

Apply one intentional timeout to every profile when needed:

    ws-man start --timeout 180

`~/.local/bin/start-sysadmin-cold` remains the desktop/autostart-compatible
wrapper around `ws-man start`.

## Workspace profile chooser

Open the graphical profile chooser:

```bash
~/bin/launch-workspace-profile --prompt
```

Select `sysadmin` to invoke `~/.local/bin/start-sysadmin-cold`.

For the command-line compatibility launcher:

```bash
workspace-profile --profile sysadmin
```

## Native live reroute

Use live reroute only when a supported native application window is already open
and needs to be returned to its resident workspace.

Preferred command:

```bash
ws-man reroute
```

The default timeout is 30 seconds. Override it for one operation when needed:

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

`ws-man reroute` is independent of profiles and always uses only the approved
installed `sysadmin-live-reroute` session. It does not accept a workspace,
profile, category, baseline, or arbitrary session argument.

The equivalent lower-level command is:

```bash
cosmic-wm restore \
  --timeout 30 \
  --debug \
  sysadmin-live-reroute
```

The approved snapshot has ten supported native rules: Spotify; the WS2, WS3, and
WS4 dedicated terminals; Visual Studio Code; and Discord, Slack, Mattermost,
Signal, and GitKraken.

It has no browser rules. Do not use it to start missing applications, launch
LibreWolf, create, match, move, close, or restore browser windows, restore browser
state, restore geometry or tile order, or manage WS7.

## Status

Inspect current COSMIC workspace/window state:

```bash
cosmic-wm status
```

## Workspace terminals

Open a dedicated terminal with its stable class:

```bash
~/bin/open-workspace-terminal 2
~/bin/open-workspace-terminal 3
~/bin/open-workspace-terminal 4
```

## Restricted commands and artifacts

| Artifact | Status |
|---|---|
| `~/bin/backups/workspace-manager-cleanup-20260917-150404/` | Legacy archive for audit/rollback only |
| Archived `startSysadmin.sh` | Do not run; replaced by `~/.local/bin/start-sysadmin-cold` |
| Archived `restore-sysadmin-complete` | Do not run; obsolete snapshot and unsafe behavior |
| Historical patch, conversion, and browser helper scripts | Do not run; retained in the dated archive |
| `pkill librewolf` | Do not use for selective cleanup; may close unrelated or WS7 browser work |
