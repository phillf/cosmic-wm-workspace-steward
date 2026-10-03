#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys
import tempfile

try:
    import yaml
except ModuleNotFoundError:
    print(
        "ERROR: PyYAML is required for ws-man policy management. "
        "Install the project dependencies and retry.",
        file=sys.stderr,
    )
    raise SystemExit(2)

LAYOUT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
OPERATIONS = ("reroute", "purge")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(2)


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def config_path() -> Path:
    return repo_root() / "ws-man.config.yaml"


def layouts_dir() -> Path:
    return repo_root() / "profiles"


def discover_layouts() -> list[str]:
    names: set[str] = set()

    for directory in layouts_dir().iterdir():
        if not directory.is_dir() or not LAYOUT_RE.fullmatch(directory.name):
            continue

        pattern = re.compile(
            re.escape(directory.name) + r"-ws([0-9]+)\.yaml"
        )

        if any(
            pattern.fullmatch(path.name)
            for path in directory.glob(f"{directory.name}-ws*.yaml")
        ):
            names.add(directory.name)

    return sorted(names)


def discover_workspaces(layout: str) -> list[int]:
    workspaces: set[int] = set()
    layout_path = layouts_dir() / layout
    pattern = re.compile(re.escape(layout) + r"-ws([0-9]+)\.yaml")

    for path in layout_path.glob(f"{layout}-ws*.yaml"):
        match = pattern.fullmatch(path.name)
        if match:
            workspaces.add(int(match.group(1)))

    return sorted(workspaces)


def require_known_layout(layout: str) -> None:
    if not LAYOUT_RE.fullmatch(layout):
        fail(f"Invalid layout name: {layout}")

    if layout not in discover_layouts():
        fail(f"Unknown layout: {layout}")


def inferred_workspace_count(layout: str) -> int:
    workspaces = discover_workspaces(layout)

    if not workspaces:
        fail(f"Layout {layout!r} has no primary workspace files.")

    expected = list(range(1, max(workspaces) + 1))
    if workspaces != expected:
        found = ",".join(map(str, workspaces))
        fail(
            f"Layout {layout!r} primary workspace files must be contiguous "
            f"from WS1; discovered {found}."
        )

    return len(workspaces)


def load_config() -> dict:
    path = config_path()

    if not path.is_file():
        fail(f"Missing configuration file: {path}")

    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"Invalid YAML in {path}: {exc}")

    if not isinstance(data, dict):
        fail("Configuration root must be a mapping.")

    return data


def operation_enabled(policy: dict | None, operation: str) -> bool:
    if policy is None:
        return False

    section = policy.get(operation, {})
    return isinstance(section, dict) and section.get("enabled", False) is True


def validate_config(data: dict) -> None:
    if data.get("version") != 1:
        fail("Configuration version must be 1.")

    defaults = data.get("defaults", {})
    if not isinstance(defaults, dict):
        fail("defaults must be a mapping.")

    layouts = data.get("layouts", {})
    if not isinstance(layouts, dict):
        fail("layouts must be a mapping.")

    known = set(discover_layouts())

    for name, policy in layouts.items():
        if not isinstance(name, str) or not LAYOUT_RE.fullmatch(name):
            fail(f"Invalid layout name in configuration: {name!r}")

        if name not in known:
            fail(
                f"Configured layout {name!r} has no primary "
                f"profiles/{name}/{name}-wsN.yaml files."
            )

        if not isinstance(policy, dict):
            fail(f"Policy for layout {name!r} must be a mapping.")

        enabled = policy.get("enabled", True)
        if not isinstance(enabled, bool):
            fail(f"Layout {name!r} enabled must be true or false.")

        inferred = inferred_workspace_count(name)
        declared = policy.get("workspace_count")

        if declared is not None:
            if (
                not isinstance(declared, int)
                or isinstance(declared, bool)
                or declared < 1
            ):
                fail(
                    f"Layout {name!r} workspace_count must be a positive integer."
                )

            if declared != inferred:
                fail(
                    f"Layout {name!r} workspace_count={declared} does not "
                    f"match {inferred} contiguous primary workspace file(s)."
                )

        for operation in OPERATIONS:
            section = policy.get(operation, {})

            if section is None:
                section = {}

            if not isinstance(section, dict):
                fail(f"Layout {name!r} {operation} policy must be a mapping.")

            operation_value = section.get("enabled", False)
            if not isinstance(operation_value, bool):
                fail(
                    f"Layout {name!r} {operation}.enabled "
                    "must be true or false."
                )

        if operation_enabled(policy, "reroute"):
            reroute = policy["reroute"]
            session = reroute.get("session")

            if not isinstance(session, str) or not session.strip():
                fail(
                    f"Layout {name!r} enables reroute but has no "
                    "reroute.session."
                )


def write_config(data: dict) -> None:
    path = config_path()
    rendered = yaml.safe_dump(
        data,
        sort_keys=False,
        default_flow_style=False,
        allow_unicode=True,
    )

    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        delete=False,
    ) as handle:
        handle.write(rendered)
        temporary_path = Path(handle.name)

    temporary_path.replace(path)


def layout_policy(data: dict, layout: str) -> dict | None:
    configured = data.get("layouts", {}).get(layout)
    if configured is None:
        return None

    if not isinstance(configured, dict):
        fail(f"Policy for layout {layout!r} must be a mapping.")

    return configured


def layout_enabled(policy: dict | None) -> bool:
    if policy is None:
        return True
    return policy.get("enabled", True) is True


def print_policy_summary(layout: str, policy: dict | None) -> None:
    enabled = layout_enabled(policy)
    active = [
        operation
        for operation in OPERATIONS
        if operation_enabled(policy, operation)
    ]

    state = "enabled" if enabled else "disabled"
    rendered = ",".join(active) if active else "none"
    configured = "configured" if policy is not None else "inferred"
    print(f"{layout}\t{configured}\t{state}\toperations={rendered}")


def command_list(args: argparse.Namespace) -> int:
    data = load_config()
    validate_config(data)

    if args.layout is None:
        for layout in discover_layouts():
            print_policy_summary(layout, layout_policy(data, layout))
        return 0

    require_known_layout(args.layout)
    policy = layout_policy(data, args.layout)
    count = inferred_workspace_count(args.layout)

    print(f"layout: {args.layout}")
    print(f"configured: {str(policy is not None).lower()}")
    print(f"enabled: {str(layout_enabled(policy)).lower()}")
    print(
        "workspace_count: "
        + str(policy.get("workspace_count", count) if policy else count)
    )
    print(f"workspace_count_source: {'config' if policy and 'workspace_count' in policy else 'inferred'}")
    print("operations:")
    for operation in OPERATIONS:
        print(f"  {operation}: {str(operation_enabled(policy, operation)).lower()}")

    if operation_enabled(policy, "reroute"):
        reroute = policy["reroute"]
        print(f"reroute.session: {reroute['session']}")

    print("workspaces: " + ",".join(map(str, discover_workspaces(args.layout))))
    return 0


def ensure_layout_policy(data: dict, layout: str) -> dict:
    layouts = data.setdefault("layouts", {})

    if not isinstance(layouts, dict):
        fail("layouts must be a mapping.")

    policy = layouts.setdefault(layout, {})

    if not isinstance(policy, dict):
        fail(f"Policy for layout {layout!r} must be a mapping.")

    return policy


def command_operation(args: argparse.Namespace) -> int:
    require_known_layout(args.layout)
    data = load_config()

    if data.get("version") != 1:
        fail("Configuration version must be 1.")

    policy = ensure_layout_policy(data, args.layout)
    section = policy.setdefault(args.operation, {})

    if not isinstance(section, dict):
        fail(
            f"Layout {args.layout!r} {args.operation} policy must be a mapping."
        )

    if args.action == "enable":
        if args.operation == "reroute":
            session = section.get("session")
            if not isinstance(session, str) or not session.strip():
                fail(
                    "Cannot enable reroute without "
                    "layouts.<name>.reroute.session."
                )

        if args.operation == "purge":
            section.setdefault("preserve_terminal_identities", True)

        section["enabled"] = True
    else:
        section["enabled"] = False

    validate_config(data)
    write_config(data)

    state = "enabled" if section["enabled"] else "disabled"
    print(f"{args.layout}: {args.operation} {state}")
    return 0


def command_validate(_: argparse.Namespace) -> int:
    data = load_config()
    validate_config(data)
    print(f"VALID: {config_path()}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ws-man-policy",
        description="Manage ws-man layout policy configuration.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate")
    validate.set_defaults(handler=command_validate)

    listing = subparsers.add_parser("list")
    listing.add_argument("layout", nargs="?")
    listing.set_defaults(handler=command_list)

    operation = subparsers.add_parser("operation")
    operation.add_argument("action", choices=("enable", "disable"))
    operation.add_argument("layout")
    operation.add_argument("operation", choices=OPERATIONS)
    operation.set_defaults(handler=command_operation)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return args.handler(args)


if __name__ == "__main__":
    raise SystemExit(main())
