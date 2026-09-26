# Terminal Font Assessment

## Purpose

Terminal font settings are user-owned preferences. COSMIC Workspace Steward does
not impose a shared default font size and does not modify terminal font settings
during `ws-man start`, profile synchronization, cold start, or native live
reroute.

The terminal-font commands provide a read-only inventory and assessment layer
for future explicit, target-aware font configuration.

## Commands

Inspect known terminal targets without changing terminal configuration:

    ws-man terminal-font status

Validate a requested point size and inspect one target without changing terminal
configuration:

    ws-man terminal-font plan --size 14 --target wezterm

Assess every known target without changing terminal configuration:

    ws-man terminal-font plan --size 14 --all

`--size` accepts a positive integer or decimal point size. `plan` validates
that value, reports the target state, and ends with:

    apply_status=deferred; no configuration was changed

This means no persistent configuration writer is implemented. The command does
not create, edit, move, or delete terminal configuration files.

## Known targets

| Target | Discovery scope | Apply status |
|---|---|---|
| `wezterm` | Executable plus `~/.wezterm.lua` or XDG Lua config | Deferred; Lua configuration review required |
| `alacritty` | Executable plus XDG `alacritty.toml` | Deferred; TOML `[font].size` review required |
| `cosmic-term` | Executable plus COSMIC Terminal `font_size` preference | Deferred; COSMIC preference lifecycle review required |
| `konsole` | Executable plus XDG `konsolerc` | Deferred; KDE profile discovery required |
| `xterm` | Executable plus `~/.Xresources` or `~/.Xdefaults` | Deferred; X resource review required |
| `xfce4-terminal` | Executable plus XDG `xfce4/terminal/terminalrc` | Deferred; Xfce terminalrc review required |

A target can be listed even when its executable is absent. In that case,
`installed=no` is reported and no configuration is changed.

## Safety boundary

The assessment commands are intentionally read-only:

- They do not change WezTerm Lua configuration.
- They do not change Alacritty TOML configuration.
- They do not change COSMIC Terminal preferences.
- They do not change Konsole profiles.
- They do not create or modify XTerm resource files.
- They do not create or modify Xfce Terminal configuration.
- They do not launch terminal applications.
- They do not invoke `cosmic-wm`.
- They do not alter cold-start or live-reroute behavior.

Future persistent font changes require a separately reviewed implementation with
a target-specific write strategy, backup behavior, explicit operator approval,
and validation of the target terminal's configuration format.
