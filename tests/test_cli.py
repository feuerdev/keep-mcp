import json

import pytest

from server import cli


class DummyLabel:
    def __init__(self, label_id="l1", name="keep-mcp"):
        self.id = label_id
        self.name = name


class DummyLabels:
    def __init__(self):
        self._labels = []

    def add(self, label):
        self._labels.append(label)

    def remove(self, label):
        self._labels = [existing for existing in self._labels if existing.id != label.id]

    def all(self):
        return self._labels


class DummyCollaborators:
    def __init__(self):
        self._emails = []

    def all(self):
        return list(self._emails)

    def add(self, email):
        self._emails.append(email)

    def remove(self, email):
        self._emails = [value for value in self._emails if value != email]


class DummyBlobType:
    def __init__(self, value="IMAGE"):
        self.value = value


class DummyBlobInner:
    def __init__(self):
        self.type = DummyBlobType("IMAGE")


class DummyBlob:
    def __init__(self, blob_id="b1"):
        self.id = blob_id
        self.blob = DummyBlobInner()


class DummyItem:
    def __init__(self, item_id: str, text: str, checked: bool):
        self.id = item_id
        self.text = text
        self.checked = checked
        self.parent_item = None

    def delete(self):
        self.deleted = True


class DummyNote:
    def __init__(self, note_id="n1"):
        self.id = note_id
        self.title = "title"
        self.text = "text"
        self.pinned = False
        self.archived = False
        self.trashed = False
        self.type = type("T", (), {"value": "NOTE"})()
        self.color = type("C", (), {"value": "white"})()
        self.labels = DummyLabels()
        self.collaborators = DummyCollaborators()
        self.blobs = [DummyBlob()]
        self.deleted = False

    def delete(self):
        self.deleted = True

    def trash(self):
        self.trashed = True

    def untrash(self):
        self.trashed = False

    def undelete(self):
        self.deleted = False


class DummyList(DummyNote):
    def __init__(self, note_id="list1"):
        super().__init__(note_id)
        self.type = type("T", (), {"value": "LIST"})()
        self.items = []

    def add(self, text, checked=False):
        item = DummyItem(f"i{len(self.items)+1}", text, checked)
        self.items.append(item)
        return item

    def get(self, item_id):
        for item in self.items:
            if item.id == item_id:
                return item
        return None


class DummyKeep:
    def __init__(self):
        self.notes = {}
        self._labels = {"l1": DummyLabel("l1", "keep-mcp")}
        self.sync_calls = 0

    def sync(self):
        self.sync_calls += 1

    def find(self, **kwargs):
        self.last_find_kwargs = kwargs
        return list(self.notes.values())

    def get(self, note_id):
        return self.notes.get(note_id)

    def createNote(self, title=None, text=None):
        note = DummyNote("created")
        note.title = title
        note.text = text
        self.notes[note.id] = note
        return note

    def createList(self, title=None, items=None):
        note = DummyList("created_list")
        note.title = title
        if items:
            for text, checked in items:
                note.add(text, checked)
        self.notes[note.id] = note
        return note

    def findLabel(self, name):
        for label in self._labels.values():
            if label.name == name:
                return label
        return None

    def createLabel(self, name):
        label = DummyLabel("new", name)
        self._labels[label.id] = label
        return label

    def labels(self):
        return list(self._labels.values())

    def getLabel(self, label_id):
        return self._labels.get(label_id)

    def all(self):
        return list(self.notes.values())

    def deleteLabel(self, label_id):
        self._labels.pop(label_id, None)

    def getMediaLink(self, blob):
        return f"https://media/{blob.id}"


@pytest.fixture()
def keep(monkeypatch):
    keep = DummyKeep()
    keep.notes["n1"] = DummyNote("n1")
    keep.notes["n1"].labels.add(DummyLabel("l1", "keep-mcp"))
    keep.notes["list1"] = DummyList("list1")
    keep.notes["list1"].labels.add(DummyLabel("l1", "keep-mcp"))
    keep.notes["list1"].add("existing", checked=False)

    monkeypatch.setattr(cli, "get_client", lambda: keep)
    monkeypatch.setattr(cli.gkeepapi.node, "List", DummyList)
    monkeypatch.setattr(
        cli.gkeepapi.node,
        "ColorValue",
        lambda color: type("Color", (), {"value": color})(),
    )
    return keep


def test_find_forwards_filters(keep):
    result = json.loads(
        cli.find(
            query="q",
            labels=["l1"],
            colors=["red"],
            pinned=True,
            archived=False,
            trashed=False,
        )
    )
    assert keep.last_find_kwargs["query"] == "q"
    assert keep.last_find_kwargs["labels"] == ["l1"]
    assert [color.value for color in keep.last_find_kwargs["colors"]] == ["red"]
    assert isinstance(result, list)


def test_find_without_colors_passes_none(keep):
    cli.find(query="q")
    assert keep.last_find_kwargs["colors"] is None


def test_find_invalid_color_raises(keep, monkeypatch):
    def bad_color(_):
        raise ValueError("bad")

    monkeypatch.setattr(cli.gkeepapi.node, "ColorValue", bad_color)
    with pytest.raises(ValueError, match="Invalid color 'invalid'"):
        cli.find(colors=["invalid"])


def test_get_note(keep):
    data = json.loads(cli.get_note("n1"))
    assert data["id"] == "n1"


def test_create_note_labels_and_sync(keep):
    data = json.loads(cli.create_note("t", "body"))
    assert data["id"] == "created"
    assert keep.sync_calls == 1


def test_create_note_creates_label_when_missing(keep):
    keep._labels = {}
    data = json.loads(cli.create_note("t", "body"))
    assert data["labels"][0]["name"] == "keep-mcp"


def test_create_list_variants(keep):
    data = json.loads(cli.create_list("list"))
    assert data["id"] == "created_list"
    data_with_items = json.loads(
        cli.create_list("list", items=[{"text": "a", "checked": True}])
    )
    assert data_with_items["items"][0]["checked"] is True


def test_create_list_creates_label_when_missing(keep):
    keep._labels = {}
    data = json.loads(cli.create_list("list"))
    assert data["labels"][0]["name"] == "keep-mcp"


def test_update_note_updates_fields(keep):
    data = json.loads(cli.update_note("n1", title="new", text="changed"))
    assert data["title"] == "new"
    assert data["text"] == "changed"


def test_update_note_not_found_raises(keep):
    with pytest.raises(ValueError, match="not found"):
        cli.update_note("missing", title="x")


def test_list_item_roundtrip(keep):
    add = json.loads(cli.add_list_item("list1", "task", checked=True))
    item_id = add["item_id"]
    updated = json.loads(
        cli.update_list_item("list1", item_id, text="task2", checked=False)
    )
    assert any(item["id"] == item_id for item in updated["items"])


def test_update_list_item_missing_item_raises(keep):
    with pytest.raises(ValueError, match="not found"):
        cli.update_list_item("list1", "missing", text="x")


def test_delete_list_item_paths(keep):
    with pytest.raises(ValueError, match="not found"):
        cli.delete_list_item("list1", "missing")

    new_item_id = json.loads(cli.add_list_item("list1", "task"))["item_id"]
    data = json.loads(cli.delete_list_item("list1", new_item_id))
    assert "marked for deletion" in data["message"]


def test_list_item_requires_list_type(keep):
    with pytest.raises(ValueError, match="not a list"):
        cli.add_list_item("n1", "x")
    with pytest.raises(ValueError, match="not a list"):
        cli.update_list_item("n1", "i1", text="x")
    with pytest.raises(ValueError, match="not a list"):
        cli.delete_list_item("n1", "i1")


def test_set_note_color_validates(keep, monkeypatch):
    def bad_color(_):
        raise ValueError("bad")

    monkeypatch.setattr(cli.gkeepapi.node, "ColorValue", bad_color)
    with pytest.raises(ValueError, match="Invalid color"):
        cli.set_note_color("n1", "invalid")


def test_note_state_transitions(keep):
    assert json.loads(cli.set_note_color("n1", "red"))["color"] == "red"
    assert json.loads(cli.pin_note("n1", True))["pinned"] is True
    assert json.loads(cli.archive_note("n1", True))["archived"] is True
    assert json.loads(cli.trash_note("n1"))["trashed"] is True
    assert json.loads(cli.restore_note("n1"))["trashed"] is False


def test_delete_note_marks_deleted(keep):
    msg = json.loads(cli.delete_note("n1"))
    assert "marked for deletion" in msg["message"]


def test_label_crud_and_missing_label_errors(keep):
    labels = json.loads(cli.list_labels())
    assert labels

    created = json.loads(cli.create_label("other"))
    assert created["name"] == "other"
    message = json.loads(cli.delete_label(created["id"]))
    assert "marked for deletion" in message["message"]

    with pytest.raises(ValueError, match="Label with ID bad not found"):
        cli.delete_label("bad")
    with pytest.raises(ValueError, match="Label with ID bad not found"):
        cli.add_label_to_note("n1", "bad")
    with pytest.raises(ValueError, match="Label with ID bad not found"):
        cli.remove_label_from_note("n1", "bad")


def test_delete_label_safe_mode_guards(keep, monkeypatch):
    # Deleting the keep-mcp label is blocked in safe mode.
    with pytest.raises(ValueError, match="keep-mcp"):
        cli.delete_label("l1")

    # Deleting a label that is on an unmanaged note is also blocked in safe mode.
    unmanaged = DummyNote("unmanaged")  # no keep-mcp label
    shared = DummyLabel("shared", "shared-tag")
    keep._labels["shared"] = shared
    unmanaged.labels.add(shared)
    keep.notes["unmanaged"] = unmanaged
    with pytest.raises(ValueError, match="unmanaged"):
        cli.delete_label("shared")

    # UNSAFE_MODE bypasses both guards.
    monkeypatch.setenv("UNSAFE_MODE", "true")
    msg = json.loads(cli.delete_label("shared"))
    assert "marked for deletion" in msg["message"]


def test_label_add_remove(keep):
    keep._labels["l2"] = DummyLabel("l2", "other")
    add = json.loads(cli.add_label_to_note("n1", "l2"))
    assert any(label["id"] == "l2" for label in add["labels"])
    remove = json.loads(cli.remove_label_from_note("n1", "l2"))
    assert all(label["id"] != "l2" for label in remove["labels"])


def test_collaborator_list_add_remove(keep):
    before = json.loads(cli.list_note_collaborators("n1"))
    assert before == []

    data = json.loads(cli.add_note_collaborator("n1", "user@example.com"))
    assert "user@example.com" in data["collaborators"]
    after = json.loads(cli.remove_note_collaborator("n1", "user@example.com"))
    assert "user@example.com" not in after["collaborators"]


def test_list_note_media(keep):
    media = json.loads(cli.list_note_media("n1"))
    assert media[0]["media_link"].startswith("https://media/")


def test_modification_guard_blocks_when_unlabeled(keep, monkeypatch):
    keep.notes["n1"].labels = DummyLabels()
    monkeypatch.setattr(cli, "can_modify_note", lambda _: False)
    with pytest.raises(ValueError, match="cannot be modified"):
        cli.update_note("n1", title="x")


def test_main_runs_stdio_transport(monkeypatch):
    captured = {}

    def fake_run(*, transport):
        captured["transport"] = transport

    monkeypatch.setattr(cli.mcp, "run", fake_run)
    cli.main()
    assert captured["transport"] == "stdio"
