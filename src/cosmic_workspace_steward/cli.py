"""Command interface for generic Workspace Steward artifacts."""
from __future__ import annotations

import os
from pathlib import Path
import sys
from typing import Mapping, Sequence, TextIO

import yaml

from .artifacts import (
    ValidatedArtifact,
    is_safe_logical_name,
    validate_artifact_envelope,
)
from .cosmic_adapter import CapabilityReport
from .discovery import DiscoveryResult, discover_artifacts
from .errors import ArtifactError
from .layout_schema import validate_layout_definition
from .planning import plan_profile, render_plan
from .profile_schema import validate_profile_definition
from .xdg import resolve_artifact_roots
from .yaml_io import create_yaml_mapping_exclusively

_USAGE = """usage:
  python -m cosmic_workspace_steward.cli profiles list
  python -m cosmic_workspace_steward.cli sessions list
  python -m cosmic_workspace_steward.cli layouts list
  python -m cosmic_workspace_steward.cli layouts show NAME
  python -m cosmic_workspace_steward.cli layouts create NAME WORKSPACE_COUNT --dry-run
  python -m cosmic_workspace_steward.cli layouts create NAME WORKSPACE_COUNT --yes
  python -m cosmic_workspace_steward.cli show profile NAME
  python -m cosmic_workspace_steward.cli show session NAME
  python -m cosmic_workspace_steward.cli plan profile NAME
  python -m cosmic_workspace_steward.cli start PROFILE --dry-run
"""


def _artifact_root(environment: Mapping[str, str], home: Path, kind: str) -> Path:
    roots = resolve_artifact_roots(environment, home)
    return roots.data / f"{kind}s"


def _emit_diagnostics(result: DiscoveryResult, stderr: TextIO) -> None:
    for diagnostic in result.diagnostics:
        print(
            f"warning: {diagnostic.path}: {diagnostic.code}: {diagnostic.message}",
            file=stderr,
        )


def _discover(
    *,
    environment: Mapping[str, str],
    home: Path,
    kind: str,
    stderr: TextIO,
) -> DiscoveryResult | None:
    try:
        root = _artifact_root(environment, home, kind)
    except ArtifactError as exc:
        print(f"error: {exc}", file=stderr)
        return None
    result = discover_artifacts(root, kind)
    _emit_diagnostics(result, stderr)
    return result


def _render_document(document: Mapping[str, object]) -> str:
    """Return deterministic YAML for a validated in-memory artifact document."""
    return yaml.safe_dump(
        dict(document),
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    ).rstrip("\n")


def _layout_document(name: str, workspace_count: int) -> dict[str, object]:
    return {
        "kind": "layout",
        "name": name,
        "version": 1,
        "workspace_count": workspace_count,
    }


def _parse_workspace_count(value: str) -> int | None:
    try:
        workspace_count = int(value)
    except ValueError:
        return None
    if workspace_count < 1:
        return None
    return workspace_count


def _find_artifact(
    result: DiscoveryResult,
    name: str,
) -> ValidatedArtifact | None:
    for discovered in result.artifacts:
        if discovered.name == name:
            return discovered.artifact
    return None


def _handle_layouts(
    arguments: list[str],
    *,
    environment: Mapping[str, str],
    home: Path,
    output: TextIO,
    errors: TextIO,
) -> int | None:
    if arguments == ["layouts", "list"]:
        result = _discover(
            environment=environment,
            home=home,
            kind="layout",
            stderr=errors,
        )
        if result is None:
            return 2
        for discovered in result.artifacts:
            try:
                validate_layout_definition(discovered.artifact)
            except ArtifactError as exc:
                print(
                    f"warning: {discovered.path}: invalid-layout: {exc}",
                    file=errors,
                )
                continue
            print(discovered.name, file=output)
        return 0

    if len(arguments) == 3 and arguments[:2] == ["layouts", "show"]:
        name = arguments[2]
        if not is_safe_logical_name(name):
            print(f"error: unsafe layout name: {name!r}", file=errors)
            return 2
        result = _discover(
            environment=environment,
            home=home,
            kind="layout",
            stderr=errors,
        )
        if result is None:
            return 2
        artifact = _find_artifact(result, name)
        if artifact is None:
            print(f"error: layout not found: {name}", file=errors)
            return 1
        try:
            validate_layout_definition(artifact)
        except ArtifactError as exc:
            print(f"error: {exc}", file=errors)
            return 1
        print(_render_document(artifact.document), file=output)
        return 0

    if not (
        len(arguments) in {4, 5}
        and arguments[:2] == ["layouts", "create"]
    ):
        return None

    name = arguments[2]
    count_text = arguments[3]
    option = arguments[4] if len(arguments) == 5 else None

    if not is_safe_logical_name(name):
        print(f"error: unsafe layout name: {name!r}", file=errors)
        return 2

    workspace_count = _parse_workspace_count(count_text)
    if workspace_count is None:
        print(
            "error: workspace_count must be a positive integer",
            file=errors,
        )
        return 2

    if option not in {"--dry-run", "--yes"}:
        print(
            "error: layout creation changes XDG data; "
            "rerun with --dry-run or --yes",
            file=errors,
        )
        return 2

    try:
        path = _artifact_root(environment, home, "layout") / f"{name}.yaml"
        document = _layout_document(name, workspace_count)
        artifact = validate_artifact_envelope(
            document,
            path,
            expected_kind="layout",
        )
        validate_layout_definition(artifact)
    except ArtifactError as exc:
        print(f"error: {exc}", file=errors)
        return 2

    if option == "--dry-run":
        print("action: create", file=output)
        print("dry_run: true", file=output)
        print("kind: layout", file=output)
        print(f"name: {name}", file=output)
        print(f"workspace_count: {workspace_count}", file=output)
        return 0

    try:
        created = create_yaml_mapping_exclusively(path, document)
    except ArtifactError as exc:
        print(f"error: {exc}", file=errors)
        return 1

    if not created:
        print(f"error: layout already exists: {name}", file=errors)
        return 1

    print(f"created layout: {name}", file=output)
    return 0


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> int:
    """Run the generic Workspace Steward artifact CLI."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    resolved_environment = os.environ if environment is None else environment
    resolved_home = Path.home() if home is None else Path(home)

    layout_result = _handle_layouts(
        arguments,
        environment=resolved_environment,
        home=resolved_home,
        output=output,
        errors=errors,
    )
    if layout_result is not None:
        return layout_result

    if (
        len(arguments) == 2
        and arguments[0] in {"profiles", "sessions"}
        and arguments[1] == "list"
    ):
        kind = arguments[0][:-1]
        result = _discover(
            environment=resolved_environment,
            home=resolved_home,
            kind=kind,
            stderr=errors,
        )
        if result is None:
            return 2
        for artifact in result.artifacts:
            print(artifact.name, file=output)
        return 0

    is_plan_command = (
        len(arguments) == 3
        and arguments[0] == "plan"
        and arguments[1] == "profile"
    )
    is_dry_run_start = (
        len(arguments) == 3
        and arguments[0] == "start"
        and arguments[2] == "--dry-run"
    )
    if is_plan_command or is_dry_run_start:
        name = arguments[2] if is_plan_command else arguments[1]
        if not is_safe_logical_name(name):
            print(f"error: unsafe profile name: {name!r}", file=errors)
            return 2
        result = _discover(
            environment=resolved_environment,
            home=resolved_home,
            kind="profile",
            stderr=errors,
        )
        if result is None:
            return 2
        for discovered in result.artifacts:
            if discovered.name == name:
                try:
                    profile = validate_profile_definition(discovered.artifact)
                except ArtifactError as exc:
                    print(f"error: {exc}", file=errors)
                    return 1
                report = CapabilityReport(
                    command_path=None,
                    version=None,
                    capabilities=(),
                    diagnostics=(),
                )
                print(render_plan(plan_profile(profile, report)), file=output)
                return 0
        print(f"error: profile not found: {name}", file=errors)
        return 1

    if (
        len(arguments) == 3
        and arguments[0] == "show"
        and arguments[1] in {"profile", "session"}
    ):
        kind, name = arguments[1], arguments[2]
        if not is_safe_logical_name(name):
            print(f"error: unsafe {kind} name: {name!r}", file=errors)
            return 2
        result = _discover(
            environment=resolved_environment,
            home=resolved_home,
            kind=kind,
            stderr=errors,
        )
        if result is None:
            return 2
        for discovered in result.artifacts:
            if discovered.name == name:
                print(
                    _render_document(discovered.artifact.document),
                    file=output,
                )
                return 0
        print(f"error: {kind} not found: {name}", file=errors)
        return 1

    print(_USAGE.rstrip(), file=errors)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
