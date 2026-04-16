from unittest.mock import patch, MagicMock
from codeforces_cli.client import CodeforcesClient, BASE_URL
from codeforces_cli.config import Config


def test_client_init(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    assert client.config is cfg
    assert client._started is False


def test_client_config_stores_session(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    cfg.save_session({"JSESSIONID": "abc123"})
    loaded = cfg.load_session()
    assert loaded["JSESSIONID"] == "abc123"


def test_client_is_logged_in_false(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    with patch.object(client, "_get", return_value='<a href="/enter">Enter</a>'):
        assert client.is_logged_in() is False


def test_client_is_logged_in_true(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    with patch.object(client, "_get", return_value='<a href="/profile/testuser">testuser</a>'):
        assert client.is_logged_in() is True


def test_login_with_cookies_parses_string(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    with patch.object(client, "_get", return_value='<a href="/profile/testuser">testuser</a>'), \
         patch.object(client, "_ensure_browser"):
        # Mock _loop_thread for the async cookie setting
        client._loop_thread = MagicMock()
        client._loop_thread.run = MagicMock(return_value=None)
        result = client.login_with_cookies("JSESSIONID=abc123; foo=bar")
    assert result is True
    saved = cfg.load_session()
    assert saved["JSESSIONID"] == "abc123"
    assert saved["foo"] == "bar"


def test_base_url_constant():
    assert BASE_URL == "https://codeforces.com"
