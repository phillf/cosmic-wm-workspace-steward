from __future__ import annotations

from io import StringIO
from pathlib import Path
from subprocess import CompletedProcess

from cosmic_workspace_steward.cosmic_adapter import CosmicWmCapabilityAdapter
from cosmic_workspace_steward.doctor import inspect_environment, main, render_report


class FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CompletedProcess[str]]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, ...]] = []

    def run(self, argv: tuple[str, ...]) -> CompletedProcess[str]:
        self.calls.append(tuple(argv))
        return self.responses[tuple(argv)]


def completed(
    argv: tuple[str, ...],
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> CompletedProcess[str]:
    return CompletedProcess(list(argv), returncode, stdout=stdout, stderr=stderr)


def safe_adapter(path: str = "/usr/bin/cosmic-wm") -> tuple[CosmicWmCapabilityAdapter, FakeRunner]:
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
    return CosmicWmCapabilityAdapter(runner=runner, command_path=path), runner


def test_doctor_is_read_only_and_renders_deterministic_report(tmp_path: Path) -> None:
    home = tmp_path / "home"
    data_root = home / ".local" / "share" / "cosmic-workspace-steward"
    profiles = data_root / "profiles"
    sessions = data_root / "sessions"
    profiles.mkdir(parents=True)
    sessions.mkdir(parents=True)

    (profiles / "daily.yaml").write_text(
        "version: 1\nkind: profile\nname: daily\n",
        encoding="utf-8",
    )
    (sessions / "morning.yaml").write_text(
        "version: 1\nkind: session\nname: morning\n",
        encoding="utf-8",
    )

    adapter, runner = safe_adapter()
    report = inspect_environment(environment={}, home=home, adapter=adapter)
    rendered = render_report(report)

    assert report.exit_code == 0
    assert runner.calls == [
        ("/usr/bin/cosmic-wm", "--version"),
        ("/usr/bin/cosmic-wm", "--help"),
        ("/usr/bin/cosmic-wm", "status"),
    ]
    assert "profiles: 1 valid, 0 findings" in rendered
    assert "sessions: 1 valid, 0 findings" in rendered
    assert "capability.workspace_introspection: supported" in rendered
    assert "capability.window_introspection: supported" in rendered
    assert "blockers: none" in rendered
    assert "result: ok" in rendered
    assert not (data_root / "config").exists()
    assert not (data_root / "state").exists()


def test_doctor_reports_invalid_artifacts_as_warnings_not_blockers(tmp_path: Path) -> None:
    home = tmp_path / "home"
    profiles = home / ".local" / "share" / "cosmic-workspace-steward" / "profiles"
    profiles.mkdir(parents=True)
    (profiles / "broken.yaml").write_text("not: [valid", encoding="utf-8")

    adapter, _ = safe_adapter()
    report = inspect_environment(environment={}, home=home, adapter=adapter)

    assert report.exit_code == 0
    assert report.blockers == ()
    assert any(item.startswith("profiles:") for item in report.warnings)
    assert "invalid-artifact" in render_report(report)


def test_doctor_warns_when_native_command_is_not_found(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "cosmic_workspace_steward.cosmic_adapter.which",
        lambda _: None,
    )

    report = inspect_environment(environment={}, home=tmp_path / "home")

    assert report.exit_code == 0
    assert report.blockers == ()
    assert "native: cosmic-wm was not found on PATH" in report.warnings
    assert "result: ok" in render_report(report)


def test_doctor_blocks_on_invalid_xdg_override(tmp_path: Path) -> None:
    report = inspect_environment(
        environment={"XDG_DATA_HOME": "relative"},
        home=tmp_path / "home",
    )

    assert report.exit_code == 1
    assert report.roots is None
    assert report.adapter is None
    assert report.blockers == ("XDG_DATA_HOME must be an absolute path when set",)


def test_main_rejects_arguments_without_running_diagnostics() -> None:
    output = StringIO()

    exit_code = main(["unexpected"], stdout=output)

    assert exit_code == 2
    assert output.getvalue() == "usage: python -m cosmic_workspace_steward.doctor\n"


def test_main_prints_report_and_returns_blocker_status(tmp_path: Path) -> None:
    output = StringIO()
    adapter, _ = safe_adapter()

    exit_code = main(
        [],
        stdout=output,
        environment={},
        home=tmp_path / "home",
        adapter=adapter,
    )

    assert exit_code == 0
    assert output.getvalue().startswith("Workspace Steward doctor\n")
    assert output.getvalue().endswith("result: ok\n")
