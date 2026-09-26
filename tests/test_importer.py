from __future__ import annotations

from io import StringIO
from pathlib import Path
from shutil import copy2

from cosmic_workspace_steward.import_ct import main
from cosmic_workspace_steward.importer import import_ct_profiles


FIXTURE = Path(__file__).parent / "fixtures" / "importer" / "sysadmin-ws1.yaml"


def test_importer_produces_inactive_review_required_draft_without_writing(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sysadmin-ws1.yaml"
    copy2(FIXTURE, source)
    before = source.read_text(encoding="utf-8")

    draft = import_ct_profiles([source], draft_name="ct-review-draft")

    assert draft.document["version"] == 1
    assert draft.document["kind"] == "import-draft"
    assert draft.document["name"] == "ct-review-draft"
    assert draft.document["status"] == "inactive"
    assert draft.document["review_required"] is True
    assert draft.document["source_format"] == "ct-reference-profile-v1"
    assert source.read_text(encoding="utf-8") == before
    assert not list(tmp_path.glob("*.draft.yaml"))
    assert [item.code for item in draft.diagnostics] == [
        "review-command-and-match",
        "review-command-and-match",
    ]


def test_importer_preserves_ambiguous_source_data_for_human_review(
    tmp_path: Path,
) -> None:
    source = tmp_path / "sysadmin-ws1.yaml"
    copy2(FIXTURE, source)

    draft = import_ct_profiles([source], draft_name="ct-review-draft")

    profile = draft.document["source_profiles"][0]
    applications = profile["applications"]
    assert applications[0] == {
        "source_index": 0,
        "command": "spotify",
        "workspace": 1,
        "match": {"class": "Spotify"},
    }
    assert applications[1]["command"] == (
        "/usr/bin/librewolf --new-window https://example.test/"
    )
    assert applications[1]["match"] == {
        "class": "librewolf",
        "title": "Example",
    }


def test_importer_cli_prints_draft_only(tmp_path: Path) -> None:
    source = tmp_path / "sysadmin-ws1.yaml"
    copy2(FIXTURE, source)
    output = StringIO()
    errors = StringIO()

    exit_code = main(
        ["--name", "ct-review-draft", str(source)],
        stdout=output,
        stderr=errors,
    )

    assert exit_code == 0
    assert errors.getvalue() == ""
    assert "kind: import-draft" in output.getvalue()
    assert "status: inactive" in output.getvalue()
    assert "review_required: true" in output.getvalue()
    assert source.exists()


def test_importer_cli_requires_explicit_draft_name() -> None:
    output = StringIO()
    errors = StringIO()

    exit_code = main([], stdout=output, stderr=errors)

    assert exit_code == 2
    assert output.getvalue() == ""
    assert errors.getvalue().startswith("usage:\n")
