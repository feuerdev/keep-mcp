import runpy

import pytest


def test_main_module_calls_cli_main(monkeypatch):
    called = {"value": False}

    def fake_main():
        called["value"] = True

    import server.cli

    monkeypatch.setattr(server.cli, "main", fake_main)
    with pytest.raises(SystemExit) as result:
        runpy.run_module("server.__main__", run_name="__main__")
    assert result.value.code is None
    assert called["value"] is True
