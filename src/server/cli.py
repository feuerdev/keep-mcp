"""
MCP plugin for Google Keep integration.
Provides tools for interacting with Google Keep notes through MCP.
"""

import json
from typing import Any

import gkeepapi
from mcp.server.fastmcp import FastMCP

from .keep_api import can_modify_note, get_client, serialize_label, serialize_note

mcp = FastMCP("keep")


def _get_note_or_raise(note_id: str):
    keep = get_client()
    note = keep.get(note_id)
    if not note:
        raise ValueError(f"Note with ID {note_id} not found")
    return keep, note


def _ensure_modifiable(note):
    if not can_modify_note(note):
        raise ValueError(
            f"Note with ID {note.id} cannot be modified "
            "(missing keep-mcp label and UNSAFE_MODE is not enabled)"
        )


def _normalize_colors(colors: list[str] | None):
    if colors is None:
        return None

    normalized_colors = []
    for color in colors:
        try:
            normalized_colors.append(gkeepapi.node.ColorValue(color))
        except ValueError as exc:
            raise ValueError(f"Invalid color '{color}'") from exc

    return normalized_colors


@mcp.tool()
def find(
    query: str = "",
    labels: list[str] | None = None,
    colors: list[str] | None = None,
    pinned: bool | None = None,
    archived: bool | None = False,
    trashed: bool = False,
) -> str:
    """Find notes using text and optional filters."""
    keep = get_client()
    normalized_colors = _normalize_colors(colors)
    notes = keep.find(
        query=query,
        labels=labels,
        colors=normalized_colors,
        pinned=pinned,
        archived=archived,
        trashed=trashed,
    )

    notes_data = [serialize_note(note) for note in notes]
    return json.dumps(notes_data)


@mcp.tool()
def get_note(note_id: str) -> str:
    """Get a note by ID."""
    _, note = _get_note_or_raise(note_id)
    return json.dumps(serialize_note(note))


@mcp.tool()
def create_note(title: str | None = None, text: str | None = None) -> str:
    """Create a new note with title and text."""
    keep = get_client()
    note = keep.createNote(title=title, text=text)

    label = keep.findLabel("keep-mcp")
    if not label:
        label = keep.createLabel("keep-mcp")

    note.labels.add(label)
    keep.sync()

    return json.dumps(serialize_note(note))


@mcp.tool()
def create_list(title: str | None = None, items: list[dict[str, Any]] | None = None) -> str:
    """
    Create a new checklist note.

    items should be objects like: {"text": "task", "checked": false}
    """
    keep = get_client()
    formatted_items = None
    if items:
        formatted_items = [
            (item.get("text", ""), bool(item.get("checked", False))) for item in items
        ]

    note = keep.createList(title=title, items=formatted_items)

    label = keep.findLabel("keep-mcp")
    if not label:
        label = keep.createLabel("keep-mcp")
    note.labels.add(label)

    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def add_list_item(note_id: str, text: str, checked: bool = False) -> str:
    """Add an item to a checklist note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    if not isinstance(note, gkeepapi.node.List):
        raise ValueError(f"Note with ID {note_id} is not a list")

    item = note.add(text=text, checked=checked)
    keep.sync()
    return json.dumps({"note_id": note.id, "item_id": item.id})


@mcp.tool()
def update_list_item(note_id: str, item_id: str, text: str | None = None, checked: bool | None = None) -> str:
    """Update checklist item text and/or checked state."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    if not isinstance(note, gkeepapi.node.List):
        raise ValueError(f"Note with ID {note_id} is not a list")

    item = note.get(item_id)
    if not item:
        raise ValueError(f"List item with ID {item_id} not found")

    if text is not None:
        item.text = text
    if checked is not None:
        item.checked = checked

    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def delete_list_item(note_id: str, item_id: str) -> str:
    """Delete a checklist item."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    if not isinstance(note, gkeepapi.node.List):
        raise ValueError(f"Note with ID {note_id} is not a list")

    item = note.get(item_id)
    if not item:
        raise ValueError(f"List item with ID {item_id} not found")

    item.delete()
    keep.sync()
    return json.dumps({"message": f"List item {item_id} marked for deletion"})


@mcp.tool()
def update_note(note_id: str, title: str | None = None, text: str | None = None) -> str:
    """Update a note's properties."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    if title is not None:
        note.title = title
    if text is not None:
        note.text = text

    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def set_note_color(note_id: str, color: str) -> str:
    """Set a note color (e.g. white, red, orange, yellow, green, teal, blue, darkblue, purple, pink, brown, gray)."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    try:
        note.color = gkeepapi.node.ColorValue(color)
    except ValueError as exc:
        raise ValueError(f"Invalid color '{color}'") from exc

    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def pin_note(note_id: str, pinned: bool = True) -> str:
    """Pin or unpin a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.pinned = pinned
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def archive_note(note_id: str, archived: bool = True) -> str:
    """Archive or unarchive a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.archived = archived
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def trash_note(note_id: str) -> str:
    """Move a note to trash."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.trash()
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def restore_note(note_id: str) -> str:
    """Restore a trashed/deleted note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.untrash()
    note.undelete()
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def delete_note(note_id: str) -> str:
    """Delete a note (mark for deletion)."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.delete()
    keep.sync()
    return json.dumps({"message": f"Note {note_id} marked for deletion"})


@mcp.tool()
def list_labels() -> str:
    """List all labels."""
    keep = get_client()
    return json.dumps([serialize_label(label) for label in keep.labels()])


@mcp.tool()
def create_label(name: str) -> str:
    """Create a label."""
    keep = get_client()
    label = keep.createLabel(name)
    keep.sync()
    return json.dumps(serialize_label(label))


@mcp.tool()
def delete_label(label_id: str) -> str:
    """Delete a label by ID."""
    keep = get_client()
    keep.deleteLabel(label_id)
    keep.sync()
    return json.dumps({"message": f"Label {label_id} marked for deletion"})


@mcp.tool()
def add_label_to_note(note_id: str, label_id: str) -> str:
    """Add a label to a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    label = keep.getLabel(label_id)
    if not label:
        raise ValueError(f"Label with ID {label_id} not found")

    note.labels.add(label)
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def remove_label_from_note(note_id: str, label_id: str) -> str:
    """Remove a label from a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    label = keep.getLabel(label_id)
    if not label:
        raise ValueError(f"Label with ID {label_id} not found")

    note.labels.remove(label)
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def list_note_collaborators(note_id: str) -> str:
    """List collaborator emails for a note."""
    _, note = _get_note_or_raise(note_id)
    return json.dumps(list(note.collaborators.all()))


@mcp.tool()
def add_note_collaborator(note_id: str, email: str) -> str:
    """Add a collaborator email to a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.collaborators.add(email)
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def remove_note_collaborator(note_id: str, email: str) -> str:
    """Remove a collaborator email from a note."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    note.collaborators.remove(email)
    keep.sync()
    return json.dumps(serialize_note(note))


@mcp.tool()
def list_note_media(note_id: str) -> str:
    """List note media blobs and direct media links when available."""
    keep, note = _get_note_or_raise(note_id)

    media = []
    for blob in note.blobs:
        media.append(
            {
                "blob_id": blob.id,
                "type": blob.blob.type.value if blob.blob and blob.blob.type else None,
                "media_link": keep.getMediaLink(blob),
            }
        )

    return json.dumps(media)


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
