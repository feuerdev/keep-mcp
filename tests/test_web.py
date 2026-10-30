import pytest
from starlette.responses import PlainTextResponse
from starlette.testclient import TestClient

from server.web import ApiKeyAuthMiddleware, create_app


def test_public_health_endpoints():
    app = create_app(api_key="secret-key")
    client = TestClient(app)

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "ok"

    res_healthz = client.get("/healthz")
    assert res_healthz.status_code == 200
    assert res_healthz.text == "OK"

    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.text == "OK"


def test_auth_middleware_blocks_unauthorized():
    dummy_app = PlainTextResponse("Protected Content")
    app = ApiKeyAuthMiddleware(dummy_app, api_key="secret-key")
    client = TestClient(app)

    res = client.get("/protected")
    assert res.status_code == 401
    assert res.json()["error"] == "Unauthorized"


def test_auth_middleware_accepts_valid_tokens():
    dummy_app = PlainTextResponse("Protected Content")
    app = ApiKeyAuthMiddleware(dummy_app, api_key="secret-key")
    client = TestClient(app)

    res_bearer = client.get("/protected", headers={"Authorization": "Bearer secret-key"})
    assert res_bearer.status_code == 200
    assert res_bearer.text == "Protected Content"

    res_api_key = client.get("/protected", headers={"X-API-Key": "secret-key"})
    assert res_api_key.status_code == 200
    assert res_api_key.text == "Protected Content"

    res_query = client.get("/protected?token=secret-key")
    assert res_query.status_code == 200
    assert res_query.text == "Protected Content"

    res_api_key_query = client.get("/protected?api_key=secret-key")
    assert res_api_key_query.status_code == 200
    assert res_api_key_query.text == "Protected Content"


def test_create_app_streamable_http():
    app = create_app(api_key=None, transport="streamable-http")
    client = TestClient(app)

    res = client.get("/healthz")
    assert res.status_code == 200
    assert res.text == "OK"
