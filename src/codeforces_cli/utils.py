import re
from pathlib import Path

SUPPORTED_EXTENSIONS = {".cpp", ".py", ".java", ".c", ".rs", ".go", ".kt"}


def parse_problem_arg(arg: str) -> tuple[str, str]:
    """Parse '1920A', '1920/A', or '1920E1' into (contest_id, problem_id)."""
    if "/" in arg:
        parts = arg.split("/", 1)
        return parts[0], parts[1]
    match = re.match(r"^(\d+)([A-Za-z]\d*)$", arg)
    if match:
        return match.group(1), match.group(2).upper()
    raise ValueError(f"Cannot parse problem argument: {arg}")


def detect_problem_from_cwd(cwd: Path, workspace: Path) -> tuple[str | None, str | None]:
    """Detect contest_id and problem_id from current working directory."""
    try:
        rel = cwd.relative_to(workspace)
    except ValueError:
        return None, None
    parts = rel.parts
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None, None


def find_source_file(directory: Path, default_lang: str) -> Path | None:
    """Find a source file in directory. Prefers default language if multiple exist."""
    sources = [f for f in directory.iterdir() if f.is_file() and f.suffix in SUPPORTED_EXTENSIONS]
    if not sources:
        return None
    for src in sources:
        if src.suffix == default_lang:
            return src
    return sources[0]
