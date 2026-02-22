from types import SimpleNamespace

from server.keep_api import can_modify_note, serialize_note


class DummyLabels:
    def __init__(self, labels):
        self._labels = labels

    def all(self):
        return self._labels


class DummyCollaborators:
    def __init__(self, emails):
        self._emails = emails

    def all(self):
        return self._emails


class DummyBlobType:
    def __init__(self, value):
        self.value = value


class DummyBlobNode:
    def __init__(self, blob_id, blob_type):
        self.id = blob_id
        self.blob = SimpleNamespace(type=DummyBlobType(blob_type))


class DummyNote:
    def __init__(self):
        self.id = "n1"
        self.title = "title"
        self.text = "text"
        self.type = SimpleNamespace(value="NOTE")
        self.pinned = False
        self.archived = False
        self.trashed = False
        self.color = SimpleNamespace(value="white")
        self.labels = DummyLabels([SimpleNamespace(id="l1", name="keep-mcp")])
        self.collaborators = DummyCollaborators(["alice@example.com"])
        self.blobs = [DummyBlobNode("b1", "IMAGE")]


class DummyListNote(DummyNote):
    def __init__(self):
        super().__init__()
        self.items = [
            SimpleNamespace(
                id="i1",
                text="item",
                checked=False,
                parent_item=None,
            )
        ]


def test_serialize_note_for_note_type():
    data = serialize_note(DummyNote())
    assert data["id"] == "n1"
    assert data["labels"][0]["name"] == "keep-mcp"
    assert data["collaborators"] == ["alice@example.com"]
    assert data["media"][0]["type"] == "IMAGE"
    assert "items" not in data


def test_serialize_note_for_list_type():
    data = serialize_note(DummyListNote())
    assert data["items"][0]["id"] == "i1"


def test_can_modify_note_respects_label(monkeypatch):
    monkeypatch.delenv("UNSAFE_MODE", raising=False)
    assert can_modify_note(DummyNote()) is True


def test_can_modify_note_respects_unsafe_mode(monkeypatch):
    monkeypatch.setenv("UNSAFE_MODE", "true")
    note = DummyNote()
    note.labels = DummyLabels([])
    assert can_modify_note(note) is True


def test_can_modify_note_false_without_label_or_unsafe(monkeypatch):
    monkeypatch.delenv("UNSAFE_MODE", raising=False)
    note = DummyNote()
    note.labels = DummyLabels([])
    assert can_modify_note(note) is False
