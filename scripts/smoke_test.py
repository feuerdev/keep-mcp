"""Basic real-account smoke test for keep-mcp server logic.

Usage:
  GOOGLE_EMAIL=... GOOGLE_MASTER_TOKEN=... python scripts/smoke_test.py

This script performs a lifecycle against Google Keep:
- create note
- update note
- set color
- pin/unpin
- archive/unarchive
- trash/restore
- delete
- create list + add/update/delete list items
- label CRUD and association

It is intended for manual verification, not CI.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from server import cli


def main() -> None:
    if not os.getenv("GOOGLE_EMAIL") or not os.getenv("GOOGLE_MASTER_TOKEN"):
        raise SystemExit("Set GOOGLE_EMAIL and GOOGLE_MASTER_TOKEN before running smoke test")

    # --- Note lifecycle ---
    print("Creating note...")
    created = cli.create_note(title="keep-mcp smoke", text="hello")
    note_id = created["id"]
    print("Created:", note_id)

    print("Updating note...")
    updated = cli.update_note(note_id, title="keep-mcp smoke updated", text="world")
    assert updated["title"] == "keep-mcp smoke updated"

    print("Setting color...")
    colored = cli.set_note_color(note_id, "RED")
    assert colored["color"] == "RED"
    # Reset to default
    cli.set_note_color(note_id, "DEFAULT")

    print("Pin/unpin...")
    assert cli.pin_note(note_id, True)["pinned"] is True
    assert cli.pin_note(note_id, False)["pinned"] is False

    print("Archive/unarchive...")
    assert cli.archive_note(note_id, True)["archived"] is True
    assert cli.archive_note(note_id, False)["archived"] is False

    print("Trash/restore...")
    assert cli.trash_note(note_id)["trashed"] is True
    restored = cli.restore_note(note_id)
    assert restored["trashed"] is False

    print("Deleting note...")
    delete_msg = cli.delete_note(note_id)
    assert "marked for deletion" in delete_msg["message"]

    # --- Checklist lifecycle ---
    print("Creating list...")
    lst = cli.create_list("keep-mcp smoke list", items=[{"text": "item1", "checked": False}])
    list_id = lst["id"]
    print("List created:", list_id)
    assert lst["items"][0]["text"] == "item1"

    print("Adding list item...")
    added = cli.add_list_item(list_id, "item2", checked=False)
    item_id = added["item_id"]

    print("Updating list item...")
    updated_list = cli.update_list_item(list_id, item_id, text="item2 edited", checked=True)
    edited = next(i for i in updated_list["items"] if i["id"] == item_id)
    assert edited["text"] == "item2 edited"
    assert edited["checked"] is True

    print("Deleting list item...")
    del_item = cli.delete_list_item(list_id, item_id)
    assert "marked for deletion" in del_item["message"]

    print("Deleting list note...")
    cli.delete_note(list_id)

    # --- Label lifecycle ---
    print("Creating label...")
    label = cli.create_label("keep-mcp-smoke-label")
    label_id = label["id"]
    print("Label created:", label_id)

    print("Listing labels (should include new label)...")
    labels = cli.list_labels()
    assert any(lb["id"] == label_id for lb in labels)

    print("Creating note for label association...")
    note_for_label = cli.create_note(title="label test")
    nfl_id = note_for_label["id"]

    print("Adding label to note...")
    labeled = cli.add_label_to_note(nfl_id, label_id)
    assert any(lb["id"] == label_id for lb in labeled["labels"])

    print("Removing label from note...")
    unlabeled = cli.remove_label_from_note(nfl_id, label_id)
    assert all(lb["id"] != label_id for lb in unlabeled["labels"])

    print("Deleting label...")
    del_label = cli.delete_label(label_id)
    assert "marked for deletion" in del_label["message"]

    print("Cleaning up label test note...")
    cli.delete_note(nfl_id)

    # --- find() ---
    print("Testing find()...")
    results = cli.find(query="keep-mcp")
    assert isinstance(results, list)

    print("Smoke test finished successfully")


if __name__ == "__main__":
    main()
