from __future__ import annotations

from io import StringIO
from pathlib import Path

import yaml

from cosmic_workspace_steward.cli import main


def data_root(home: Path) -> Path:
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


def test_layout_create_dry_run_is_non_mutating(tmp_path: Path) -> None:
    home = tmp_path / "home"

    exit_code, stdout, stderr = run_cli(
        ["layouts", "create", "sysadmin", "6", "--dry-run"],
        home=home,
    )

    assert exit_code == 0
    assert stderr == ""
    assert stdout == (
        "action: create\n"
        "dry_run: true\n"
        "kind: layout\n"
        "name: sysadmin\n"
        "workspace_count: 6\n"
    )
    assert not data_root(home).exists()


def test_layout_create_requires_explicit_confirmation(tmp_path: Path) -> None:
    home = tmp_path / "home"

    exit_code, stdout, stderr = run_cli(
        ["layouts", "create", "sysadmin", "6"],
        home=home,
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr == (
        "error: layout creation changes XDG data; "
        "rerun with --dry-run or --yes\n"
    )
    assert not data_root(home).exists()


def test_layout_create_writes_valid_canonical_artifact(tmp_path: Path) -> None:
    home = tmp_path / "home"

    exit_code, stdout, stderr = run_cli(
        ["layouts", "create", "sysadmin", "6", "--yes"],
        home=home,
    )

    path = data_root(home) / "layouts" / "sysadmin.yaml"
    assert exit_code == 0
    assert stdout == "created layout: sysadmin\n"
    assert stderr == ""
    assert yaml.safe_load(path.read_text(encoding="utf-8")) == {
        "kind": "layout",
        "name": "sysadmin",
        "version": 1,
        "workspace_count": 6,
    }


def test_layout_create_refuses_to_overwrite_existing_artifact(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"
    path = data_root(home) / "layouts" / "sysadmin.yaml"
    path.parent.mkdir(parents=True)
    original = (
        "kind: layout\n"
        "name: sysadmin\n"
        "version: 1\n"
        "workspace_count: 4\n"
    )
    path.write_text(original, encoding="utf-8")

    exit_code, stdout, stderr = run_cli(
        ["layouts", "create", "sysadmin", "6", "--yes"],
        home=home,
    )

    assert exit_code == 1
    assert stdout == ""
    assert stderr == "error: layout already exists: sysadmin\n"
    assert path.read_text(encoding="utf-8") == original


def test_layout_create_rejects_unsafe_name_without_mutation(tmp_path: Path) -> None:
    home = tmp_path / "home"

    exit_code, stdout, stderr = run_cli(
        ["layouts", "create", "../escape", "6", "--dry-run"],
        home=home,
    )

    assert exit_code == 2
    assert stdout == ""
    assert stderr == "error: unsafe layout name: '../escape'\n"
    assert not data_root(home).exists()


def test_layout_create_rejects_invalid_workspace_count_without_mutation(
    tmp_path: Path,
) -> None:
    home = tmp_path / "home"

    for value in ("0", "-1", "many", "6.0"):
        exit_code, stdout, stderr = run_cli(
            ["layouts", "create", "sysadmin", value, "--dry-run"],
            home=home,
        )

        assert exit_code == 2
        assert stdout == ""
        assert stderr == (
            "error: workspace_count must be a positive integer\n"
        )

    assert not data_root(home).exists()


def test_layouts_list_is_sorted_and_read_only(tmp_path: Path) -> None:
    home = tmp_path / "home"
    layouts = data_root(home) / "layouts"
    layouts.mkdir(parents=True)

    (layouts / "zeta.yaml").write_text(
        "kind: layout\nname: zeta\nversion: 1\nworkspace_count: 2\n",
        encoding="utf-8",
    )
    (layouts / "alpha.yaml").write_text(
        "kind: layout\nname: alpha\nversion: 1\nworkspace_count: 4\n",
        encoding="utf-8",
    )

    exit_code, stdout, stderr = run_cli(
        ["layouts", "list"],
        home=home,
    )

    assert exit_code == 0
    assert stdout == "alpha\nzeta\n"
    assert stderr == ""


def test_layouts_show_renders_canonical_document(tmp_path: Path) -> None:
    home = tmp_path / "home"
    layouts = data_root(home) / "layouts"
    layouts.mkdir(parents=True)

    (layouts / "sysadmin.yaml").write_text(
        "workspace_count: 6\nkind: layout\nversion: 1\nname: sysadmin\n",
        encoding="utf-8",
    )

    exit_code, stdout, stderr = run_cli(
        ["layouts", "show", "sysadmin"],
        home=home,
    )

    assert exit_code == 0
    assert stderr == ""
    assert stdout == (
        "kind: layout\n"
        "name: sysadmin\n"
        "version: 1\n"
        "workspace_count: 6\n"
    )
