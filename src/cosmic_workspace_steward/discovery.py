"""Read-only generic YAML artifact discovery."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .artifacts import ValidatedArtifact, validate_artifact_envelope
from .errors import ArtifactError
from .yaml_io import load_yaml_mapping


@dataclass(frozen=True)
class DiscoveryDiagnostic:
    """One non-fatal discovery finding."""

    path: Path
    code: str
    message: str


@dataclass(frozen=True)
class DiscoveredArtifact:
    """One validated artifact safely discovered under a designated root."""

    name: str
    path: Path
    artifact: ValidatedArtifact


@dataclass(frozen=True)
class DiscoveryResult:
    """Deterministic discovery output with usable artifacts and diagnostics."""

    artifacts: tuple[DiscoveredArtifact, ...]
    diagnostics: tuple[DiscoveryDiagnostic, ...]


def _diagnostic(path: Path, code: str, message: str) -> DiscoveryDiagnostic:
    return DiscoveryDiagnostic(path=path, code=code, message=message)


def _is_within_root(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def discover_artifacts(root: Path, expected_kind: str) -> DiscoveryResult:
    """Discover one expected generic artifact kind without filesystem mutation."""

    artifact_root = Path(root)
    if not artifact_root.exists():
        return DiscoveryResult(artifacts=(), diagnostics=())

    try:
        resolved_root = artifact_root.resolve(strict=True)
    except OSError as exc:
        return DiscoveryResult(
            artifacts=(),
            diagnostics=(
                _diagnostic(
                    artifact_root,
                    "unresolvable-root",
                    f"unable to resolve artifact root: {exc.strerror or exc}",
                ),
            ),
        )

    if not resolved_root.is_dir():
        return DiscoveryResult(
            artifacts=(),
            diagnostics=(
                _diagnostic(
                    artifact_root,
                    "root-not-directory",
                    "artifact root is not a directory",
                ),
            ),
        )

    candidates: list[DiscoveredArtifact] = []
    diagnostics: list[DiscoveryDiagnostic] = []

    try:
        entries = sorted(resolved_root.iterdir(), key=lambda entry: entry.name)
    except OSError as exc:
        return DiscoveryResult(
            artifacts=(),
            diagnostics=(
                _diagnostic(
                    resolved_root,
                    "unreadable-root",
                    f"unable to read artifact root: {exc.strerror or exc}",
                ),
            ),
        )

    for entry in entries:
        if entry.suffix not in {".yaml", ".yml"}:
            continue

        try:
            resolved_entry = entry.resolve(strict=True)
        except OSError as exc:
            diagnostics.append(
                _diagnostic(
                    entry,
                    "unresolvable-path",
                    f"unable to resolve artifact path: {exc.strerror or exc}",
                )
            )
            continue

        if not _is_within_root(resolved_entry, resolved_root):
            diagnostics.append(
                _diagnostic(
                    entry,
                    "path-escape",
                    "artifact path resolves outside the designated root",
                )
            )
            continue

        if not resolved_entry.is_file():
            diagnostics.append(
                _diagnostic(
                    entry,
                    "not-regular-file",
                    "artifact candidate is not a regular file",
                )
            )
            continue

        try:
            document = load_yaml_mapping(resolved_entry)
            artifact = validate_artifact_envelope(
                document,
                entry,
                expected_kind=expected_kind,
            )
        except ArtifactError as exc:
            diagnostics.append(
                _diagnostic(
                    entry,
                    "invalid-artifact",
                    str(exc),
                )
            )
            continue

        if artifact.name is None:
            diagnostics.append(
                _diagnostic(
                    entry,
                    "unnamed-artifact",
                    "discovered artifacts must have a logical name",
                )
            )
            continue

        candidates.append(
            DiscoveredArtifact(
                name=artifact.name,
                path=entry,
                artifact=artifact,
            )
        )

    candidates_by_name: dict[str, list[DiscoveredArtifact]] = {}
    for candidate in candidates:
        candidates_by_name.setdefault(candidate.name, []).append(candidate)

    artifacts: list[DiscoveredArtifact] = []
    for name in sorted(candidates_by_name):
        group = candidates_by_name[name]
        if len(group) == 1:
            artifacts.append(group[0])
            continue
        for candidate in sorted(group, key=lambda item: str(item.path)):
            diagnostics.append(
                _diagnostic(
                    candidate.path,
                    "duplicate-name",
                    f"duplicate artifact logical name: {name}",
                )
            )

    return DiscoveryResult(
        artifacts=tuple(sorted(artifacts, key=lambda item: item.name)),
        diagnostics=tuple(
            sorted(
                diagnostics,
                key=lambda item: (str(item.path), item.code, item.message),
            )
        ),
    )
