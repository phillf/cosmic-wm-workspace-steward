from __future__ import annotations

from io import StringIO
from pathlib import Path

from cosmic_workspace_steward.cli import main


def write_artifact(
    root: Path,
    name: str,
    *,
    kind: str,
    extra: str = "",
) -> None:
    root.mkdir(parents=True, exist_ok=True)
    (root / f"{name}.yaml").write_text(
        f"version: 1\nkind: {kind}\nname: {name}\n{extra}",
        encoding="utf-8",
    )


def generic_data_root(home: Path) -> Path:
    return home / ".local" / "share" / "cosmic-workspace-steward"


def run_cli(
    argv: list[str],
    *,
    home: Path,
    environment: dict[str, str] | None = None,
) -> tuple[int, str, str]:
    stdout = StringIO()
    stderr = StringIO()
    exit_code = main(
        argv,
        stdout=stdout,
        stderr=stderr,
        environment={} if environment is None else environment,
        home=home,
    )
    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_profiles_list_is_sorted_and_does_not_read_ct_repository_files(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = generic_data_root(home) / "profiles"
    write_artifact(profiles, "zeta", kind="profile")
    write_artifact(profiles, "alpha", kind="profile")

    exit_code, stdout, stderr = run_cli(["profiles", "list"], home=home)

    assert exit_code == 0
    assert stdout == "alpha\nzeta\n"
    assert stderr == ""
    assert not (home / ".config" / "cosmic-workspace-steward").exists()
    assert not (home / ".local" / "state" / "cosmic-workspace-steward").exists()


def test_sessions_list_reports_invalid_artifacts_without_hiding_valid_entries(tmp_path: Path) -> None:
    home = tmp_path / "home"
    sessions = generic_data_root(home) / "sessions"
    write_artifact(sessions, "valid", kind="session")
    (sessions / "broken.yaml").write_text("not: [valid", encoding="utf-8")

    exit_code, stdout, stderr = run_cli(["sessions", "list"], home=home)

    assert exit_code == 0
    assert stdout == "valid\n"
    assert "warning:" in stderr
    assert "broken.yaml" in stderr
    assert "invalid-artifact" in stderr


def test_show_profile_renders_canonical_validated_document(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = generic_data_root(home) / "profiles"
    write_artifact(
        profiles,
        "daily",
        kind="profile",
        extra="description: Daily workspace\nlaunch_groups:\n  - terminal\n",
    )

    exit_code, stdout, stderr = run_cli(["show", "profile", "daily"], home=home)

    assert exit_code == 0
    assert stderr == ""
    assert stdout == (
        "description: Daily workspace\n"
        "kind: profile\n"
        "launch_groups:\n"
        "- terminal\n"
        "name: daily\n"
        "version: 1\n"
    )


def test_show_session_rejects_unsafe_name_before_discovery(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["show", "session", "../escape"],
        home=tmp_path / "home",
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr == "error: unsafe session name: '../escape'\n"


def test_show_reports_absent_name_after_read_only_discovery(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["show", "profile", "missing"],
        home=tmp_path / "home",
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: profile not found: missing\n"


def test_cli_rejects_invalid_grammar(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["profiles", "show"],
        home=tmp_path / "home",
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr.startswith("usage:\n")


def test_cli_reports_invalid_xdg_override(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["profiles", "list"],
        home=tmp_path / "home",
        environment={"XDG_DATA_HOME": "relative"},
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr == "error: XDG_DATA_HOME must be an absolute path when set\n"


def test_empty_roots_are_successful_read_only_lists(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["profiles", "list"],
        home=tmp_path / "home",
    )

    assert exit_code == 0
    assert stdout == ""
    assert stderr == ""


def test_plan_profile_is_deterministic_and_does_not_probe_native_commands(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = generic_data_root(home) / "profiles"
    write_artifact(
        profiles,
        "daily",
        kind="profile",
        extra=(
            "launch_groups:\n"
            "  - name: core\n"
            "    workspace: 1\n"
            "    applications:\n"
            "      - id: terminal\n"
            "        command: [wezterm]\n"
            "      - id: browser\n"
            "        command: [librewolf, --new-window]\n"
            "  - name: communications\n"
            "    workspace: 2\n"
            "    applications:\n"
            "      - id: slack\n"
            "        command: [slack]\n"
        ),
    )

    exit_code, stdout, stderr = run_cli(["plan", "profile", "daily"], home=home)

    assert exit_code == 0
    assert stderr == ""
    assert stdout == (
        "profile: daily\n"
        "dry_run: true\n"
        "001 unknown prepare-workspace-group core@workspace-1 -- "
        "serial launch group; no workspace mutation is performed\n"
        "002 unknown launch-application core/terminal -- argv=['wezterm']\n"
        "003 unknown launch-application core/browser -- "
        "argv=['librewolf', '--new-window']\n"
        "004 unknown prepare-workspace-group communications@workspace-2 -- "
        "serial launch group; no workspace mutation is performed\n"
        "005 unknown launch-application communications/slack -- argv=['slack']\n"
    )


def test_plan_profile_rejects_invalid_body_without_creating_or_running_anything(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = generic_data_root(home) / "profiles"
    write_artifact(profiles, "broken", kind="profile")

    exit_code, stdout, stderr = run_cli(["plan", "profile", "broken"], home=home)

    assert exit_code == 1
    assert stdout == ""
    assert "launch_groups must be a non-empty list" in stderr


def test_plan_profile_rejects_unsafe_name_before_discovery(tmp_path: Path) -> None:
    exit_code, stdout, stderr = run_cli(
        ["plan", "profile", "../escape"],
        home=tmp_path / "home",
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr == "error: unsafe profile name: '../escape'\n"


def test_start_dry_run_is_an_alias_for_profile_planning(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = generic_data_root(home) / "profiles"
    write_artifact(
        profiles,
        "daily",
        kind="profile",
        extra=(
            "launch_groups:\n"
            "  - name: core\n"
            "    workspace: 1\n"
            "    applications:\n"
            "      - id: terminal\n"
            "        command: [wezterm]\n"
        ),
    )

    plan_exit, plan_stdout, plan_stderr = run_cli(
        ["plan", "profile", "daily"],
        home=home,
    )
    start_exit, start_stdout, start_stderr = run_cli(
        ["start", "daily", "--dry-run"],
        home=home,
    )

    assert start_exit == plan_exit == 0
    assert start_stdout == plan_stdout
    assert start_stderr == plan_stderr == ""
