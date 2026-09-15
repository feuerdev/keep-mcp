from server import keep_api


class DummyKeep:
    def __init__(self):
        self.auth_calls = []

    def sync(self):
        pass

    def authenticate(self, email, token):
        self.auth_calls.append((email, token))


def test_get_client_authenticates_and_caches(monkeypatch):
    keep_api._keep_client = None
    created = DummyKeep()

    monkeypatch.setattr(keep_api, "load_dotenv", lambda: None)
    monkeypatch.setattr(keep_api.os, "getenv", lambda key: {
        "GOOGLE_EMAIL": "user@example.com",
        "GOOGLE_MASTER_TOKEN": "token",
    }.get(key))
    monkeypatch.setattr(keep_api.gkeepapi, "Keep", lambda: created)

    first = keep_api.get_client()
    second = keep_api.get_client()

    assert first is created
    assert second is created
    assert created.auth_calls == [("user@example.com", "token")]


def test_get_client_raises_when_missing_credentials(monkeypatch):
    keep_api._keep_client = None
    monkeypatch.setattr(keep_api, "load_dotenv", lambda: None)
    monkeypatch.setattr(keep_api.os, "getenv", lambda _key: None)

    try:
        keep_api.get_client()
    except ValueError as exc:
        assert "Missing Google Keep credentials" in str(exc)
    else:
        raise AssertionError("Expected ValueError for missing credentials")


def test_cached_client_refreshes_external_changes(monkeypatch):
    class RemoteKeep(DummyKeep):
        title = 'old title'

        def sync(self):
            self.title = 'edited in Keep'

    created = RemoteKeep()
    monkeypatch.setattr(keep_api, '_keep_client', created)
    assert keep_api.get_client().title == 'edited in Keep'


def test_concurrent_initialization_authenticates_once(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    entered = Event()
    release = Event()
    second_started = Event()
    created = []

    class SlowKeep(DummyKeep):
        def __init__(self):
            super().__init__()
            created.append(self)

        def authenticate(self, email, token):
            entered.set()
            assert release.wait(2)
            super().authenticate(email, token)

        def sync(self):
            pass

    monkeypatch.setattr(keep_api, '_keep_client', None)
    monkeypatch.setattr(keep_api, 'load_dotenv', lambda: None)
    monkeypatch.setenv('GOOGLE_EMAIL', 'test@example.com')
    monkeypatch.setenv('GOOGLE_MASTER_TOKEN', 'fake')
    monkeypatch.setattr(keep_api.gkeepapi, 'Keep', SlowKeep)

    def second_call():
        second_started.set()
        return keep_api.get_client()

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(keep_api.get_client)
        try:
            assert entered.wait(2)
            second = pool.submit(second_call)
            assert second_started.wait(2)
        finally:
            release.set()
        assert first.result() is second.result()
    assert len(created) == 1


def test_tools_do_not_overlap_access_to_shared_state(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event

    from server import cli

    entered = Event()
    release = Event()
    second_started = Event()
    overlap = Event()

    def serialize(note):
        if note == 'first':
            entered.set()
            assert release.wait(2)
        else:
            overlap.set()
        return {'id': note}

    monkeypatch.setattr(cli, '_get_note_or_raise', lambda note_id: (None, note_id))
    monkeypatch.setattr(cli, 'serialize_note', serialize)

    def second_call():
        second_started.set()
        return cli.get_note('second')

    with ThreadPoolExecutor(max_workers=2) as pool:
        first = pool.submit(cli.get_note, 'first')
        try:
            assert entered.wait(2)
            second = pool.submit(second_call)
            assert second_started.wait(2)
            assert not overlap.wait(0.1)
        finally:
            release.set()
        first.result()
        second.result()
    assert overlap.is_set()
