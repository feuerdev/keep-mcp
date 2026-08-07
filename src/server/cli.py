"""
MCP plugin for Google Keep integration.
Provides tools for interacting with Google Keep notes through MCP.
"""

import json
import re
from datetime import datetime, timezone
from itertools import islice
from typing import Any

import gkeepapi

try:
    from mcp.server import MCPServer
except ImportError:  # MCP SDK 1.x: FastMCP became MCPServer in 2.0
    from mcp.server.fastmcp import FastMCP as MCPServer

from .keep_api import (
    KEEP_MCP_LABEL,
    can_modify_note,
    get_client,
    has_keep_mcp_label,
    is_unsafe_mode,
    serialize_label,
    serialize_note,
)

mcp = MCPServer("keep")


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


def _parse_utc(value: str | None, param: str) -> datetime | None:
    if value is None:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(
            f"Invalid {param} '{value}': expected ISO 8601, "
            "e.g. 2026-07-29 or 2026-07-29T12:00:00Z"
        ) from exc
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None or value.tzinfo is not None:
        return value
    return value.replace(tzinfo=timezone.utc)


def _build_time_filter(
    created_after: datetime | None,
    created_before: datetime | None,
    updated_after: datetime | None,
    updated_before: datetime | None,
):
    if not any((created_after, created_before, updated_after, updated_before)):
        return None

    def within(note) -> bool:
        timestamps = getattr(note, "timestamps", None)
        created = _as_utc(getattr(timestamps, "created", None))
        updated = _as_utc(getattr(timestamps, "updated", None))
        if created_after and (created is None or created < created_after):
            return False
        if created_before and (created is None or created >= created_before):
            return False
        if updated_after and (updated is None or updated < updated_after):
            return False
        return not (updated_before and (updated is None or updated >= updated_before))

    return within


@mcp.tool()
def find(
    query: str = "",
    labels: list[str] | None = None,
    colors: list[str] | None = None,
    pinned: bool | None = None,
    archived: bool | None = False,
    trashed: bool = False,
    case_sensitive: bool = False,
    created_after: str | None = None,
    created_before: str | None = None,
    updated_after: str | None = None,
    updated_before: str | None = None,
    limit: int | None = None,
) -> str:
    """Find notes using text and optional filters.

    query matches title and text, case-insensitively unless case_sensitive
    is true. labels should be label IDs. colors should be ColorValue strings
    (e.g. DEFAULT, RED, CERULEAN). The date bounds accept ISO 8601 dates or
    datetimes, interpreted as UTC when no timezone is given (e.g. 2026-07-29
    or 2026-07-29T12:00:00Z); after-bounds are inclusive, before-bounds
    exclusive. limit caps the number of returned notes.
    """
    keep = get_client()
    normalized_colors = _normalize_colors(colors)

    search_query: str | re.Pattern = query
    if query and not case_sensitive:
        search_query = re.compile(re.escape(query), re.IGNORECASE)

    time_filter = _build_time_filter(
        _parse_utc(created_after, "created_after"),
        _parse_utc(created_before, "created_before"),
        _parse_utc(updated_after, "updated_after"),
        _parse_utc(updated_before, "updated_before"),
    )

    notes = keep.find(
        query=search_query,
        func=time_filter,
        labels=labels,
        colors=normalized_colors,
        pinned=pinned,
        archived=archived,
        trashed=trashed,
    )
    if limit is not None:
        notes = islice(notes, max(limit, 0))

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
        raise TypeError(f"Note with ID {note_id} is not a list")

    item = note.add(text=text, checked=checked)
    keep.sync()
    return json.dumps({"note_id": note.id, "item_id": item.id})


@mcp.tool()
def update_list_item(note_id: str, item_id: str, text: str | None = None, checked: bool | None = None) -> str:
    """Update checklist item text and/or checked state."""
    keep, note = _get_note_or_raise(note_id)
    _ensure_modifiable(note)

    if not isinstance(note, gkeepapi.node.List):
        raise TypeError(f"Note with ID {note_id} is not a list")

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
        raise TypeError(f"Note with ID {note_id} is not a list")

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
    """Set a note color. Valid values: DEFAULT (white), RED, ORANGE, YELLOW, GREEN, TEAL, BLUE, CERULEAN (dark blue), PURPLE, PINK, BROWN, GRAY."""
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
    label = keep.getLabel(label_id)
    if not label:
        raise ValueError(f"Label with ID {label_id} not found")
    if not is_unsafe_mode():
        if label.name == KEEP_MCP_LABEL:
            raise ValueError(
                f"Cannot delete the '{KEEP_MCP_LABEL}' label in safe mode: all notes managed "
                "by this server would become permanently unmodifiable. Set UNSAFE_MODE=true to override."
            )
        unmanaged = [
            n for n in keep.all()
            if any(lb.id == label_id for lb in n.labels.all()) and not has_keep_mcp_label(n)
        ]
        if unmanaged:
            raise ValueError(
                f"Cannot delete label '{label.name}' in safe mode: it is attached to "
                f"{len(unmanaged)} unmanaged note(s). Deleting it would silently modify "
                "those notes. Set UNSAFE_MODE=true to override."
            )
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
    if label.name == KEEP_MCP_LABEL and not is_unsafe_mode():
        raise ValueError(
            f"Cannot remove the '{KEEP_MCP_LABEL}' label in safe mode: the note would "
            "become permanently unmodifiable. Set UNSAFE_MODE=true to override."
        )

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
