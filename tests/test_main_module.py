import runpy


def test_main_module_calls_cli_main(monkeypatch):
    called = {"value": False}

    def fake_main():
        called["value"] = True

    import server.cli

    monkeypatch.setattr(server.cli, "main", fake_main)
    runpy.run_module("server.__main__", run_name="__main__")
    assert called["value"] is True
