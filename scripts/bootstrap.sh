#!/usr/bin/env bash
set -Eeuo pipefail
IFS=$'\n\t'

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)"

config_home="${XDG_CONFIG_HOME:-$HOME/.config}"
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
state_home="${XDG_STATE_HOME:-$HOME/.local/state}"

wm_dir="$config_home/cosmic-wm-manager"
profile_dir="$wm_dir/profiles"
session_dir="$wm_dir/sessions"
legacy_session_dir="$session_dir/legacy-disabled"

local_bin_dir="$HOME/.local/bin"
user_bin_dir="$HOME/bin"
applications_dir="$data_home/applications"
autostart_dir="$config_home/autostart"

approved_snapshot_source="$repo_dir/sessions/sysadmin-managed-reroute-v1-ws1-ws6-no-stale-ws1-browser-2026-08-24.yaml"
approved_snapshot_name="sysadmin-live-reroute.yaml"
backup_dir="$state_home/cosmic-wm-workspace-manager/bootstrap-backups/$(date +%Y%m%d-%H%M%S)"

dry_run=0
force=0
install_autostart=0

usage() {
  cat <<'USAGE'
Usage:
  bootstrap.sh [--dry-run] [--force] [--install-autostart]

Install this repository's active COSMIC workspace-manager assets as symlinks.

Options:
  --dry-run            Print intended actions without changing files.
  --force              Back up conflicting files/symlinks, then replace them.
  --install-autostart  Also install the repository autostart desktop entry.
                       Default: do not modify autostart.
  -h, --help           Show this help.

Behavior:
  - Links sysadmin-ws1.yaml through sysadmin-ws6.yaml into the live profile dir.
  - Links the declared WS3 terminal and browser scoped cold-start profiles.
  - Links only the approved 17-window reroute snapshot as sysadmin-live-reroute.
  - Quarantines known unsafe/obsolete live snapshots when --force is supplied.
  - Links active launch scripts and desktop entries.
  - Does not touch the disabled cosmic-wm-manager autostart entry.
USAGE
}

while (($#)); do
  case "$1" in
    --dry-run) dry_run=1 ;;
    --force) force=1 ;;
    --install-autostart) install_autostart=1 ;;
    -h|--help) usage; exit 0 ;;
    *) printf 'Unknown option: %s\n' "$1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

run() {
  if ((dry_run)); then
    printf '[dry-run]'
    printf ' %q' "$@"
    printf '\n'
  else
    "$@"
  fi
}

ensure_dir() {
  run mkdir -p -- "$1"
}

backup_path() {
  local destination="$1"
  local relative="${destination#$HOME/}"
  local backup="$backup_dir/$relative"

  if ((dry_run)); then
    printf '[dry-run] backup %q -> %q\n' "$destination" "$backup"
    return 0
  fi

  mkdir -p -- "$(dirname -- "$backup")"
  cp -a -- "$destination" "$backup"
  printf '[backup] %s -> %s\n' "$destination" "$backup"
}

same_target() {
  local left="$1"
  local right="$2"

  [[ -L "$left" ]] || return 1
  [[ "$(readlink -f -- "$left")" == "$(readlink -f -- "$right")" ]]
}

link_file() {
  local source="$1"
  local destination="$2"

  [[ -f "$source" ]] || {
    printf 'ERROR: Missing repository source: %s\n' "$source" >&2
    exit 1
  }

  if same_target "$destination" "$source"; then
    printf '[ok] %s -> %s\n' "$destination" "$source"
    return 0
  fi

  if [[ -e "$destination" || -L "$destination" ]]; then
    if (( ! force )); then
      printf 'ERROR: Destination already exists: %s\n' "$destination" >&2
      printf '       Re-run with --force to back it up and replace it.\n' >&2
      exit 1
    fi

    backup_path "$destination"
    run rm -rf -- "$destination"
  fi

  ensure_dir "$(dirname -- "$destination")"
  run ln -s -- "$source" "$destination"
  printf '[link] %s -> %s\n' "$destination" "$source"
}

quarantine_snapshot() {
  local filename="$1"
  local source="$session_dir/$filename"
  local destination="$legacy_session_dir/$filename.disabled"

  [[ -e "$source" || -L "$source" ]] || return 0

  if (( ! force )); then
    printf '[notice] Existing legacy snapshot left unchanged: %s\n' "$source"
    printf '         Re-run with --force to move it to: %s\n' "$destination"
    return 0
  fi

  ensure_dir "$legacy_session_dir"

  if [[ -e "$destination" || -L "$destination" ]]; then
    backup_path "$destination"
    run rm -rf -- "$destination"
  fi

  run mv -- "$source" "$destination"
  printf '[quarantined] %s -> %s\n' "$source" "$destination"
}

[[ -f "$approved_snapshot_source" ]] || {
  printf 'ERROR: Approved snapshot is missing: %s\n' "$approved_snapshot_source" >&2
  exit 1
}

ensure_dir "$profile_dir"
ensure_dir "$session_dir"
ensure_dir "$local_bin_dir"
ensure_dir "$user_bin_dir"
ensure_dir "$applications_dir"

for workspace in 1 2 3 4 5 6; do
  link_file \
    "$repo_dir/profiles/sysadmin/sysadmin-ws${workspace}.yaml" \
    "$profile_dir/sysadmin-ws${workspace}.yaml"
done

link_file \
  "$repo_dir/profiles/sysadmin/sysadmin-ws3-terminals.yaml" \
  "$profile_dir/sysadmin-ws3-terminals.yaml"

link_file \
  "$repo_dir/profiles/sysadmin/sysadmin-ws3-browsers.yaml" \
  "$profile_dir/sysadmin-ws3-browsers.yaml"

link_file \
  "$approved_snapshot_source" \
  "$session_dir/$approved_snapshot_name"

link_file \
  "$repo_dir/scripts/local-bin/start-sysadmin-cold" \
  "$local_bin_dir/start-sysadmin-cold"

link_file \
  "$repo_dir/scripts/bin/workspace-term" \
  "$user_bin_dir/workspace-term"

link_file \
  "$repo_dir/scripts/bin/workspace-profile" \
  "$user_bin_dir/workspace-profile"

link_file \
  "$repo_dir/scripts/bin/open-workspace-terminal" \
  "$user_bin_dir/open-workspace-terminal"

link_file \
  "$repo_dir/scripts/bin/launch-workspace-profile" \
  "$user_bin_dir/launch-workspace-profile"

link_file \
  "$repo_dir/scripts/bin/ws-man" \
  "$user_bin_dir/ws-man"

link_file \
  "$repo_dir/scripts/desktop/sysadmin-cold-start.desktop" \
  "$applications_dir/sysadmin-cold-start.desktop"

link_file \
  "$repo_dir/scripts/desktop/ct-workspace-profile.desktop" \
  "$applications_dir/ct-workspace-profile.desktop"

if ((install_autostart)); then
  link_file \
    "$repo_dir/scripts/autostart/start-sysadmin.desktop" \
    "$autostart_dir/start-sysadmin.desktop"
else
  printf '%s\n' '[skip] Autostart unchanged; use --install-autostart to opt in.'
fi

quarantine_snapshot "sysadmin-managed-reroute-v1-ws1-ws6-only-2026-08-24.yaml"
quarantine_snapshot "sysadmin-managed-reroute-v1-2026-08-24.yaml"

if (( ! dry_run )); then
  chmod 0755 \
    "$repo_dir/scripts/bootstrap.sh" \
    "$repo_dir/scripts/local-bin/start-sysadmin-cold" \
    "$repo_dir/scripts/bin/workspace-term" \
    "$repo_dir/scripts/bin/workspace-profile" \
    "$repo_dir/scripts/bin/open-workspace-terminal" \
    "$repo_dir/scripts/bin/launch-workspace-profile" \
    "$repo_dir/scripts/bin/ws-man"
fi

cat <<EOF2

Bootstrap complete.

Repository:
  $repo_dir

Approved live-reroute snapshot:
  $session_dir/$approved_snapshot_name

Use only:
  cosmic-wm restore --timeout 30 --debug sysadmin-live-reroute

Backups, if any:
  $backup_dir

Notes:
  - The approved snapshot routes already-open windows to WS1–WS6.
  - It does not restore tile ordering, window geometry, sizes, or split ratios.
  - WS7 remains excluded by the approved snapshot.
  - Autostart is unchanged unless --install-autostart was supplied.
EOF2
