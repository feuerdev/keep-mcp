import json
import traceback

import gkeepapi
import pytest
import requests

from server import keep_api


@pytest.fixture(autouse=True)
def isolated_config(monkeypatch):
    monkeypatch.setattr(keep_api, '_keep_client', None)
    monkeypatch.setattr(keep_api, 'load_dotenv', lambda: None)
    monkeypatch.setenv('GOOGLE_EMAIL', 'fixture@example.com')
    monkeypatch.setenv('GOOGLE_MASTER_TOKEN', 'fixture-token-must-not-leak')
    monkeypatch.delenv('UNSAFE_MODE', raising=False)


@pytest.mark.parametrize('key', ['GOOGLE_EMAIL', 'GOOGLE_MASTER_TOKEN'])
def test_whitespace_credentials_are_rejected_before_authentication(monkeypatch, key):
    monkeypatch.setenv(key, '   ')
    monkeypatch.setattr(keep_api.gkeepapi, 'Keep', lambda: pytest.fail('No client for invalid config'))
    with pytest.raises(ValueError, match=key):
        keep_api.get_client()


@pytest.mark.parametrize('failure', [
    gkeepapi.exception.LoginException('fixture-token-must-not-leak'),
    requests.ConnectionError('fixture-token-must-not-leak'),
    requests.exceptions.JSONDecodeError('fixture-token-must-not-leak', 'private response', 0),
])
def test_authentication_error_and_traceback_do_not_expose_provider_payload(monkeypatch, failure):
    class Client:
        def authenticate(self, *args):
            raise failure
    monkeypatch.setattr(keep_api.gkeepapi, 'Keep', Client)
    try:
        keep_api.get_client()
    except (RuntimeError, requests.RequestException) as exc:
        message = ''.join(traceback.format_exception(exc))
        assert 'fixture-token-must-not-leak' not in message
        assert 'private response' not in message
        assert keep_api._keep_client is None
    else:
        pytest.fail('Authentication must fail')


def test_offline_diagnosis_reports_only_presence_and_supported_versions(monkeypatch, capsys):
    from server import cli
    monkeypatch.setattr(keep_api.gkeepapi, 'Keep', lambda: pytest.fail('Offline check must not connect'))
    assert cli.main(['--check-config']) == 0
    data = json.loads(capsys.readouterr().out)
    assert data['status'] == 'configured'
    assert data['credential_source'] == 'environment_or_local_dotenv'
    assert data['write_mode'] == 'label_guarded'
    assert data['versions']['gkeepapi']
    assert 'fixture-token-must-not-leak' not in json.dumps(data)
    assert 'fixture@example.com' not in json.dumps(data)


def test_offline_diagnosis_rejects_missing_token_without_stdio_server(monkeypatch, capsys):
    from server import cli
    monkeypatch.delenv('GOOGLE_MASTER_TOKEN')
    monkeypatch.setattr(cli.mcp, 'run', lambda **kw: pytest.fail('No server for offline check'))
    assert cli.main(['--check-config']) == 1
    data = json.loads(capsys.readouterr().out)
    assert data['status'] == 'configuration_error'
    assert data['missing'] == ['GOOGLE_MASTER_TOKEN']


def test_network_failure_has_actionable_redacted_error_without_retry(monkeypatch):
    attempts = []
    client = object()
    monkeypatch.setattr(keep_api, '_keep_client', client)
    @keep_api.keep_operation
    def mutation():
        attempts.append('sent')
        raise requests.ConnectionError('fixture-token-must-not-leak')
    with pytest.raises(requests.ConnectionError) as result:
        mutation()
    assert 'network' in str(result.value).lower()
    assert 'fixture-token-must-not-leak' not in ''.join(traceback.format_exception(result.value))
    assert attempts == ['sent']
    assert keep_api._keep_client is None
