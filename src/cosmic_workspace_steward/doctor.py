"""Non-mutating diagnostics for generic Workspace Steward artifacts."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys
from typing import Mapping, Sequence, TextIO

from .cosmic_adapter import CapabilityReport, CosmicWmCapabilityAdapter
from .discovery import DiscoveryResult, discover_artifacts
from .errors import ArtifactError
from .xdg import ArtifactRoots, resolve_artifact_roots


@dataclass(frozen=True)
class DoctorReport:
    """Read-only diagnostic result for the generic Workspace Steward runtime."""

    roots: ArtifactRoots | None
    profiles: DiscoveryResult | None
    sessions: DiscoveryResult | None
    adapter: CapabilityReport | None
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

    @property
    def exit_code(self) -> int:
        return 1 if self.blockers else 0


def inspect_environment(
    *,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    adapter: CosmicWmCapabilityAdapter | None = None,
) -> DoctorReport:
    """Collect diagnostic state without creating files or changing desktop state."""
    resolved_environment = os.environ if environment is None else environment
    resolved_home = Path.home() if home is None else Path(home)
    blockers: list[str] = []
    warnings: list[str] = []

    try:
        roots = resolve_artifact_roots(resolved_environment, resolved_home)
    except ArtifactError as exc:
        return DoctorReport(
            roots=None,
            profiles=None,
            sessions=None,
            adapter=None,
            blockers=(str(exc),),
            warnings=(),
        )

    profiles = discover_artifacts(roots.data / "profiles", "profile")
    sessions = discover_artifacts(roots.data / "sessions", "session")

    for label, result in (("profiles", profiles), ("sessions", sessions)):
        for diagnostic in result.diagnostics:
            warnings.append(
                f"{label}: {diagnostic.path}: {diagnostic.code}: {diagnostic.message}"
            )

    capability_adapter = adapter or CosmicWmCapabilityAdapter()
    native = capability_adapter.discover()

    if native.command_path is None:
        warnings.append("native: cosmic-wm was not found on PATH")

    for diagnostic in native.diagnostics:
        warnings.append(f"native: {diagnostic.code}: {diagnostic.message}")

    return DoctorReport(
        roots=roots,
        profiles=profiles,
        sessions=sessions,
        adapter=native,
        blockers=tuple(sorted(blockers)),
        warnings=tuple(sorted(warnings)),
    )


def render_report(report: DoctorReport) -> str:
    """Render a stable, human-readable report without writing files."""
    lines: list[str] = ["Workspace Steward doctor"]

    if report.roots is None:
        lines.append("roots: unavailable")
    else:
        lines.extend(
            (
                f"config_root: {report.roots.config}",
                f"state_root: {report.roots.state}",
                f"data_root: {report.roots.data}",
            )
        )

    for label, result in (("profiles", report.profiles), ("sessions", report.sessions)):
        if result is None:
            lines.append(f"{label}: unavailable")
        else:
            lines.append(f"{label}: {len(result.artifacts)} valid, {len(result.diagnostics)} findings")

    if report.adapter is None:
        lines.append("native_command: unavailable")
    else:
        lines.append(f"native_command: {report.adapter.command_path or 'not found'}")
        lines.append(f"native_version: {report.adapter.version or 'unknown'}")
        for capability in report.adapter.capabilities:
            detail = f" ({capability.detail})" if capability.detail else ""
            lines.append(
                f"capability.{capability.name}: {capability.state.value}{detail}"
            )

    if report.blockers:
        lines.append("blockers:")
        lines.extend(f"- {item}" for item in report.blockers)
    else:
        lines.append("blockers: none")

    if report.warnings:
        lines.append("warnings:")
        lines.extend(f"- {item}" for item in report.warnings)
    else:
        lines.append("warnings: none")

    lines.append(f"result: {'blocked' if report.blockers else 'ok'}")
    return "\n".join(lines)


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    environment: Mapping[str, str] | None = None,
    home: Path | None = None,
    adapter: CosmicWmCapabilityAdapter | None = None,
) -> int:
    """Run the read-only doctor command."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout

    if arguments:
        print("usage: python -m cosmic_workspace_steward.doctor", file=output)
        return 2

    report = inspect_environment(
        environment=environment,
        home=home,
        adapter=adapter,
    )
    print(render_report(report), file=output)
    return report.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
