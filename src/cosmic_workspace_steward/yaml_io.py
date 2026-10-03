"""Safe YAML mapping loading and exclusive artifact creation."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import yaml

from .errors import YamlArtifactError


def load_yaml_mapping(path: Path) -> dict[str, Any]:
    """Safely load one non-empty YAML mapping from an existing regular file."""

    artifact_path = Path(path)

    if not artifact_path.is_file():
        raise YamlArtifactError(artifact_path, "artifact is not an existing regular file")

    try:
        with artifact_path.open(encoding="utf-8") as stream:
            document = yaml.safe_load(stream)
    except OSError as exc:
        raise YamlArtifactError(artifact_path, f"unable to read artifact: {exc.strerror}") from exc
    except yaml.YAMLError as exc:
        raise YamlArtifactError(artifact_path, f"invalid or unsafe YAML: {exc}") from exc

    if document is None:
        raise YamlArtifactError(artifact_path, "artifact is empty")

    if not isinstance(document, dict):
        raise YamlArtifactError(artifact_path, "artifact root must be a YAML mapping")

    return document


def create_yaml_mapping_exclusively(
    path: Path,
    document: Mapping[str, Any],
) -> bool:
    """Create one YAML mapping without replacing an existing artifact."""
    artifact_path = Path(path)
    rendered = yaml.safe_dump(
        document,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    )

    try:
        artifact_path.parent.mkdir(parents=True, exist_ok=True)
        with artifact_path.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
    except FileExistsError:
        return False
    except OSError as exc:
        raise YamlArtifactError(
            artifact_path,
            f"unable to create artifact: {exc.strerror or exc}",
        ) from exc

    return True
