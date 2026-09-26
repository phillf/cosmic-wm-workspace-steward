from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

import pytest

from cosmic_workspace_steward.cosmic_adapter import (
    CapabilityState,
    CosmicWmCapabilityAdapter,
)


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CompletedProcess[str] | Exception]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...]) -> CompletedProcess[str]:
        self.calls.append(tuple(argv))
        response = self.responses[tuple(argv)]
        if isinstance(response, Exception):
            raise response
        return response


def completed(
    argv: tuple[str, ...],
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> CompletedProcess[str]:
    return CompletedProcess(list(argv), returncode, stdout=stdout, stderr=stderr)


def test_missing_command_returns_unsupported_without_running_anything(monkeypatch) -> None:
    monkeypatch.setattr(
        "cosmic_workspace_steward.cosmic_adapter.which",
        lambda _: None,
    )

    report = CosmicWmCapabilityAdapter().discover()

    assert report.command_path is None
    assert all(item.state is CapabilityState.UNSUPPORTED for item in report.capabilities)
    assert report.diagnostics[0].code == "command_not_found"


def test_adapter_runs_only_the_explicit_read_only_probe_allowlist() -> None:
    path = "/usr/bin/cosmic-wm"
    runner = FakeRunner(
        {
            (path, "--version"): completed((path, "--version"), "cosmic-wm 1.0.0\n"),
            (path, "--help"): completed((path, "--help"), "Usage: cosmic-wm [OPTIONS]\n"),
            (path, "status"): completed((path, "status"), "Total workspaces active: 7\n"),
        }
    )

    report = CosmicWmCapabilityAdapter(runner=runner, command_path=path).discover()

    assert runner.calls == [(path, "--version"), (path, "--help"), (path, "status")]
    assert report.version == "cosmic-wm 1.0.0"
    assert report.capability("version_detection").state is CapabilityState.SUPPORTED
    assert report.capability("help_discovery").state is CapabilityState.SUPPORTED
    assert report.capability("workspace_introspection").state is CapabilityState.SUPPORTED
    assert report.capability("window_introspection").state is CapabilityState.SUPPORTED
    assert report.capability("profile_application").state is CapabilityState.UNKNOWN
    assert report.capability("session_application").state is CapabilityState.UNKNOWN


def test_unsupported_version_is_informational_and_status_can_still_be_supported() -> None:
    path = "/usr/bin/cosmic-wm"
    runner = FakeRunner(
        {
            (path, "--version"): completed(
                (path, "--version"),
                stderr="No such option: --version",
                returncode=2,
            ),
            (path, "--help"): completed((path, "--help"), "Usage: cosmic-wm COMMAND\n"),
            (path, "status"): completed((path, "status"), "Total workspaces active: 7\n"),
        }
    )

    report = CosmicWmCapabilityAdapter(runner=runner, command_path=path).discover()

    assert report.version is None
    assert report.capability("version_detection").state is CapabilityState.UNKNOWN
    assert report.capability("workspace_introspection").state is CapabilityState.SUPPORTED
    assert report.capability("window_introspection").state is CapabilityState.SUPPORTED
    assert [item.code for item in report.diagnostics] == ["version_unsupported"]


def test_failed_status_does_not_create_speculative_introspection_capabilities() -> None:
    path = "/usr/bin/cosmic-wm"
    runner = FakeRunner(
        {
            (path, "--version"): completed((path, "--version"), "cosmic-wm 1.0.0\n"),
            (path, "--help"): completed((path, "--help"), "Usage: cosmic-wm COMMAND\n"),
            (path, "status"): completed(
                (path, "status"),
                stderr="not connected to COSMIC session",
                returncode=1,
            ),
        }
    )

    report = CosmicWmCapabilityAdapter(runner=runner, command_path=path).discover()

    assert report.capability("workspace_introspection").state is CapabilityState.UNKNOWN
    assert report.capability("window_introspection").state is CapabilityState.UNKNOWN
    assert [item.code for item in report.diagnostics] == ["probe_failed"]


def test_runner_exception_is_captured_as_a_diagnostic() -> None:
    path = "/usr/bin/cosmic-wm"
    runner = FakeRunner(
        {
            (path, "--version"): FileNotFoundError("missing binary"),
            (path, "--help"): TimeoutError("probe timed out"),
            (path, "status"): TimeoutError("probe timed out"),
        }
    )

    report = CosmicWmCapabilityAdapter(runner=runner, command_path=path).discover()

    assert report.version is None
    assert all(item.state is CapabilityState.UNKNOWN for item in report.capabilities)
    assert [item.code for item in report.diagnostics] == [
        "version_unsupported",
        "probe_failed",
        "probe_failed",
    ]


def test_unsafe_operational_commands_are_rejected() -> None:
    path = "/usr/bin/cosmic-wm"
    adapter = CosmicWmCapabilityAdapter(command_path=path)

    with pytest.raises(ValueError, match="unsafe cosmic-wm probe rejected"):
        adapter._safe_run(command_path=Path(path), arguments=("start",), diagnostics=[])
