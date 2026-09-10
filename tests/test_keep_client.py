import io
from server import keep_api


class DummyKeep:
    def __init__(self):
        self.auth_calls = []

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


def test_get_client_reads_token_from_secret_file(monkeypatch):
    keep_api._keep_client = None
    created = DummyKeep()

    monkeypatch.setattr(keep_api, "load_dotenv", lambda: None)
    monkeypatch.setattr(keep_api.os, "getenv", lambda key: {
        "GOOGLE_EMAIL": "user@example.com",
    }.get(key))
    monkeypatch.setattr(keep_api.os.path, "exists", lambda p: p == "/run/secrets/google_master_token")
    monkeypatch.setattr("builtins.open", lambda p, *a, **kw: io.StringIO("token-from-file\n"))
    monkeypatch.setattr(keep_api.gkeepapi, "Keep", lambda: created)

    keep_api.get_client()

    assert created.auth_calls == [("user@example.com", "token-from-file")]


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
