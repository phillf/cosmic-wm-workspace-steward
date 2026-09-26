"""Read-only capability discovery for the native COSMIC window manager."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from shutil import which
from subprocess import CompletedProcess, run
from typing import Protocol, Sequence


class CapabilityState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Diagnostic:
    code: str
    message: str


@dataclass(frozen=True)
class Capability:
    name: str
    state: CapabilityState
    detail: str | None = None


@dataclass(frozen=True)
class CapabilityReport:
    command_path: Path | None
    version: str | None
    capabilities: tuple[Capability, ...]
    diagnostics: tuple[Diagnostic, ...]

    def capability(self, name: str) -> Capability:
        for capability in self.capabilities:
            if capability.name == name:
                return capability
        raise KeyError(name)


class CommandRunner(Protocol):
    def run(self, argv: Sequence[str]) -> CompletedProcess[str]:
        """Run an explicitly allowlisted, read-only command."""


class SubprocessRunner:
    def run(self, argv: Sequence[str]) -> CompletedProcess[str]:
        return run(
            list(argv),
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )


class CosmicWmCapabilityAdapter:
    """Discover native COSMIC capabilities through safe, read-only probes.

    This adapter is the only layer that invokes ``cosmic-wm``. It allows
    exactly ``--help``, ``--version``, and ``status``. No command which starts,
    saves, restores, configures, recompiles, or otherwise mutates state is
    available through this adapter.
    """

    _COMMAND = "cosmic-wm"
    _SAFE_ARGUMENTS = (("--version",), ("--help",), ("status",))
    _CAPABILITIES = (
        "version_detection",
        "help_discovery",
        "workspace_introspection",
        "window_introspection",
        "profile_application",
        "session_application",
    )

    def __init__(
        self,
        runner: CommandRunner | None = None,
        command_path: str | Path | None = None,
    ) -> None:
        self._runner = runner or SubprocessRunner()
        self._command_path = Path(command_path) if command_path else None

    def discover(self) -> CapabilityReport:
        command_path = self._resolve_command()
        if command_path is None:
            return CapabilityReport(
                command_path=None,
                version=None,
                capabilities=tuple(
                    Capability(
                        name,
                        CapabilityState.UNSUPPORTED,
                        "cosmic-wm was not found",
                    )
                    for name in self._CAPABILITIES
                ),
                diagnostics=(
                    Diagnostic(
                        "command_not_found",
                        "cosmic-wm was not found on PATH; no native command was invoked.",
                    ),
                ),
            )

        diagnostics: list[Diagnostic] = []
        version_result = self._safe_run(
            command_path,
            ("--version",),
            diagnostics,
            failure_code="version_unsupported",
        )
        help_result = self._safe_run(command_path, ("--help",), diagnostics)
        status_result = self._safe_run(command_path, ("status",), diagnostics)

        version = self._parse_version(version_result.stdout) if version_result else None

        return CapabilityReport(
            command_path=command_path,
            version=version,
            capabilities=self._capabilities_from_results(
                version=version,
                help_result=help_result,
                status_result=status_result,
            ),
            diagnostics=tuple(diagnostics),
        )

    def _resolve_command(self) -> Path | None:
        if self._command_path is not None:
            return self._command_path
        found = which(self._COMMAND)
        return Path(found) if found else None

    def _safe_run(
        self,
        command_path: Path,
        arguments: tuple[str, ...],
        diagnostics: list[Diagnostic],
        *,
        failure_code: str = "probe_failed",
    ) -> CompletedProcess[str] | None:
        if arguments not in self._SAFE_ARGUMENTS:
            raise ValueError(f"unsafe cosmic-wm probe rejected: {arguments!r}")

        argv = (str(command_path), *arguments)
        try:
            result = self._runner.run(argv)
        except (OSError, TimeoutError) as exc:
            diagnostics.append(
                Diagnostic(
                    failure_code,
                    f"{' '.join(argv)} could not be executed: {exc}",
                ),
            )
            return None

        if result.returncode != 0:
            message = (result.stderr or result.stdout).strip() or "command returned no output"
            diagnostics.append(
                Diagnostic(
                    failure_code,
                    f"{' '.join(argv)} exited with {result.returncode}: {message}",
                ),
            )
            return None

        return result

    @staticmethod
    def _parse_version(output: str) -> str | None:
        line = next((line.strip() for line in output.splitlines() if line.strip()), "")
        return line or None

    def _capabilities_from_results(
        self,
        *,
        version: str | None,
        help_result: CompletedProcess[str] | None,
        status_result: CompletedProcess[str] | None,
    ) -> tuple[Capability, ...]:
        status_detail = (
            "Read-only status probe completed; output is retained only as probe evidence "
            "and is not parsed into window records."
            if status_result
            else "Read-only status probe did not complete successfully."
        )
        return (
            Capability(
                "version_detection",
                CapabilityState.SUPPORTED if version else CapabilityState.UNKNOWN,
                version if version else "No recognized version output was returned.",
            ),
            Capability(
                "help_discovery",
                CapabilityState.SUPPORTED if help_result else CapabilityState.UNKNOWN,
                "Read-only --help probe completed."
                if help_result
                else "Read-only --help probe did not complete successfully.",
            ),
            Capability(
                "workspace_introspection",
                CapabilityState.SUPPORTED if status_result else CapabilityState.UNKNOWN,
                status_detail,
            ),
            Capability(
                "window_introspection",
                CapabilityState.SUPPORTED if status_result else CapabilityState.UNKNOWN,
                status_detail,
            ),
            Capability(
                "profile_application",
                CapabilityState.UNKNOWN,
                "No safe, documented profile-application contract is used.",
            ),
            Capability(
                "session_application",
                CapabilityState.UNKNOWN,
                "No safe, documented session-application contract is used.",
            ),
        )
