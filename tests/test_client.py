from unittest.mock import patch, MagicMock
from codeforces_cli.client import CodeforcesClient
from codeforces_cli.config import Config


def test_client_init(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    assert client.base_url == "https://codeforces.com"


def test_client_loads_saved_session(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    cfg.save_session({"JSESSIONID": "abc123"})
    client = CodeforcesClient(cfg)
    assert client.session.cookies.get("JSESSIONID") == "abc123"


def test_client_is_logged_in_false(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    with patch.object(client.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = '<a href="/enter">Enter</a>'
        mock_get.return_value = mock_resp
        assert client.is_logged_in() is False


def test_client_is_logged_in_true(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    client = CodeforcesClient(cfg)
    with patch.object(client.session, "get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = '<a href="/profile/testuser">testuser</a>'
        mock_get.return_value = mock_resp
        assert client.is_logged_in() is True
