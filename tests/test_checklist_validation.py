"""Exercise checklist validation with real gkeepapi objects, without network calls."""

import json
from unittest.mock import Mock

import gkeepapi
import pytest

from server import cli


@pytest.fixture
def offline_keep(monkeypatch):
    keep = gkeepapi.Keep()
    monkeypatch.setattr(keep, "sync", Mock())
    monkeypatch.setattr(cli, "get_client", lambda: keep)
    monkeypatch.setenv("UNSAFE_MODE", "false")
    return keep


@pytest.mark.parametrize("checked", ["false", "true", 0, 1, None])
def test_create_list_rejects_non_boolean_checked_without_creating_note(offline_keep, checked):
    with pytest.raises(TypeError, match="checked.*boolean"):
        cli.create_list("Tasks", [{"text": "Buy milk", "checked": checked}])
    assert list(offline_keep.all()) == []
    offline_keep.sync.assert_not_called()


def test_create_list_preserves_boolean_checked_and_default(offline_keep):
    result = json.loads(cli.create_list("Tasks", [
        {"text": "Unchecked", "checked": False},
        {"text": "Checked", "checked": True},
        {"text": "Default"},
    ]))
    assert {item["text"]: item["checked"] for item in result["items"]} == {
        "Unchecked": False, "Checked": True, "Default": False,
    }


def test_update_list_text_does_not_partially_change_title(offline_keep):
    note = offline_keep.createList("Original", [("Buy milk", False)])
    note.labels.add(offline_keep.createLabel("keep-mcp"))
    with pytest.raises(ValueError, match="checklist.*item"):
        cli.update_note(note.id, title="Changed", text="Replacement")
    assert note.title == "Original"
    assert [item.text for item in note.items] == ["Buy milk"]
    offline_keep.sync.assert_not_called()


def test_update_list_title_remains_supported(offline_keep):
    note = offline_keep.createList("Original", [("Buy milk", False)])
    note.labels.add(offline_keep.createLabel("keep-mcp"))
    result = json.loads(cli.update_note(note.id, title="Changed"))
    assert result["title"] == "Changed"
    assert result["items"][0]["text"] == "Buy milk"
