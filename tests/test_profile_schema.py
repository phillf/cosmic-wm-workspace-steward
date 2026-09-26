from __future__ import annotations

from pathlib import Path

import pytest

from cosmic_workspace_steward.artifacts import validate_artifact_envelope
from cosmic_workspace_steward.errors import ArtifactValidationError
from cosmic_workspace_steward.profile_schema import validate_profile_definition


def profile_artifact(document: dict[str, object]):
    return validate_artifact_envelope(document, Path("daily.yaml"), expected_kind="profile")


def valid_document() -> dict[str, object]:
    return {
        "version": 1,
        "kind": "profile",
        "name": "daily",
        "description": "Daily operations",
        "launch_groups": [
            {
                "name": "core",
                "workspace": 1,
                "applications": [
                    {"id": "terminal", "command": ["wezterm"]},
                    {"id": "browser", "command": ["librewolf", "--new-window"]},
                ],
            },
            {
                "name": "communications",
                "workspace": 2,
                "applications": [{"id": "slack", "command": ["slack"]}],
            },
        ],
    }


def test_validates_profile_definition_and_preserves_declared_order() -> None:
    profile = validate_profile_definition(profile_artifact(valid_document()))

    assert profile.name == "daily"
    assert profile.description == "Daily operations"
    assert [group.name for group in profile.launch_groups] == ["core", "communications"]
    assert profile.launch_groups[0].workspace == 1
    assert [app.identifier for app in profile.launch_groups[0].applications] == [
        "terminal",
        "browser",
    ]
    assert profile.launch_groups[0].applications[1].command == (
        "librewolf",
        "--new-window",
    )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (
            lambda document: document.pop("launch_groups"),
            "launch_groups must be a non-empty list",
        ),
        (
            lambda document: document.__setitem__("launch_groups", []),
            "launch_groups must be a non-empty list",
        ),
        (
            lambda document: document["launch_groups"][0].__setitem__("name", "Core"),
            "launch_groups\\[0\\].name must match",
        ),
        (
            lambda document: document["launch_groups"][0].__setitem__("workspace", 0),
            "workspace must be a positive integer",
        ),
        (
            lambda document: document["launch_groups"][0].__setitem__("workspace", True),
            "workspace must be a positive integer",
        ),
        (
            lambda document: document["launch_groups"][0].__setitem__("applications", []),
            "applications must be a non-empty list",
        ),
        (
            lambda document: document["launch_groups"][0]["applications"][0].__setitem__(
                "id", "../terminal"
            ),
            "id must match",
        ),
        (
            lambda document: document["launch_groups"][0]["applications"][0].__setitem__(
                "command", "wezterm"
            ),
            "command must be a non-empty list",
        ),
        (
            lambda document: document["launch_groups"][0]["applications"][0].__setitem__(
                "command", ["wezterm", ""]
            ),
            "command\\[1\\] must be a non-empty string",
        ),
    ],
)
def test_rejects_invalid_profile_body(
    mutate,
    message: str,
) -> None:
    document = valid_document()
    mutate(document)

    with pytest.raises(ArtifactValidationError, match=message):
        validate_profile_definition(profile_artifact(document))


def test_rejects_duplicate_group_names() -> None:
    document = valid_document()
    document["launch_groups"].append(
        {
            "name": "core",
            "workspace": 3,
            "applications": [{"id": "editor", "command": ["code"]}],
        }
    )

    with pytest.raises(ArtifactValidationError, match="duplicate launch group name: core"):
        validate_profile_definition(profile_artifact(document))


def test_rejects_duplicate_application_identifiers_within_group() -> None:
    document = valid_document()
    document["launch_groups"][0]["applications"].append(
        {"id": "terminal", "command": ["foot"]}
    )

    with pytest.raises(
        ArtifactValidationError,
        match="duplicate application id in launch group core: terminal",
    ):
        validate_profile_definition(profile_artifact(document))
