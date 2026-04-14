from pathlib import Path
from codeforces_cli.utils import parse_problem_arg, detect_problem_from_cwd, find_source_file


def test_parse_problem_arg_combined():
    contest, problem = parse_problem_arg("1920A")
    assert contest == "1920"
    assert problem == "A"


def test_parse_problem_arg_slash():
    contest, problem = parse_problem_arg("1920/A")
    assert contest == "1920"
    assert problem == "A"


def test_parse_problem_arg_with_numbers():
    contest, problem = parse_problem_arg("1920E1")
    assert contest == "1920"
    assert problem == "E1"


def test_detect_problem_from_cwd(tmp_path):
    problem_dir = tmp_path / "cf" / "1920" / "A"
    problem_dir.mkdir(parents=True)
    contest, problem = detect_problem_from_cwd(problem_dir, workspace=tmp_path / "cf")
    assert contest == "1920"
    assert problem == "A"


def test_detect_problem_from_cwd_not_in_workspace(tmp_path):
    contest, problem = detect_problem_from_cwd(tmp_path, workspace=tmp_path / "cf")
    assert contest is None
    assert problem is None


def test_find_source_file_single(tmp_path):
    (tmp_path / "main.cpp").write_text("int main() {}")
    src = find_source_file(tmp_path, default_lang=".cpp")
    assert src.name == "main.cpp"


def test_find_source_file_prefers_default(tmp_path):
    (tmp_path / "main.cpp").write_text("int main() {}")
    (tmp_path / "main.py").write_text("pass")
    src = find_source_file(tmp_path, default_lang=".cpp")
    assert src.suffix == ".cpp"


def test_find_source_file_none(tmp_path):
    src = find_source_file(tmp_path, default_lang=".cpp")
    assert src is None
