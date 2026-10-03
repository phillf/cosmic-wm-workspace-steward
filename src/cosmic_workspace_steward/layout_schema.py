"""Validation for inert workspace layout artifacts."""
from __future__ import annotations

from dataclasses import dataclass

from .artifacts import ValidatedArtifact
from .errors import ArtifactValidationError


@dataclass(frozen=True)
class LayoutDefinition:
    """A validated inert layout definition."""

    name: str
    workspace_count: int


def validate_layout_definition(artifact: ValidatedArtifact) -> LayoutDefinition:
    """Validate the body of a generic layout artifact."""
    document = artifact.document
    workspace_count = document.get("workspace_count")

    if (
        isinstance(workspace_count, bool)
        or not isinstance(workspace_count, int)
        or workspace_count < 1
    ):
        raise ArtifactValidationError(
            artifact.path,
            "workspace_count must be a positive integer",
        )

    if artifact.name is None:
        raise ArtifactValidationError(
            artifact.path,
            "layout artifact must have a logical name",
        )

    return LayoutDefinition(
        name=artifact.name,
        workspace_count=workspace_count,
    )
