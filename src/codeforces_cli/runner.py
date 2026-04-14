import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass
class RunResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool


def compare_output(actual: str, expected: str) -> bool:
    """Compare output ignoring trailing whitespace per line and trailing newlines."""
    actual_lines = [line.rstrip() for line in actual.rstrip().split("\n")]
    expected_lines = [line.rstrip() for line in expected.rstrip().split("\n")]
    return actual_lines == expected_lines


def compile_source(source: Path, compile_cmd: str | None, work_dir: Path) -> tuple[bool, str]:
    """Compile source file. Returns (success, message)."""
    if not compile_cmd:
        return True, ""

    output = source.with_suffix("")
    cmd = compile_cmd.format(source=source.name, output=output.name)

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "Compilation timed out"


def run_test(
    source: Path,
    input_data: str,
    compile_cmd: str | None,
    run_cmd: str,
    timeout: int,
    work_dir: Path,
) -> RunResult:
    """Run a program with input and return the result."""
    output = source.with_suffix("")
    classname = source.stem
    cmd = run_cmd.format(
        source=source.name,
        output=output.name,
        classname=classname,
    )

    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            input=input_data,
            timeout=timeout,
        )
        return RunResult(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
            timed_out=False,
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            stdout="",
            stderr="Time limit exceeded",
            returncode=-1,
            timed_out=True,
        )
