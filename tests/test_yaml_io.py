from pathlib import Path

import pytest

from cosmic_workspace_steward.errors import YamlArtifactError
from cosmic_workspace_steward.yaml_io import load_yaml_mapping


def test_loads_yaml_mapping(tmp_path: Path) -> None:
    path = tmp_path / "profile.yaml"
    path.write_text("version: 1\nkind: profile\nname: example\n", encoding="utf-8")

    assert load_yaml_mapping(path) == {
        "version": 1,
        "kind": "profile",
        "name": "example",
    }


@pytest.mark.parametrize(
    ("contents", "message"),
    [
        ("", "artifact is empty"),
        ("- one\n- two\n", "artifact root must be a YAML mapping"),
        ("example", "artifact root must be a YAML mapping"),
        ("value: [unterminated\n", "invalid or unsafe YAML"),
        ("value: !!python/object/apply:os.system ['echo unsafe']\n", "invalid or unsafe YAML"),
    ],
)
def test_rejects_invalid_or_non_mapping_yaml(
    tmp_path: Path,
    contents: str,
    message: str,
) -> None:
    path = tmp_path / "artifact.yaml"
    path.write_text(contents, encoding="utf-8")

    with pytest.raises(YamlArtifactError, match=message):
        load_yaml_mapping(path)


def test_rejects_missing_or_non_regular_path(tmp_path: Path) -> None:
    missing = tmp_path / "missing.yaml"

    with pytest.raises(YamlArtifactError, match="existing regular file"):
        load_yaml_mapping(missing)

    directory = tmp_path / "directory.yaml"
    directory.mkdir()

    with pytest.raises(YamlArtifactError, match="existing regular file"):
        load_yaml_mapping(directory)


def test_creates_yaml_mapping_exclusively(tmp_path: Path) -> None:
    from cosmic_workspace_steward.yaml_io import create_yaml_mapping_exclusively

    path = tmp_path / "layouts" / "sysadmin.yaml"

    created = create_yaml_mapping_exclusively(
        path,
        {
            "kind": "layout",
            "name": "sysadmin",
            "version": 1,
            "workspace_count": 6,
        },
    )

    assert created is True
    assert load_yaml_mapping(path) == {
        "kind": "layout",
        "name": "sysadmin",
        "version": 1,
        "workspace_count": 6,
    }


def test_exclusive_yaml_mapping_creation_preserves_existing_content(
    tmp_path: Path,
) -> None:
    from cosmic_workspace_steward.yaml_io import create_yaml_mapping_exclusively

    path = tmp_path / "sysadmin.yaml"
    original = "kind: layout\nname: sysadmin\nversion: 1\nworkspace_count: 4\n"
    path.write_text(original, encoding="utf-8")

    created = create_yaml_mapping_exclusively(
        path,
        {
            "kind": "layout",
            "name": "sysadmin",
            "version": 1,
            "workspace_count": 6,
        },
    )

    assert created is False
    assert path.read_text(encoding="utf-8") == original
