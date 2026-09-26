"""Domain errors for generic Workspace Steward artifact handling."""

from __future__ import annotations

from pathlib import Path


class ArtifactError(ValueError):
    """Base error for a generic Workspace Steward artifact."""


class YamlArtifactError(ArtifactError):
    """Raised when a YAML artifact cannot be safely loaded."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        super().__init__(f"{path}: {message}")


class ArtifactValidationError(ArtifactError):
    """Raised when a generic artifact violates the version-1 contract."""

    def __init__(self, path: Path, message: str) -> None:
        self.path = path
        super().__init__(f"{path}: {message}")
