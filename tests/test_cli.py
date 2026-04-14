from click.testing import CliRunner
from codeforces_cli.cli import main


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "Codeforces CLI" in result.output


def test_login_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["login", "--help"])
    assert result.exit_code == 0


def test_contest_list_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["contest", "list", "--help"])
    assert result.exit_code == 0


def test_contest_info_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["contest", "info", "--help"])
    assert result.exit_code == 0


def test_download_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["download", "--help"])
    assert result.exit_code == 0


def test_parse_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["parse", "--help"])
    assert result.exit_code == 0


def test_test_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["test", "--help"])
    assert result.exit_code == 0


def test_submit_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["submit", "--help"])
    assert result.exit_code == 0


def test_status_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["status", "--help"])
    assert result.exit_code == 0


def test_standings_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["standings", "--help"])
    assert result.exit_code == 0


def test_open_command_exists():
    runner = CliRunner()
    result = runner.invoke(main, ["open", "--help"])
    assert result.exit_code == 0
