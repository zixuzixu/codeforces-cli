from pathlib import Path
from codeforces_cli.runner import compile_source, run_test, compare_output


def test_compare_output_exact_match():
    assert compare_output("6\n", "6") is True


def test_compare_output_trailing_whitespace():
    assert compare_output("6  \n  ", "6") is True


def test_compare_output_mismatch():
    assert compare_output("7\n", "6") is False


def test_compare_output_multiline():
    assert compare_output("1\n2\n3\n", "1\n2\n3") is True


def test_compare_output_multiline_mismatch():
    assert compare_output("1\n2\n4\n", "1\n2\n3") is False


def test_run_test_python(tmp_path):
    script = tmp_path / "main.py"
    script.write_text("x = int(input())\nprint(x * 2)")
    input_data = "5"
    result = run_test(
        source=script,
        input_data=input_data,
        compile_cmd=None,
        run_cmd="python3 {source}",
        timeout=5,
        work_dir=tmp_path,
    )
    assert result.stdout.strip() == "10"
    assert result.returncode == 0


def test_run_test_timeout(tmp_path):
    script = tmp_path / "main.py"
    script.write_text("import time\ntime.sleep(10)")
    result = run_test(
        source=script,
        input_data="",
        compile_cmd=None,
        run_cmd="python3 {source}",
        timeout=1,
        work_dir=tmp_path,
    )
    assert result.timed_out is True


def test_compile_source_not_needed(tmp_path):
    script = tmp_path / "main.py"
    script.write_text("print('hi')")
    ok, msg = compile_source(script, compile_cmd=None, work_dir=tmp_path)
    assert ok is True
