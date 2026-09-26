"""Explicit review-only CT reference profile importer CLI."""
from __future__ import annotations

from pathlib import Path
import sys
from typing import Sequence, TextIO

import yaml

from .errors import ArtifactError
from .importer import import_ct_profiles


_USAGE = """usage:
  python -m cosmic_workspace_steward.import_ct --name DRAFT_NAME PROFILE.yaml [PROFILE.yaml ...]
"""


def main(
    argv: Sequence[str] | None = None,
    *,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    arguments = list(sys.argv[1:] if argv is None else argv)
    output = sys.stdout if stdout is None else stdout
    errors = sys.stderr if stderr is None else stderr

    if len(arguments) < 3 or arguments[0] != "--name":
        print(_USAGE.rstrip(), file=errors)
        return 2

    draft_name = arguments[1]
    source_paths = [Path(value) for value in arguments[2:]]
    try:
        draft = import_ct_profiles(source_paths, draft_name=draft_name)
    except ArtifactError as exc:
        print(f"error: {exc}", file=errors)
        return 2

    print(
        yaml.safe_dump(
            dict(draft.document),
            allow_unicode=True,
            default_flow_style=False,
            sort_keys=True,
        ).rstrip("\n"),
        file=output,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
