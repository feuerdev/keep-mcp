"""Basic real-account smoke test for keep-mcp server logic.

Usage:
  GOOGLE_EMAIL=... GOOGLE_MASTER_TOKEN=... python scripts/smoke_test.py

This script performs a minimal lifecycle against Google Keep:
- create note
- update note
- pin/unpin
- archive/unarchive
- trash/restore
- delete

It is intended for manual verification, not CI.
"""

import json
import os

from server import cli


def main() -> None:
    if not os.getenv("GOOGLE_EMAIL") or not os.getenv("GOOGLE_MASTER_TOKEN"):
        raise SystemExit("Set GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN before running smoke test")

    print("Creating note...")
    created = json.loads(cli.create_note(title="keep-mcp smoke", text="hello"))
    note_id = created["id"]
    print("Created:", note_id)

    print("Updating note...")
    updated = json.loads(cli.update_note(note_id, title="keep-mcp smoke updated", text="world"))
    assert updated["title"] == "keep-mcp smoke updated"

    print("Pin/unpin...")
    assert json.loads(cli.pin_note(note_id, True))["pinned"] is True
    assert json.loads(cli.pin_note(note_id, False))["pinned"] is False

    print("Archive/unarchive...")
    assert json.loads(cli.archive_note(note_id, True))["archived"] is True
    assert json.loads(cli.archive_note(note_id, False))["archived"] is False

    print("Trash/restore...")
    assert json.loads(cli.trash_note(note_id))["trashed"] is True
    restored = json.loads(cli.restore_note(note_id))
    assert restored["trashed"] is False

    print("Deleting note...")
    delete_msg = json.loads(cli.delete_note(note_id))
    assert "marked for deletion" in delete_msg["message"]

    print("Smoke test finished successfully")


if __name__ == "__main__":
    main()
