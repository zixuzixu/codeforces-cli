import json
from pathlib import Path
from codeforces_cli.config import Config


def test_default_config(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    cfg = Config(config_dir=tmp_path / ".cf")
    assert cfg.workspace == Path.home() / "cf"
    assert cfg.default_language == ".cpp"
    assert ".cpp" in cfg.languages
    assert ".py" in cfg.languages
    assert ".java" in cfg.languages


def test_language_config_has_required_fields(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    cpp = cfg.languages[".cpp"]
    assert "compile" in cpp
    assert "run" in cpp
    assert "cf_lang_id" in cpp


def test_save_and_load_config(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    cfg.workspace = tmp_path / "my_cf"
    cfg.save()
    cfg2 = Config(config_dir=tmp_path / ".cf")
    assert cfg2.workspace == tmp_path / "my_cf"


def test_get_template_default(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    template = cfg.get_template(".cpp")
    assert "#include" in template
    assert "int main" in template


def test_get_template_custom(tmp_path):
    cfg = Config(config_dir=tmp_path / ".cf")
    template_dir = tmp_path / ".cf" / "templates"
    template_dir.mkdir(parents=True)
    (template_dir / "main.cpp").write_text("// custom\nint main() {}")
    template = cfg.get_template(".cpp")
    assert "// custom" in template
