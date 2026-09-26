"""Read-only command interface for generic Workspace Steward artifacts."""

from __future__ import annotations

from pathlib import Path
import os
import sys
from typing import Mapping, Sequence, TextIO

import yaml

from .artifacts import is_safe_logical_name
from .cosmic_adapter import CapabilityReport
from .discovery import DiscoveryResult, discover_artifacts
from .errors import ArtifactError
from .planning import plan_profile, render_plan
from .profile_schema import validate_profile_definition
from .xdg import resolve_artifact_roots


_USAGE = """usage:
  python -m cosmic_workspace_steward.cli profiles list
  python -m cosmic_workspace_steward.cli sessions list
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


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> int:
    """Run the generic read-only artifact CLI."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr
    resolved_environment = os.environ if environment is None else environment
    resolved_home = Path.home() if home is None else Path(home)

    if len(arguments) == 2 and arguments[0] in {"profiles", "sessions"} and arguments[1] == "list":
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

        for artifact in result.artifacts:
            if artifact.name == name:
                try:
                    profile = validate_profile_definition(artifact.artifact)
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

    if len(arguments) == 3 and arguments[0] == "show" and arguments[1] in {"profile", "session"}:
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

        for artifact in result.artifacts:
            if artifact.name == name:
                print(_render_document(artifact.artifact.document), file=output)
                return 0

        print(f"error: {kind} not found: {name}", file=errors)
        return 1

    print(_USAGE.rstrip(), file=errors)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
