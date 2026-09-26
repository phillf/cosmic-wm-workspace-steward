from __future__ import annotations

from pathlib import Path
from shutil import copytree

from cosmic_workspace_steward.cosmic_adapter import (
    Capability,
    CapabilityReport,
    CapabilityState,
)
from cosmic_workspace_steward.discovery import discover_artifacts
from cosmic_workspace_steward.planning import plan_profile, render_plan
from cosmic_workspace_steward.profile_schema import validate_profile_definition


FIXTURES = Path(__file__).parent / "fixtures" / "artifacts"


def capability_report() -> CapabilityReport:
    return CapabilityReport(
        command_path=None,
        version=None,
        capabilities=(
            Capability(
                "workspace_introspection",
                CapabilityState.SUPPORTED,
            ),
            Capability(
                "profile_application",
                CapabilityState.UNKNOWN,
            ),
        ),
        diagnostics=(),
    )


def test_fixture_valid_profile_has_deterministic_discovery_and_plan(
    tmp_path: Path,
) -> None:
    root = tmp_path / "profiles"
    copytree(FIXTURES / "valid-profiles", root)

    result = discover_artifacts(root, "profile")

    assert [artifact.name for artifact in result.artifacts] == ["daily"]
    assert result.diagnostics == ()

    profile = validate_profile_definition(result.artifacts[0].artifact)
    assert render_plan(plan_profile(profile, capability_report())) == "\n".join(
        [
            "profile: daily",
            "dry_run: true",
            (
                "001 requires-confirmation "
                "prepare-workspace-group core@workspace-1 -- "
                "serial launch group; no workspace mutation is performed"
            ),
            "002 unknown launch-application core/terminal -- argv=['wezterm']",
            (
                "003 unknown launch-application core/browser -- "
                "argv=['librewolf', '--new-window']"
            ),
            (
                "004 requires-confirmation "
                "prepare-workspace-group communications@workspace-2 -- "
                "serial launch group; no workspace mutation is performed"
            ),
            "005 unknown launch-application communications/slack -- argv=['slack']",
        ]
    )


def test_fixture_invalid_profiles_produce_named_safety_diagnostics(
    tmp_path: Path,
) -> None:
    root = tmp_path / "profiles"
    copytree(FIXTURES / "invalid-profiles", root)

    result = discover_artifacts(root, "profile")

    assert result.artifacts == ()
    assert [
        (diagnostic.path.name, diagnostic.code)
        for diagnostic in result.diagnostics
    ] == [
        ("duplicate-extension.yaml", "duplicate-name"),
        ("duplicate-extension.yml", "duplicate-name"),
        ("name-mismatch.yaml", "invalid-artifact"),
        ("unsafe-python-tag.yaml", "invalid-artifact"),
    ]
