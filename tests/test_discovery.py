from pathlib import Path

import pytest

from cosmic_workspace_steward.discovery import DiscoveryResult, discover_artifacts


def write_artifact(
    root: Path,
    filename: str,
    *,
    kind: str = "profile",
    name: str | None = None,
    extra: str = "",
) -> Path:
    artifact_name = name if name is not None else Path(filename).stem
    path = root / filename
    path.write_text(
        f"version: 1\nkind: {kind}\nname: {artifact_name}\n{extra}",
        encoding="utf-8",
    )
    return path


def diagnostic_codes(result: DiscoveryResult) -> list[str]:
    return [diagnostic.code for diagnostic in result.diagnostics]


def test_missing_root_is_an_empty_read_only_result(tmp_path: Path) -> None:
    root = tmp_path / "missing"

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert result.diagnostics == ()
    assert not root.exists()


def test_empty_root_is_an_empty_result(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert result.diagnostics == ()


def test_discovers_yaml_artifacts_in_name_order(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    write_artifact(root, "zeta.yaml")
    write_artifact(root, "alpha.yml")
    (root / "ignored.json").write_text("{}", encoding="utf-8")
    (root / "notes.txt").write_text("ignored", encoding="utf-8")

    result = discover_artifacts(root, "profile")

    assert [artifact.name for artifact in result.artifacts] == ["alpha", "zeta"]
    assert [artifact.path.name for artifact in result.artifacts] == [
        "alpha.yml",
        "zeta.yaml",
    ]
    assert result.diagnostics == ()


def test_invalid_artifact_does_not_hide_valid_sibling(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    write_artifact(root, "valid.yaml")
    (root / "invalid.yaml").write_text("value: [unterminated\n", encoding="utf-8")

    result = discover_artifacts(root, "profile")

    assert [artifact.name for artifact in result.artifacts] == ["valid"]
    assert diagnostic_codes(result) == ["invalid-artifact"]
    assert result.diagnostics[0].path.name == "invalid.yaml"


@pytest.mark.parametrize(
    ("filename", "contents"),
    [
        ("empty.yaml", ""),
        ("list.yaml", "- one\n- two\n"),
        ("wrong-kind.yaml", "version: 1\nkind: session\nname: wrong-kind\n"),
        ("mismatch.yaml", "version: 1\nkind: profile\nname: other\n"),
    ],
)
def test_invalid_candidates_are_reported_and_excluded(
    tmp_path: Path,
    filename: str,
    contents: str,
) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    (root / filename).write_text(contents, encoding="utf-8")

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["invalid-artifact"]
    assert result.diagnostics[0].path.name == filename


def test_root_that_is_not_a_directory_is_reported(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.write_text("not a directory", encoding="utf-8")

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["root-not-directory"]


def test_directory_candidate_is_reported(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    (root / "directory.yaml").mkdir()

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["not-regular-file"]


def test_contained_symlink_is_allowed(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    nested = root / "nested"
    nested.mkdir(parents=True)
    target = nested / "linked.yaml"
    target.write_text(
        "version: 1\nkind: profile\nname: linked\n",
        encoding="utf-8",
    )
    (root / "linked.yaml").symlink_to("nested/linked.yaml")

    result = discover_artifacts(root, "profile")

    assert [artifact.name for artifact in result.artifacts] == ["linked"]
    assert [artifact.path.name for artifact in result.artifacts] == ["linked.yaml"]
    assert result.diagnostics == ()


def test_symlink_escape_is_rejected_without_reading_target(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    outside = tmp_path / "outside.yaml"
    root.mkdir()
    outside.write_text(
        "version: 1\nkind: profile\nname: outside\n",
        encoding="utf-8",
    )
    (root / "escape.yaml").symlink_to(outside)

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["path-escape"]


def test_dangling_symlink_is_reported(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    (root / "missing.yaml").symlink_to("does-not-exist.yaml")

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["unresolvable-path"]


def test_duplicate_extensions_are_reported_and_excluded(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    write_artifact(root, "example.yaml")
    write_artifact(root, "example.yml")

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["duplicate-name", "duplicate-name"]
    assert [diagnostic.path.name for diagnostic in result.diagnostics] == [
        "example.yaml",
        "example.yml",
    ]


def test_filename_name_mismatches_are_reported_and_excluded(
    tmp_path: Path,
) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    write_artifact(root, "first.yaml", name="shared")
    write_artifact(root, "second.yaml", name="shared")

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert diagnostic_codes(result) == ["invalid-artifact", "invalid-artifact"]
    assert [diagnostic.path.name for diagnostic in result.diagnostics] == [
        "first.yaml",
        "second.yaml",
    ]


def test_artifacts_and_diagnostics_are_deterministic(tmp_path: Path) -> None:
    root = tmp_path / "profiles"
    root.mkdir()
    write_artifact(root, "zeta.yaml")
    write_artifact(root, "alpha.yaml")
    (root / "bad.yaml").write_text("version: 2\nkind: profile\nname: bad\n", encoding="utf-8")
    (root / "empty.yaml").write_text("", encoding="utf-8")

    result = discover_artifacts(root, "profile")

    assert [artifact.name for artifact in result.artifacts] == ["alpha", "zeta"]
    assert [diagnostic.path.name for diagnostic in result.diagnostics] == [
        "bad.yaml",
        "empty.yaml",
    ]
