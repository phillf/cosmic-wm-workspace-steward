from pathlib import Path

import pytest

from cosmic_workspace_steward.artifacts import (
    ARTIFACT_KINDS,
    is_safe_logical_name,
    validate_artifact_envelope,
)
from cosmic_workspace_steward.errors import ArtifactValidationError


@pytest.mark.parametrize("kind", sorted(ARTIFACT_KINDS))
def test_validates_every_supported_artifact_kind(kind: str) -> None:
    if kind == "config":
        document: dict[str, object] = {"version": 1, "kind": kind}
        path = Path("config.yaml")
    else:
        document = {"version": 1, "kind": kind, "name": "example"}
        path = Path("example.yaml")

    artifact = validate_artifact_envelope(document, path)

    assert artifact.version == 1
    assert artifact.kind == kind
    assert artifact.path == path
    assert artifact.document == document


@pytest.mark.parametrize(
    ("document", "message"),
    [
        ({}, "artifact version must be the integer 1"),
        (
            {"version": True, "kind": "profile", "name": "example"},
            "artifact version must be the integer 1",
        ),
        (
            {"version": "1", "kind": "profile", "name": "example"},
            "artifact version must be the integer 1",
        ),
        (
            {"version": 2, "kind": "profile", "name": "example"},
            "unsupported artifact version: 2",
        ),
        (
            {"version": 1, "name": "example"},
            "artifact kind must be a non-empty string",
        ),
        (
            {"version": 1, "kind": "unknown", "name": "example"},
            "unknown artifact kind: unknown",
        ),
    ],
)
def test_rejects_invalid_version_or_kind(
    document: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ArtifactValidationError, match=message):
        validate_artifact_envelope(document, Path("example.yaml"))


@pytest.mark.parametrize(
    "name",
    [
        "",
        ".",
        "..",
        "../example",
        "example/name",
        "example.yaml",
        "example name",
        "Example",
        "-example",
        "example_1",
    ],
)
def test_rejects_unsafe_named_artifact_names(name: str) -> None:
    with pytest.raises(
        ArtifactValidationError,
        match=r"artifact name must match",
    ):
        validate_artifact_envelope(
            {"version": 1, "kind": "profile", "name": name},
            Path("example.yaml"),
        )


@pytest.mark.parametrize(
    "name",
    [
        "a",
        "example",
        "sysadmin-ws1",
        "import-draft-2026-09-25",
    ],
)
def test_accepts_safe_logical_names(name: str) -> None:
    assert is_safe_logical_name(name)


def test_rejects_filename_name_mismatch() -> None:
    with pytest.raises(ArtifactValidationError, match="does not match name"):
        validate_artifact_envelope(
            {"version": 1, "kind": "profile", "name": "other"},
            Path("example.yaml"),
        )


def test_rejects_named_non_yaml_filename() -> None:
    with pytest.raises(ArtifactValidationError, match=r"end in \.yaml or \.yml"):
        validate_artifact_envelope(
            {"version": 1, "kind": "profile", "name": "example"},
            Path("example.json"),
        )


def test_allows_yaml_and_yml_extensions() -> None:
    document = {"version": 1, "kind": "session", "name": "example"}

    assert validate_artifact_envelope(document, Path("example.yaml")).name == "example"
    assert validate_artifact_envelope(document, Path("example.yml")).name == "example"


def test_validates_expected_kind_without_discovery() -> None:
    document = {"version": 1, "kind": "profile", "name": "example"}

    artifact = validate_artifact_envelope(
        document,
        Path("example.yaml"),
        expected_kind="profile",
    )
    assert artifact.kind == "profile"

    with pytest.raises(ArtifactValidationError, match="does not match expected kind"):
        validate_artifact_envelope(
            document,
            Path("example.yaml"),
            expected_kind="session",
        )
