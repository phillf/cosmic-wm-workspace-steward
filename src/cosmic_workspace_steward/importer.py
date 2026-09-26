"""Read-only importer for CT reference deployment profile drafts."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from .artifacts import is_safe_logical_name
from .errors import ArtifactError
from .yaml_io import load_yaml_mapping


@dataclass(frozen=True)
class ImportDiagnostic:
    """One non-fatal finding preserved for human review."""

    code: str
    path: Path
    message: str


@dataclass(frozen=True)
class ImportDraft:
    """A review-required generic import draft with source diagnostics."""

    document: Mapping[str, Any]
    diagnostics: tuple[ImportDiagnostic, ...]


def _safe_draft_name(value: str) -> str:
    normalized = value.lower().replace("_", "-")
    normalized = "-".join(part for part in normalized.split("-") if part)
    if not is_safe_logical_name(normalized):
        raise ArtifactError(
            f"unsafe import draft name derived from source: {value!r}"
        )
    return normalized


def _source_profile_names(paths: Sequence[Path]) -> list[str]:
    names: list[str] = []
    for path in paths:
        try:
            source = load_yaml_mapping(path)
        except ArtifactError:
            names.append(path.stem)
            continue
        name = source.get("name")
        names.append(name if isinstance(name, str) else path.stem)
    return names


def _read_source_profile(path: Path) -> tuple[Mapping[str, Any] | None, ImportDiagnostic | None]:
    try:
        document = load_yaml_mapping(path)
    except ArtifactError as exc:
        return None, ImportDiagnostic(
            "invalid-source-profile",
            path,
            str(exc),
        )
    return document, None


def import_ct_profiles(paths: Sequence[Path], *, draft_name: str) -> ImportDraft:
    """Create an inactive review-only draft from explicit CT profile paths.

    The importer reads files only. It does not write artifacts, invoke native
    commands, alter CT profiles, execute source commands, or map shell commands
    and COSMIC matchers into generic launch behavior.
    """
    safe_name = _safe_draft_name(draft_name)
    diagnostics: list[ImportDiagnostic] = []
    source_profiles: list[dict[str, Any]] = []

    for source_path in sorted((Path(path) for path in paths), key=lambda path: str(path)):
        document, failure = _read_source_profile(source_path)
        if failure is not None:
            diagnostics.append(failure)
            continue
        assert document is not None

        name = document.get("name")
        description = document.get("description")
        apps = document.get("apps")

        profile: dict[str, Any] = {
            "source_path": str(source_path),
            "source_name": name if isinstance(name, str) else None,
            "source_description": description if isinstance(description, str) else None,
            "applications": [],
        }

        if not isinstance(name, str) or not name:
            diagnostics.append(
                ImportDiagnostic(
                    "missing-source-name",
                    source_path,
                    "source profile name is missing or not a non-empty string",
                )
            )
        if not isinstance(apps, list):
            diagnostics.append(
                ImportDiagnostic(
                    "invalid-source-apps",
                    source_path,
                    "source profile apps must be a list",
                )
            )
            source_profiles.append(profile)
            continue

        for index, app in enumerate(apps):
            if not isinstance(app, Mapping):
                diagnostics.append(
                    ImportDiagnostic(
                        "invalid-source-app",
                        source_path,
                        f"apps[{index}] is not a mapping",
                    )
                )
                continue

            record = {
                "source_index": index,
                "command": app.get("command"),
                "workspace": app.get("workspace"),
                "match": app.get("match"),
            }
            profile["applications"].append(record)
            diagnostics.append(
                ImportDiagnostic(
                    "review-command-and-match",
                    source_path,
                    (
                        f"apps[{index}] was preserved as source data; "
                        "shell command strings and CT matcher metadata require "
                        "human mapping before a generic profile can be created"
                    ),
                )
            )

        source_profiles.append(profile)

    diagnostics = sorted(
        diagnostics,
        key=lambda item: (str(item.path), item.code, item.message),
    )
    document: dict[str, Any] = {
        "version": 1,
        "kind": "import-draft",
        "name": safe_name,
        "status": "inactive",
        "review_required": True,
        "source_format": "ct-reference-profile-v1",
        "source_profiles": source_profiles,
        "diagnostics": [
            {
                "code": item.code,
                "source_path": str(item.path),
                "message": item.message,
            }
            for item in diagnostics
        ],
    }
    return ImportDraft(document=document, diagnostics=tuple(diagnostics))
