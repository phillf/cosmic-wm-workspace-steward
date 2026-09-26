"""Validation for version-1 generic profile bodies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from .artifacts import ValidatedArtifact, is_safe_logical_name
from .errors import ArtifactValidationError


@dataclass(frozen=True)
class PlannedApplication:
    """One declarative application launch intent within a serial group."""

    identifier: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class LaunchGroup:
    """One serial workspace-level launch group."""

    name: str
    workspace: int
    applications: tuple[PlannedApplication, ...]


@dataclass(frozen=True)
class ProfileDefinition:
    """Validated version-1 generic profile planning input."""

    name: str
    description: str | None
    launch_groups: tuple[LaunchGroup, ...]


def _error(artifact: ValidatedArtifact, message: str) -> ArtifactValidationError:
    return ArtifactValidationError(artifact.path, message)


def _mapping(value: object, artifact: ValidatedArtifact, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise _error(artifact, f"{label} must be a mapping")
    return value


def _non_empty_string(value: object, artifact: ValidatedArtifact, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise _error(artifact, f"{label} must be a non-empty string")
    return value


def _safe_name(value: object, artifact: ValidatedArtifact, label: str) -> str:
    if not is_safe_logical_name(value):
        raise _error(
            artifact,
            f"{label} must match ^[a-z0-9][a-z0-9-]*$",
        )
    return str(value)


def _positive_workspace(value: object, artifact: ValidatedArtifact, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise _error(artifact, f"{label} must be a positive integer")
    return value


def _command(value: object, artifact: ValidatedArtifact, label: str) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence) or not value:
        raise _error(artifact, f"{label} must be a non-empty list of non-empty strings")

    command: list[str] = []
    for index, argument in enumerate(value):
        command.append(_non_empty_string(argument, artifact, f"{label}[{index}]"))
    return tuple(command)


def validate_profile_definition(artifact: ValidatedArtifact) -> ProfileDefinition:
    """Validate the generic profile body without executing or writing anything."""
    if artifact.kind != "profile" or artifact.name is None:
        raise _error(artifact, "profile definition requires a named profile artifact")

    document = artifact.document
    description_value = document.get("description")
    if description_value is not None and not isinstance(description_value, str):
        raise _error(artifact, "description must be a string when present")

    groups_value = document.get("launch_groups")
    if isinstance(groups_value, (str, bytes)) or not isinstance(groups_value, Sequence) or not groups_value:
        raise _error(artifact, "launch_groups must be a non-empty list")

    group_names: set[str] = set()
    launch_groups: list[LaunchGroup] = []

    for group_index, group_value in enumerate(groups_value):
        group = _mapping(group_value, artifact, f"launch_groups[{group_index}]")
        name = _safe_name(group.get("name"), artifact, f"launch_groups[{group_index}].name")
        if name in group_names:
            raise _error(artifact, f"duplicate launch group name: {name}")
        group_names.add(name)

        workspace = _positive_workspace(
            group.get("workspace"),
            artifact,
            f"launch_groups[{group_index}].workspace",
        )

        applications_value = group.get("applications")
        if (
            isinstance(applications_value, (str, bytes))
            or not isinstance(applications_value, Sequence)
            or not applications_value
        ):
            raise _error(
                artifact,
                f"launch_groups[{group_index}].applications must be a non-empty list",
            )

        application_ids: set[str] = set()
        applications: list[PlannedApplication] = []
        for application_index, application_value in enumerate(applications_value):
            application = _mapping(
                application_value,
                artifact,
                f"launch_groups[{group_index}].applications[{application_index}]",
            )
            identifier = _safe_name(
                application.get("id"),
                artifact,
                f"launch_groups[{group_index}].applications[{application_index}].id",
            )
            if identifier in application_ids:
                raise _error(
                    artifact,
                    f"duplicate application id in launch group {name}: {identifier}",
                )
            application_ids.add(identifier)
            command = _command(
                application.get("command"),
                artifact,
                f"launch_groups[{group_index}].applications[{application_index}].command",
            )
            applications.append(PlannedApplication(identifier=identifier, command=command))

        launch_groups.append(
            LaunchGroup(
                name=name,
                workspace=workspace,
                applications=tuple(applications),
            )
        )

    return ProfileDefinition(
        name=artifact.name,
        description=description_value,
        launch_groups=tuple(launch_groups),
    )
