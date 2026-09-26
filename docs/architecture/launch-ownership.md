# Launch Ownership

## Purpose

This document defines which component may start an application and which
component may only route an already-open window. Keeping those responsibilities
separate prevents duplicate launches and makes recovery predictable.

## Canonical startup path

The managed graphical-login and profile-selection path is:

```text
start-sysadmin-cold
  -> ws-man start
      -> cosmic-wm start sysadmin-ws1 --timeout 90
      -> cosmic-wm start sysadmin-ws2 --timeout 90
      -> cosmic-wm start sysadmin-ws3 --timeout 90
      -> cosmic-wm start sysadmin-ws4 --timeout 90
      -> cosmic-wm start sysadmin-ws5 --timeout 90
      -> cosmic-wm start sysadmin-ws6 --timeout 180
```

The canonical deployed command is:

```bash
~/.local/bin/start-sysadmin-cold
```

Its repository source is:

```text
scripts/local-bin/start-sysadmin-cold
```

The `sysadmin` option in `launch-workspace-profile` also resolves to this
canonical launcher.

## Ownership matrix

| Component | May launch native apps | May launch LibreWolf | May reroute open native windows | May manage WS7 |
|---|---:|---:|---:|---:|
| WS1–WS6 cold-start profiles | Yes | Yes | No | No |
| `start-sysadmin-cold` | Invokes profiles serially | Indirectly, through profiles | No | No |
| Native-only live reroute snapshot | No; it expects matches | No | Yes | No |
| `workspace-profile --profile sysadmin` | Delegates to cold start | Indirectly, through cold start | No | No |
| Manual operator action | Only when intentional | Only when intentional | Only when intentional | Do not alter through managed reroute |

## Rules

1. Start the normal managed workspace set with `start-sysadmin-cold`.
2. Use a cold-start profile to launch its intended applications, including its
   profile-defined LibreWolf windows.
3. Use the native-only reroute snapshot only to correct the placement of
   already-open supported native applications.
4. Do not add browser launch commands or browser matchers to the live reroute
   snapshot.
5. Do not use the live reroute snapshot as a substitute for cold start.
6. Keep WS7 outside every managed reroute input.
7. Treat `~/bin` as compatibility entrypoints; the repository is the source of
   truth for active workspace-manager launch assets.

## Example

If GitKraken is open on WS3, use the native-only live reroute to return it to
WS6. If the WS2 GitLab browser window is missing, use the normal cold-start
workflow or intentionally launch that browser window; do not use native reroute
to create it.
