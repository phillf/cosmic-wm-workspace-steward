"""Generic YAML artifact-envelope validation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any, Mapping

from .errors import ArtifactValidationError

SUPPORTED_VERSION = 1

ARTIFACT_KINDS = frozenset(
    {
        "config",
        "profile",
        "session",
        "template",
        "import-draft",
        "layout",
        "backup-manifest",
        "migration-map",
    }
)

NAMED_ARTIFACT_KINDS = frozenset(ARTIFACT_KINDS - {"config"})

_LOGICAL_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


@dataclass(frozen=True)
class ValidatedArtifact:
    """A validated version-1 generic YAML artifact envelope."""

    path: Path
    version: int
    kind: str
    name: str | None
    document: Mapping[str, Any]


def is_safe_logical_name(value: object) -> bool:
    """Return whether value is a permitted generic artifact logical name."""

    return isinstance(value, str) and bool(_LOGICAL_NAME_PATTERN.fullmatch(value))


def validate_artifact_envelope(
    document: Mapping[str, Any],
    path: Path,
    *,
    expected_kind: str | None = None,
) -> ValidatedArtifact:
    """Validate a version-1 generic YAML artifact envelope without mutation."""

    artifact_path = Path(path)

    version = document.get("version")
    if isinstance(version, bool) or not isinstance(version, int):
        raise ArtifactValidationError(
            artifact_path,
            "artifact version must be the integer 1",
        )
    if version != SUPPORTED_VERSION:
        raise ArtifactValidationError(
            artifact_path,
            f"unsupported artifact version: {version}; supported version: 1",
        )

    kind = document.get("kind")
    if not isinstance(kind, str) or not kind:
        raise ArtifactValidationError(
            artifact_path,
            "artifact kind must be a non-empty string",
        )
    if kind not in ARTIFACT_KINDS:
        raise ArtifactValidationError(
            artifact_path,
            f"unknown artifact kind: {kind}",
        )
    if expected_kind is not None and kind != expected_kind:
        raise ArtifactValidationError(
            artifact_path,
            f"artifact kind {kind!r} does not match expected kind {expected_kind!r}",
        )

    name = document.get("name")
    if kind in NAMED_ARTIFACT_KINDS:
        if not is_safe_logical_name(name):
            raise ArtifactValidationError(
                artifact_path,
                "artifact name must match ^[a-z0-9][a-z0-9-]*$",
            )
        suffix = artifact_path.suffix
        if suffix not in {".yaml", ".yml"}:
            raise ArtifactValidationError(
                artifact_path,
                "named artifact filename must end in .yaml or .yml",
            )
        if artifact_path.stem != name:
            raise ArtifactValidationError(
                artifact_path,
                f"artifact filename stem {artifact_path.stem!r} does not match name {name!r}",
            )
    elif name is not None and not is_safe_logical_name(name):
        raise ArtifactValidationError(
            artifact_path,
            "optional config artifact name must match ^[a-z0-9][a-z0-9-]*$",
        )

    return ValidatedArtifact(
        path=artifact_path,
        version=version,
        kind=kind,
        name=name if isinstance(name, str) else None,
        document=document,
    )
