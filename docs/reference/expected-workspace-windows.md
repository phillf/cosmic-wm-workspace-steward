# Expected Workspace Windows

This inventory defines the intended applications launched by the canonical
cold-start profiles:

- `profiles/sysadmin/sysadmin-ws1.yaml`
- `profiles/sysadmin/sysadmin-ws2.yaml`
- `profiles/sysadmin/sysadmin-ws3.yaml`
- `profiles/sysadmin/sysadmin-ws4.yaml`
- `profiles/sysadmin/sysadmin-ws5.yaml`
- `profiles/sysadmin/sysadmin-ws6.yaml`

The profile YAML files are the source of truth. Update this document in the same
commit as any profile change that adds, removes, or materially changes a
managed application.

## Scope boundary

This is a cold-start inventory, not a live-reroute inventory.

Cold-start profiles may launch the listed native applications and LibreWolf
windows. The approved live reroute is browser-free and covers only ten
already-open native rules: Spotify; the WS2–WS4 dedicated terminals; Visual
Studio Code; and the five WS6 communication/client applications.

Browser windows are intentionally outside live reroute.

## Shared LibreWolf model

All profile-managed browser windows use the normal shared LibreWolf session:

```text
/usr/bin/librewolf --new-window <URL>
```

A profile-managed browser window is distinct from unrelated LibreWolf windows
or tabs that may also be open. Profile matching is governed by the configured
`class` and `title` fields rather than incidental runtime suffixes such as
`Original profile — LibreWolf`.

## Workspace 1 — General

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| YouTube | `https://www.youtube.com/` | `class: librewolf`; title: `YouTube` | Shared LibreWolf window; cold-start only |
| Spotify | `spotify` | `class: Spotify` | Native application; supported by live reroute |

## Workspace 2 — Infrastructure

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| Workspace terminal | `/home/pjfernandes/bin/workspace-term 2` | `class: me.creativetech.terminal.workspace2` | Dedicated terminal; supported by live reroute |
| PVE / Portainer | `https://pve.creativetech.me/` | `class: librewolf`; title: `Proxmox Virtual Environment` | Shared LibreWolf window; Portainer opens as a secondary tab; cold-start only |
| PBS / PDM | `https://pbs.creativetech.me/` | `class: librewolf`; title: `Proxmox Backup Server` | Shared LibreWolf window; PDM opens as a secondary tab; cold-start only |
| GitLab | `https://git.creativetech.me/` | `class: librewolf`; title: `GitLab` | Shared LibreWolf window; cold-start only |
| CT Codex / Atlas | `https://codex.creativetech.me/ops/` | `class: librewolf`; title: `Ops \| CT Codex` | Shared LibreWolf window; Atlas opens as a secondary tab; cold-start only |

## Workspace 3 — Observability

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| Workspace terminal | `/home/pjfernandes/bin/workspace-term 3` | `class: me.creativetech.terminal.workspace3` | Dedicated terminal; supported by live reroute |
| Grafana Cloud | `https://creativetech.grafana.net/login/` | `class: librewolf`; title: `Grafana` | Shared LibreWolf window; cold-start only |

The MBTA browser window sometimes used during routing verification is a
temporary placeholder. It is not profile-defined and is not required for WS3.

## Workspace 4 — Home Automation

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| CT Codex Home Assistant documentation | `https://codex.creativetech.me/docker-stacks/docker02/homeassistant/?_highlight=home&_highlight=ass` | `class: librewolf`; title: `Home Assistant \| CT Codex` | Shared LibreWolf window; cold-start only |
| Home Assistant dashboard | `https://ha-tst.creativetech.me/home/overview` | `class: librewolf`; title: `Home Assistant` | Shared LibreWolf window; cold-start only |
| Workspace terminal | `/home/pjfernandes/bin/workspace-term 4` | `class: me.creativetech.terminal.workspace4` | Dedicated terminal; supported by live reroute |
| Perplexity Home Automation project | `https://www.perplexity.ai/projects/ceb715a6-26e6-49e4-af03-97308d473ef3` | `class: librewolf`; title: `Home Automation \| Perplexity` | Shared LibreWolf window; cold-start only |

## Workspace 5 — Development

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| Visual Studio Code | `code` | `class: code` | Native application; supported by live reroute |

WS5 is intentionally Visual Studio Code only.

## Workspace 6 — Communications

| Managed window | Launch target | Matcher | Notes |
|---|---|---|---|
| Slack | `slack` | `class: Slack` | Native application; supported by live reroute |
| Discord | `/usr/bin/discord` | `class: discord` | Native application; supported by live reroute |
| GitKraken Desktop | `gitkraken` | `class: gitkraken`; title: `GitKraken Desktop` | Native application; supported by live reroute |
| Signal | `signal-desktop` | `class: signal` | Native application; supported by live reroute |
| Mattermost Desktop | `/usr/bin/mattermost-desktop` | `class: Mattermost.Desktop` | Native application; supported by live reroute |

## WS7 exclusion

WS7 assistant/control activity is not part of this cold-start inventory or the
approved native live reroute snapshot.

## Validation

Launch one profile at a time when testing a profile definition:

```bash
cosmic-wm start sysadmin-ws4 --timeout 150
```

Inspect the result:

```bash
cosmic-wm status
```

A cold-start validation pass requires each declared application in the tested
profile to appear in its configured workspace. Browser page titles and active
tabs can change after launch because managed browser windows share the normal
LibreWolf session.

For native reroute validation, use the dedicated
[validation procedure](../operations/validation.md) instead.
