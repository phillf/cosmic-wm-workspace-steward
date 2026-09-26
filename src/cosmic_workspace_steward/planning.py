"""Deterministic, non-mutating generic profile planning."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from .cosmic_adapter import CapabilityReport, CapabilityState
from .profile_schema import ProfileDefinition


class ActionState(str, Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"
    REQUIRES_CONFIRMATION = "requires-confirmation"


@dataclass(frozen=True)
class PlannedAction:
    """One ordered, non-executing action proposal."""

    sequence: int
    action: str
    subject: str
    state: ActionState
    detail: str


@dataclass(frozen=True)
class ProfilePlan:
    """A deterministic dry-run plan for one validated generic profile."""

    profile_name: str
    actions: tuple[PlannedAction, ...]


def _capability_state(report: CapabilityReport, name: str) -> CapabilityState:
    try:
        return report.capability(name).state
    except KeyError:
        return CapabilityState.UNKNOWN


def _workspace_action_state(report: CapabilityReport) -> ActionState:
    native = _capability_state(report, "workspace_introspection")
    if native is CapabilityState.UNSUPPORTED:
        return ActionState.UNSUPPORTED
    if native is CapabilityState.SUPPORTED:
        return ActionState.REQUIRES_CONFIRMATION
    return ActionState.UNKNOWN


def _launch_action_state(report: CapabilityReport) -> ActionState:
    native = _capability_state(report, "profile_application")
    if native is CapabilityState.SUPPORTED:
        return ActionState.REQUIRES_CONFIRMATION
    if native is CapabilityState.UNSUPPORTED:
        return ActionState.UNSUPPORTED
    return ActionState.UNKNOWN


def plan_profile(profile: ProfileDefinition, report: CapabilityReport) -> ProfilePlan:
    """Create a deterministic, non-mutating action plan.

    A plan never runs an application, changes a workspace, writes an artifact,
    or invokes a native command. It simply preserves validated launch-group and
    application order while exposing current native capability limits.
    """
    actions: list[PlannedAction] = []
    sequence = 1

    for group in profile.launch_groups:
        actions.append(
            PlannedAction(
                sequence=sequence,
                action="prepare-workspace-group",
                subject=f"{group.name}@workspace-{group.workspace}",
                state=_workspace_action_state(report),
                detail="serial launch group; no workspace mutation is performed",
            )
        )
        sequence += 1

        for application in group.applications:
            actions.append(
                PlannedAction(
                    sequence=sequence,
                    action="launch-application",
                    subject=f"{group.name}/{application.identifier}",
                    state=_launch_action_state(report),
                    detail="argv=" + repr(list(application.command)),
                )
            )
            sequence += 1

    return ProfilePlan(profile_name=profile.name, actions=tuple(actions))


def render_plan(plan: ProfilePlan) -> str:
    """Render stable human-readable dry-run plan output."""
    lines = [f"profile: {plan.profile_name}", "dry_run: true"]
    for action in plan.actions:
        lines.append(
            f"{action.sequence:03d} {action.state.value} "
            f"{action.action} {action.subject} -- {action.detail}"
        )
    return "\n".join(lines)
