"""Generic, non-mutating core for COSMIC Workspace Steward."""

from .artifacts import (
    ARTIFACT_KINDS,
    SUPPORTED_VERSION,
    ValidatedArtifact,
    is_safe_logical_name,
    validate_artifact_envelope,
)
from .xdg import ArtifactRoots, resolve_artifact_roots
from .yaml_io import load_yaml_mapping

__all__ = [
    "ARTIFACT_KINDS",
    "ArtifactRoots",
    "SUPPORTED_VERSION",
    "ValidatedArtifact",
    "is_safe_logical_name",
    "load_yaml_mapping",
    "resolve_artifact_roots",
    "validate_artifact_envelope",
]
