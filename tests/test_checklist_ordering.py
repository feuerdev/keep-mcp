"""Ordering and replacement against real gkeepapi nodes, without a Google account."""

from unittest.mock import Mock

import anyio
import gkeepapi
import pytest
from mcp.server.mcpserver.exceptions import ToolError

from server import cli, keep_api


@pytest.fixture
def keep(monkeypatch):
    keep = gkeepapi.Keep()
    monkeypatch.setattr(keep, "sync", Mock())
    monkeypatch.setattr(cli, "get_client", lambda: keep)
    monkeypatch.setenv("UNSAFE_MODE", "false")
    return keep


@pytest.fixture
def checklist(keep):
    note = keep.createList("Tasks", [("First", False), ("Second", True), ("Third", False)])
    note.labels.add(keep.createLabel("keep-mcp"))
    # gkeepapi's default additions need not be in input order.
    for index, item in enumerate(note.children):
        item.sort = (3 - index) * note.SORT_DELTA
    return note


def snapshot(note):
    return [(item.id, item.text, item.checked, item.sort, item.deleted) for item in note.items]


def restored_note(keep, note):
    restored = gkeepapi.Keep()
    restored.restore(keep.dump())
    return restored.get(note.id)


def test_bulk_order_survives_serialization_and_preserves_items(keep, checklist):
    original = snapshot(checklist)
    ids = [item[0] for item in original]
    order = [ids[2], ids[0], ids[1]]
    result = cli.reorder_list_items(checklist.id, order)
    assert [item["id"] for item in result["items"]] == order
    restored = restored_note(keep, checklist)
    assert [item.id for item in restored.items] == order
    assert {(i.id, i.text, i.checked) for i in restored.items} == {i[:3] for i in original}
    assert all(i.parent_item is None for i in restored.items)
    keep.sync.assert_called_once_with()


@pytest.mark.parametrize("source,position,expected", [
    (2, 0, [2, 0, 1]), (0, 2, [1, 2, 0]), (0, 1, [1, 0, 2]),
])
def test_move_uses_final_zero_based_position(keep, checklist, source, position, expected):
    ids = [i.id for i in checklist.items]
    result = cli.move_list_item(checklist.id, ids[source], position)
    assert [i["id"] for i in result["items"]] == [ids[index] for index in expected]
    assert [i.id for i in restored_note(keep, checklist).items] == [ids[index] for index in expected]
    keep.sync.assert_called_once_with()


@pytest.mark.parametrize("tool", ["move_list_item", "reorder_list_items"])
def test_unchanged_order_does_not_dirty_items_or_sync(keep, checklist, tool):
    # Model a clean tree fetched from Google, including all child timestamps.
    checklist.save()
    for item in checklist.items:
        item.save()
    before = keep.dump()
    ids = [item.id for item in checklist.items]
    if tool == "move_list_item":
        result = cli.move_list_item(checklist.id, ids[1], 1)
    else:
        result = cli.reorder_list_items(checklist.id, ids)
    assert [item["id"] for item in result["items"]] == ids
    assert keep.dump() == before
    assert not checklist.dirty
    assert not any(item.dirty for item in checklist.items)
    keep.sync.assert_not_called()


@pytest.mark.parametrize("bad_order", ["duplicate", "missing", "unknown", "empty", "foreign", "deleted"])
def test_bad_bulk_order_leaves_tree_unchanged(keep, checklist, bad_order):
    ids = [i.id for i in checklist.items]
    other = keep.createList("Other", [("Foreign", False)])
    deleted = checklist.add("Deleted")
    deleted.delete()
    orders = {
        "duplicate": [ids[0], ids[0], ids[2]], "missing": ids[:-1],
        "unknown": [*ids[:-1], "missing"], "empty": [],
        "foreign": [*ids[:-1], other.items[0].id], "deleted": [*ids[:-1], deleted.id],
    }
    before = snapshot(checklist)
    with pytest.raises(ToolError):
        cli.reorder_list_items(checklist.id, orders[bad_order])
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()


@pytest.mark.parametrize("position", [-1, 3, True, 1.5, "1"])
def test_bad_move_position_leaves_tree_unchanged(keep, checklist, position):
    before = snapshot(checklist)
    with pytest.raises(ToolError, match="position"):
        anyio.run(cli.mcp.call_tool, "move_list_item", {
            "note_id": checklist.id, "item_id": checklist.items[0].id, "position": position,
        })
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()


def test_move_unknown_id_leaves_tree_unchanged(keep, checklist):
    before = snapshot(checklist)
    with pytest.raises(ToolError, match="not found"):
        cli.move_list_item(checklist.id, "missing", 0)
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()


def test_move_on_empty_list_reports_missing_item(keep):
    note = keep.createList("Empty")
    note.labels.add(keep.createLabel("keep-mcp"))
    with pytest.raises(ToolError, match="List item with ID missing not found"):
        cli.move_list_item(note.id, "missing", 0)
    assert note.items == []
    keep.sync.assert_not_called()


def invoke(tool, note):
    if tool == "move_list_item":
        return cli.move_list_item(note.id, note.items[0].id if hasattr(note, "items") else "missing", 1)
    if tool == "reorder_list_items":
        return cli.reorder_list_items(note.id, [i.id for i in reversed(note.items)] if hasattr(note, "items") else [])
    return cli.replace_list_items(note.id, [{"text": "New"}])


@pytest.mark.parametrize("tool", ["move_list_item", "reorder_list_items", "replace_list_items"])
def test_tools_reject_indentation_without_mutation(keep, checklist, tool):
    parent, child, _ = checklist.items
    parent.indent(child)
    before = snapshot(checklist)
    with pytest.raises(ToolError, match="Indented"):
        invoke(tool, checklist)
    assert snapshot(checklist) == before
    assert child.parent_item is parent
    keep.sync.assert_not_called()


@pytest.mark.parametrize("tool", ["move_list_item", "reorder_list_items", "replace_list_items"])
def test_tools_enforce_safety_and_list_type(keep, checklist, monkeypatch, tool):
    checklist.labels.remove(checklist.labels.all()[0])
    before = snapshot(checklist)
    with pytest.raises(ToolError, match="cannot be modified"):
        invoke(tool, checklist)
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()

    monkeypatch.setenv("UNSAFE_MODE", "true")
    note = keep.createNote("Plain", "Text")
    with pytest.raises(ToolError, match="not a list"):
        invoke(tool, note)
    keep.sync.assert_not_called()
    invoke(tool, checklist)
    keep.sync.assert_called_once_with()


@pytest.mark.parametrize("tool,args", [
    (cli.move_list_item, ("missing", 0)), (cli.reorder_list_items, ([],)),
    (cli.replace_list_items, ([],)),
])
def test_missing_note(keep, tool, args):
    with pytest.raises(ToolError, match="not found"):
        tool("missing", *args)
    keep.sync.assert_not_called()


def test_replacement_preserves_metadata_and_uses_new_ids(keep, checklist):
    checklist.pinned = True
    checklist.archived = True
    checklist.color = gkeepapi.node.ColorValue.Red
    checklist.labels.add(keep.createLabel("Personal"))
    checklist.collaborators.add("person@example.com")
    old_items = list(checklist.items)
    metadata = {k: v for k, v in cli.serialize_note(checklist).items() if k not in ("items", "text", "updated")}
    result = cli.replace_list_items(checklist.id, [{"text": "A", "checked": True}, {"text": "B"}])
    assert [(i["text"], i["checked"]) for i in result["items"]] == [("A", True), ("B", False)]
    assert not {i.id for i in old_items} & {i["id"] for i in result["items"]}
    assert all(i.deleted for i in old_items)
    assert {k: result[k] for k in metadata} == metadata
    assert [(i.text, i.checked) for i in restored_note(keep, checklist).items] == [("A", True), ("B", False)]
    keep.sync.assert_called_once_with()


def test_empty_replacement_and_empty_order(keep, checklist):
    assert cli.replace_list_items(checklist.id, [])["items"] == []
    keep.sync.assert_called_once_with()
    keep.sync.reset_mock()
    assert cli.reorder_list_items(checklist.id, [])["items"] == []
    keep.sync.assert_not_called()
    with pytest.raises(ToolError, match="not found"):
        cli.move_list_item(checklist.id, "missing", 0)
    keep.sync.assert_not_called()


@pytest.mark.parametrize("invalid", [
    {"text": "Bad", "checked": "false"}, {"text": "Bad", "checked": 1},
    {"text": "Bad", "checked": None}, {"checked": True}, {"text": None},
    {"text": 42}, {"text": "Child", "parent_item_id": "parent"},
])
def test_replacement_validates_all_items_before_mutation(keep, checklist, invalid):
    before = snapshot(checklist)
    with pytest.raises(ToolError):
        anyio.run(cli.mcp.call_tool, "replace_list_items", {
            "note_id": checklist.id, "items": [{"text": "Valid"}, invalid],
        })
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()
    # A later successful mutation must not flush any rejected replacement.
    cli.pin_note(checklist.id, True)
    keep.sync.assert_called_once_with()
    assert [(i.text, i.checked) for i in checklist.items] == [(i[1], i[2]) for i in before]


def test_sync_failure_invalidates_shared_client(keep, checklist, monkeypatch):
    monkeypatch.setattr(keep_api, "_keep_client", keep)
    keep.sync.side_effect = RuntimeError("sync failed")
    with pytest.raises(RuntimeError, match="sync failed"):
        cli.replace_list_items(checklist.id, [{"text": "New"}])
    assert keep_api._keep_client is None


def test_mcp_registration_and_calls(keep, checklist):
    async def exercise():
        tools = {tool.name: tool for tool in await cli.mcp.list_tools()}
        for name in ("move_list_item", "reorder_list_items", "replace_list_items"):
            assert name in tools
            assert tools[name].annotations.destructive_hint is True
        assert tools["move_list_item"].input_schema["properties"]["position"]["type"] == "integer"
        ids = [i.id for i in checklist.items]
        await cli.mcp.call_tool("reorder_list_items", {"note_id": checklist.id, "item_ids": ids[::-1]})
        assert [i.id for i in checklist.items] == ids[::-1]
        await cli.mcp.call_tool("move_list_item", {"note_id": checklist.id, "item_id": ids[0], "position": 0})
        assert checklist.items[0].id == ids[0]
        await cli.mcp.call_tool("replace_list_items", {"note_id": checklist.id, "items": [{"text": "MCP", "checked": True}]})
        assert [(i.text, i.checked) for i in checklist.items] == [("MCP", True)]

    anyio.run(exercise)


@pytest.mark.parametrize("tool,payload", [
    ("move_list_item", {"item_id": "any", "position": True}),
    ("replace_list_items", {"items": [{"text": "Bad", "checked": "false"}]}),
    ("replace_list_items", {"items": [{"text": "Child", "parent_item_id": "parent"}]}),
])
def test_mcp_rejects_invalid_types_without_mutation(keep, checklist, tool, payload):
    before = snapshot(checklist)
    with pytest.raises(ToolError):
        anyio.run(cli.mcp.call_tool, tool, {"note_id": checklist.id, **payload})
    assert snapshot(checklist) == before
    keep.sync.assert_not_called()
