from __future__ import annotations

from pathlib import Path

from cosmic_workspace_steward.artifacts import validate_artifact_envelope
from cosmic_workspace_steward.cosmic_adapter import (
    Capability,
    CapabilityReport,
    CapabilityState,
)
from cosmic_workspace_steward.planning import ActionState, plan_profile, render_plan
from cosmic_workspace_steward.profile_schema import validate_profile_definition


def report(*capabilities: Capability) -> CapabilityReport:
    return CapabilityReport(
        command_path=Path("/usr/bin/cosmic-wm"),
        version=None,
        capabilities=capabilities,
        diagnostics=(),
    )


def profile():
    artifact = validate_artifact_envelope(
        {
            "version": 1,
            "kind": "profile",
            "name": "daily",
            "launch_groups": [
                {
                    "name": "core",
                    "workspace": 1,
                    "applications": [
                        {"id": "terminal", "command": ["wezterm"]},
                        {"id": "browser", "command": ["librewolf"]},
                    ],
                },
                {
                    "name": "communications",
                    "workspace": 2,
                    "applications": [{"id": "slack", "command": ["slack"]}],
                },
            ],
        },
        Path("daily.yaml"),
        expected_kind="profile",
    )
    return validate_profile_definition(artifact)


def test_plan_preserves_serial_group_and_application_order() -> None:
    plan = plan_profile(
        profile(),
        report(
            Capability("workspace_introspection", CapabilityState.SUPPORTED),
            Capability("profile_application", CapabilityState.UNKNOWN),
        ),
    )

    assert [action.sequence for action in plan.actions] == [1, 2, 3, 4, 5]
    assert [action.subject for action in plan.actions] == [
        "core@workspace-1",
        "core/terminal",
        "core/browser",
        "communications@workspace-2",
        "communications/slack",
    ]
    assert [action.state for action in plan.actions] == [
        ActionState.REQUIRES_CONFIRMATION,
        ActionState.UNKNOWN,
        ActionState.UNKNOWN,
        ActionState.REQUIRES_CONFIRMATION,
        ActionState.UNKNOWN,
    ]


def test_plan_marks_supported_profile_application_as_requires_confirmation() -> None:
    plan = plan_profile(
        profile(),
        report(
            Capability("workspace_introspection", CapabilityState.SUPPORTED),
            Capability("profile_application", CapabilityState.SUPPORTED),
        ),
    )

    assert all(
        action.state is ActionState.REQUIRES_CONFIRMATION
        for action in plan.actions
    )


def test_plan_marks_unsupported_capabilities_explicitly() -> None:
    plan = plan_profile(
        profile(),
        report(
            Capability("workspace_introspection", CapabilityState.UNSUPPORTED),
            Capability("profile_application", CapabilityState.UNSUPPORTED),
        ),
    )

    assert [action.state for action in plan.actions] == [
        ActionState.UNSUPPORTED,
        ActionState.UNSUPPORTED,
        ActionState.UNSUPPORTED,
        ActionState.UNSUPPORTED,
        ActionState.UNSUPPORTED,
    ]


def test_missing_capabilities_are_unknown_and_rendering_is_stable() -> None:
    plan = plan_profile(profile(), report())

    assert all(action.state is ActionState.UNKNOWN for action in plan.actions)
    assert render_plan(plan) == "\n".join(
        [
            "profile: daily",
            "dry_run: true",
            "001 unknown prepare-workspace-group core@workspace-1 -- serial launch group; no workspace mutation is performed",
            "002 unknown launch-application core/terminal -- argv=['wezterm']",
            "003 unknown launch-application core/browser -- argv=['librewolf']",
            "004 unknown prepare-workspace-group communications@workspace-2 -- serial launch group; no workspace mutation is performed",
            "005 unknown launch-application communications/slack -- argv=['slack']",
        ]
    )
