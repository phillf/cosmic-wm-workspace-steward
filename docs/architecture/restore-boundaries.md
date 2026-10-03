# Restore Boundaries

## Two different operations

A cold start and a live reroute solve different problems and must remain
separate.

| Operation | Authoritative source | Purpose | Application scope |
|---|---|---|---|
| Cold start | `profiles/sysadmin/sysadmin-ws1.yaml` through `profiles/sysadmin/sysadmin-ws6.yaml` | Start the normal managed workspace set serially | Profile-defined native applications and LibreWolf windows |
| Live reroute | `sessions/sysadmin-managed-reroute-v1-ws1-ws6-no-stale-ws1-browser-2026-08-24.yaml` | Reassign matching already-open native windows to WS1–WS6 | Ten native application rules only |

## Native-only live reroute

The approved session file is named
`sysadmin-live-native-reroute` inside its YAML content. It has ten native
application rules:

- WS1: Spotify
- WS2: dedicated workspace terminal
- WS3: dedicated workspace terminal
- WS4: dedicated workspace terminal
- WS5: Visual Studio Code
- WS6: Discord, Slack, Mattermost, Signal, and GitKraken

The snapshot deliberately contains no LibreWolf matcher and no LibreWolf
command. A live reroute must not launch LibreWolf.

## Why browsers are excluded

Browser page titles are dynamic. Title-based matching can fail after redirects,
navigation, sign-in, changed active tabs, closed tabs, or a different window
organization. Earlier browser-aware reroute snapshots could respond to an
unmatched saved browser rule by launching a generic LibreWolf window.

The browser-free boundary prevents a reroute from creating an unintended
browser window. Intended browser windows remain the responsibility of the
cold-start profiles.

## What live reroute does

A live reroute can reuse a matching open native application window and assign it
to its resident workspace. It is appropriate when a supported native app is
already running but is on the wrong workspace.

## What live reroute does not do

The saved session schema does not restore:

- Browser windows, browser tabs, page identity, or browser placement
- Applications not listed in the native snapshot
- WS7 assistant/control windows
- Tile tree, split orientation, in-workspace ordering, split ratios, geometry,
  floating coordinates, stack membership, tab group state, or focus order

A successful restore message means that supported native windows matched and
were assigned to workspaces. It does not mean the original visual layout was
reconstructed.
