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
        self._emails = [e for e in self._emails if e != email]


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
        item = type("Item", (), {"id": f"i{len(self.items)+1}", "text": text, "checked": checked, "parent_item": None})()
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
        self.labels = {"l1": DummyLabel("l1", "keep-mcp")}
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
        for label in self.labels.values():
            if label.name == name:
                return label
        return None

    def createLabel(self, name):
        label = DummyLabel("new", name)
        self.labels[label.id] = label
        return label

    def labels(self):
        return list(self.labels.values())

    def getLabel(self, label_id):
        return self.labels.get(label_id)

    def deleteLabel(self, label_id):
        self.labels.pop(label_id, None)

    def getMediaLink(self, blob):
        return f"https://media/{blob.id}"


@pytest.fixture()
def keep(monkeypatch):
    keep = DummyKeep()
    keep.notes["n1"] = DummyNote("n1")
    keep.notes["n1"].labels.add(DummyLabel("l1", "keep-mcp"))
    keep.notes["list1"] = DummyList("list1")
    keep.notes["list1"].labels.add(DummyLabel("l1", "keep-mcp"))

    monkeypatch.setattr(cli, "get_client", lambda: keep)
    monkeypatch.setattr(cli.gkeepapi.node, "List", DummyList)
    monkeypatch.setattr(cli.gkeepapi.node, "ColorValue", lambda c: type("Color", (), {"value": c})())
    return keep


def test_find_forwards_filters(keep):
    result = json.loads(cli.find(query="q", labels=["l1"], colors=["red"], pinned=True, archived=False, trashed=False))
    assert keep.last_find_kwargs["query"] == "q"
    assert keep.last_find_kwargs["labels"] == ["l1"]
    assert isinstance(result, list)


def test_create_note_labels_and_sync(keep):
    data = json.loads(cli.create_note("t", "body"))
    assert data["id"] == "created"
    assert keep.sync_calls == 1


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
    updated = json.loads(cli.update_list_item("list1", item_id, text="task2", checked=False))
    assert any(i["id"] == item_id for i in updated["items"])


def test_list_item_requires_list_type(keep):
    with pytest.raises(ValueError, match="not a list"):
        cli.add_list_item("n1", "x")


def test_set_note_color_validates(keep, monkeypatch):
    def bad_color(_):
        raise ValueError("bad")

    monkeypatch.setattr(cli.gkeepapi.node, "ColorValue", bad_color)
    with pytest.raises(ValueError, match="Invalid color"):
        cli.set_note_color("n1", "invalid")


def test_label_add_remove(keep):
    keep.labels["l2"] = DummyLabel("l2", "other")
    add = json.loads(cli.add_label_to_note("n1", "l2"))
    assert any(lbl["id"] == "l2" for lbl in add["labels"])
    remove = json.loads(cli.remove_label_from_note("n1", "l2"))
    assert all(lbl["id"] != "l2" for lbl in remove["labels"])


def test_collaborator_add_remove(keep):
    data = json.loads(cli.add_note_collaborator("n1", "user@example.com"))
    assert "user@example.com" in data["collaborators"]
    after = json.loads(cli.remove_note_collaborator("n1", "user@example.com"))
    assert "user@example.com" not in after["collaborators"]


def test_list_note_media(keep):
    media = json.loads(cli.list_note_media("n1"))
    assert media[0]["media_link"].startswith("https://media/")


def test_delete_note_marks_deleted(keep):
    msg = json.loads(cli.delete_note("n1"))
    assert "marked for deletion" in msg["message"]


def test_modification_guard_blocks_when_unlabeled(keep, monkeypatch):
    keep.notes["n1"].labels = DummyLabels()
    monkeypatch.setattr(cli, "can_modify_note", lambda _: False)
    with pytest.raises(ValueError, match="cannot be modified"):
        cli.update_note("n1", title="x")
