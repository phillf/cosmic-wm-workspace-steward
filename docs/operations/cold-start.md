# Cold Start

## Purpose

Use a cold start to launch the normal managed workspace set after a controlled
login or when the intended profile-defined applications need to be started.

Cold start owns the initial launch of native applications and the intended
LibreWolf windows defined by the WS1–WS6 profiles.

## Canonical command

    ws-man start

`ws-man start` is the canonical CT-specific cold-start command. It starts
these profiles serially:

    sysadmin-ws1
    sysadmin-ws2
    sysadmin-ws3
    sysadmin-ws4
    sysadmin-ws5
    sysadmin-ws6

The default timeout policy is 90 seconds for WS1 through WS5 and 180 seconds
for WS6.

Preview the complete serial plan without launching or moving windows:

    ws-man start --dry-run

Override every profile timeout intentionally when needed:

    ws-man start --timeout 180

For desktop-launcher and graphical-login-autostart compatibility,
`~/.local/bin/start-sysadmin-cold` remains installed as a thin wrapper around
`ws-man start`. Its repository source is
`scripts/local-bin/start-sysadmin-cold`.

The `sysadmin` option in `~/bin/launch-workspace-profile` delegates to this
same cold-start workflow.

## When to use it

Use cold start when:

- Starting the managed workstation layout after graphical login
- Recreating intended profile-defined browser windows
- Starting missing managed applications intentionally
- Performing a controlled fresh start of WS1–WS6

Do not use cold start merely to move a supported native application that is
already open on the wrong workspace. Use the native-only live reroute for that
case.

## Desktop launchers

Two tracked desktop assets invoke the cold-start workflow:

| Asset | Purpose |
|---|---|
| `scripts/desktop/sysadmin-cold-start.desktop` | Manual cold-start application launcher |
| `scripts/autostart/start-sysadmin.desktop` | Optional graphical-login autostart source |

The profile chooser desktop shortcut invokes
`~/bin/launch-workspace-profile --prompt`; selecting `sysadmin` runs the same
cold-start workflow.

## Validate after startup

Run:

    cosmic-wm status

Confirm expected managed applications are present in WS1 through WS6. Browser
windows are launched by their owning profiles, but their current page title,
active tab, and tab organization can change after startup.

The current tooling does not reconstruct tile order, geometry, split ratios,
stack/tab groups, or focus order.
