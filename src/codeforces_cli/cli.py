import webbrowser
import time
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from codeforces_cli.config import Config
from codeforces_cli.client import CodeforcesClient
from codeforces_cli.utils import parse_problem_arg, detect_problem_from_cwd, find_source_file
from codeforces_cli.runner import compile_source, run_test, compare_output

console = Console()


def get_client() -> tuple[Config, CodeforcesClient]:
    config = Config()
    client = CodeforcesClient(config)
    return config, client


@click.group()
@click.version_option()
def main():
    """Codeforces CLI - interact with Codeforces from your terminal."""
    pass


@main.command()
def login():
    """Login to Codeforces by importing browser cookies.

    Steps:
    1. Open codeforces.com in your browser and log in
    2. Open DevTools (F12) → Application → Cookies → codeforces.com
    3. Copy the cookie string (or use DevTools Console: document.cookie)
    4. Paste it here
    """
    config, client = get_client()

    console.print("[bold]Login to Codeforces via browser cookies[/bold]\n")
    console.print("1. Open [cyan]https://codeforces.com[/cyan] in your browser and log in")
    console.print("2. Open DevTools (F12) → Console")
    console.print("3. Run: [cyan]document.cookie[/cyan]")
    console.print("4. Copy the output and paste below\n")

    cookie_string = click.prompt("Paste cookies")

    success = client.login_with_cookies(cookie_string)

    if success:
        console.print("[green]Login successful![/green]")
    else:
        console.print("[red]Login failed. Make sure you're logged in on codeforces.com before copying cookies.[/red]")
        raise SystemExit(1)


@main.group()
def contest():
    """Contest commands."""
    pass


@contest.command("list")
def contest_list():
    """List upcoming and recent contests."""
    _, client = get_client()
    with console.status("Fetching contests..."):
        contests = client.get_contest_list()

    if not contests:
        console.print("[yellow]No contests found.[/yellow]")
        return

    table = Table(title="Contests")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    table.add_column("Time", style="green")
    for c in contests[:20]:
        table.add_row(c["id"], c["name"], c["time"])
    console.print(table)


@contest.command("info")
@click.argument("contest_id")
def contest_info(contest_id: str):
    """Show contest details and problem list."""
    _, client = get_client()
    with console.status("Fetching contest info..."):
        problems = client.get_contest_problems(contest_id)

    if not problems:
        console.print("[yellow]No problems found.[/yellow]")
        return

    table = Table(title=f"Contest {contest_id}")
    table.add_column("ID", style="cyan")
    table.add_column("Name")
    for p in problems:
        table.add_row(p["id"], p["name"])
    console.print(table)


def _download_problem(config: Config, client: CodeforcesClient, contest_id: str, problem_id: str):
    """Download problem statement and samples, create source template."""
    from codeforces_cli.parser import parse_sample_tests, parse_problem_statement

    problem_dir = config.workspace / contest_id / problem_id
    problem_dir.mkdir(parents=True, exist_ok=True)

    # Fetch page once, extract both statement and samples
    html = client.get_problem_page(contest_id, problem_id)
    samples = parse_sample_tests(html)
    statement = parse_problem_statement(html)

    # Save problem statement
    if statement:
        (problem_dir / "problem.txt").write_text(statement)

    if not samples:
        console.print(f"  [yellow]{problem_id}: no samples found[/yellow]")
        return

    for i, (inp, out) in enumerate(samples, 1):
        (problem_dir / f"in{i}.txt").write_text(inp + "\n")
        (problem_dir / f"out{i}.txt").write_text(out + "\n")

    # Create template source file if not exists
    ext = config.default_language
    ext_name = {".cpp": "main.cpp", ".py": "main.py", ".java": "Main.java"}
    src_file = problem_dir / ext_name.get(ext, f"main{ext}")
    if not src_file.exists():
        template = config.get_template(ext)
        src_file.write_text(template)

    console.print(f"  [green]{problem_id}: {len(samples)} sample(s) + problem statement[/green]")


@main.command()
@click.argument("contest_id")
def download(contest_id: str):
    """Download all problems' sample tests for a contest."""
    config, client = get_client()
    with console.status("Fetching problem list..."):
        problems = client.get_contest_problems(contest_id)

    if not problems:
        console.print("[red]No problems found.[/red]")
        return

    console.print(f"Downloading contest {contest_id} ({len(problems)} problems)...")
    for p in problems:
        _download_problem(config, client, contest_id, p["id"])

    console.print(f"\n[green]Saved to {config.workspace / contest_id}[/green]")


@main.command()
@click.argument("problem")
def parse(problem: str):
    """Download sample tests for a single problem (e.g. 1920/A or 1920A)."""
    config, client = get_client()
    contest_id, problem_id = parse_problem_arg(problem)

    console.print(f"Downloading {contest_id}/{problem_id}...")
    _download_problem(config, client, contest_id, problem_id)
    console.print(f"\n[green]Saved to {config.workspace / contest_id / problem_id}[/green]")


@main.command("test")
@click.argument("problem", required=False)
def test_cmd(problem: str | None):
    """Run local tests against sample cases."""
    config, _ = get_client()

    if problem:
        contest_id, problem_id = parse_problem_arg(problem)
        problem_dir = config.workspace / contest_id / problem_id
    else:
        cwd = Path.cwd()
        contest_id, problem_id = detect_problem_from_cwd(cwd, config.workspace)
        if not contest_id:
            console.print("[red]Cannot detect problem from current directory. "
                          "Pass problem as argument (e.g. cf test 1920A) or cd into the problem directory.[/red]")
            raise SystemExit(1)
        problem_dir = cwd

    if not problem_dir.exists():
        console.print(f"[red]Directory {problem_dir} not found. Run cf download first.[/red]")
        raise SystemExit(1)

    source = find_source_file(problem_dir, config.default_language)
    if not source:
        console.print(f"[red]No source file found in {problem_dir}[/red]")
        raise SystemExit(1)

    ext = source.suffix
    lang = config.languages.get(ext)
    if not lang:
        console.print(f"[red]Unsupported language: {ext}[/red]")
        raise SystemExit(1)

    # Compile
    ok, msg = compile_source(source, lang.get("compile"), problem_dir)
    if not ok:
        console.print(f"[red]Compilation failed:[/red]\n{msg}")
        raise SystemExit(1)

    # Find test cases
    test_inputs = sorted(problem_dir.glob("in*.txt"))
    if not test_inputs:
        console.print("[yellow]No test cases found.[/yellow]")
        return

    passed = 0
    total = len(test_inputs)

    for in_file in test_inputs:
        num = in_file.stem.replace("in", "")
        out_file = problem_dir / f"out{num}.txt"
        if not out_file.exists():
            console.print(f"[yellow]Test {num}: missing expected output[/yellow]")
            continue

        input_data = in_file.read_text()
        expected = out_file.read_text().strip()

        result = run_test(
            source=source,
            input_data=input_data,
            compile_cmd=None,  # already compiled
            run_cmd=lang["run"],
            timeout=config.test_timeout,
            work_dir=problem_dir,
        )

        # Save actual output to ans{num}.txt
        ans_file = problem_dir / f"ans{num}.txt"
        ans_file.write_text(result.stdout)

        if result.timed_out:
            console.print(f"[red]Test {num}: TLE (>{config.test_timeout}s)[/red]")
        elif result.returncode != 0:
            console.print(f"[red]Test {num}: RE[/red]\n{result.stderr}")
        elif compare_output(result.stdout, expected):
            console.print(f"[green]Test {num}: PASS[/green]")
            passed += 1
        else:
            console.print(f"[red]Test {num}: FAIL[/red]")
            console.print(f"  Expected: {expected}")
            console.print(f"  Got:      {result.stdout.strip()}")

    color = "green" if passed == total else "red"
    console.print(f"\n[{color}]{passed}/{total} passed[/{color}]")


@main.command()
@click.argument("problem", required=False)
def run(problem: str | None):
    """Compile and run solution, feeding each test case input and showing output."""
    config, _ = get_client()

    if problem:
        contest_id, problem_id = parse_problem_arg(problem)
        problem_dir = config.workspace / contest_id / problem_id
    else:
        cwd = Path.cwd()
        contest_id, problem_id = detect_problem_from_cwd(cwd, config.workspace)
        if not contest_id:
            console.print("[red]Cannot detect problem. Pass as argument or cd into problem directory.[/red]")
            raise SystemExit(1)
        problem_dir = cwd

    if not problem_dir.exists():
        console.print(f"[red]Directory {problem_dir} not found. Run cf download first.[/red]")
        raise SystemExit(1)

    source = find_source_file(problem_dir, config.default_language)
    if not source:
        console.print(f"[red]No source file found in {problem_dir}[/red]")
        raise SystemExit(1)

    ext = source.suffix
    lang = config.languages.get(ext)
    if not lang:
        console.print(f"[red]Unsupported language: {ext}[/red]")
        raise SystemExit(1)

    # Compile
    console.print(f"[cyan]Compiling {source.name}...[/cyan]")
    ok, msg = compile_source(source, lang.get("compile"), problem_dir)
    if not ok:
        console.print(f"[red]Compilation failed:[/red]\n{msg}")
        raise SystemExit(1)
    console.print("[green]Compiled OK[/green]\n")

    # Find and run each test case
    test_inputs = sorted(problem_dir.glob("in*.txt"))
    if not test_inputs:
        console.print("[yellow]No test cases found.[/yellow]")
        return

    for in_file in test_inputs:
        num = in_file.stem.replace("in", "")
        out_file = problem_dir / f"out{num}.txt"
        input_data = in_file.read_text()
        expected = out_file.read_text().strip() if out_file.exists() else None

        console.print(f"[bold]━━━ Test {num} ━━━[/bold]")
        console.print(f"[dim]Input:[/dim]")
        console.print(input_data.rstrip())

        result = run_test(
            source=source,
            input_data=input_data,
            compile_cmd=None,
            run_cmd=lang["run"],
            timeout=config.test_timeout,
            work_dir=problem_dir,
        )

        # Save actual output to ans{num}.txt
        ans_file = problem_dir / f"ans{num}.txt"
        ans_file.write_text(result.stdout)

        if result.timed_out:
            console.print(f"[red]TLE (>{config.test_timeout}s)[/red]")
        elif result.returncode != 0:
            console.print(f"[red]Runtime Error[/red]\n{result.stderr}")
        else:
            console.print(f"[dim]Output:[/dim]")
            console.print(result.stdout.rstrip())
            if expected is not None:
                console.print(f"[dim]Expected:[/dim]")
                console.print(expected)
                if compare_output(result.stdout, expected):
                    console.print(f"[green]>>> PASS[/green]")
                else:
                    console.print(f"[red]>>> FAIL[/red]")
        console.print(f"[dim]Saved to {ans_file.name}[/dim]")
        console.print()


@main.command()
@click.argument("problem", required=False)
def submit(problem: str | None):
    """Submit solution to Codeforces."""
    config, client = get_client()

    if problem:
        contest_id, problem_id = parse_problem_arg(problem)
        problem_dir = config.workspace / contest_id / problem_id
    else:
        cwd = Path.cwd()
        contest_id, problem_id = detect_problem_from_cwd(cwd, config.workspace)
        if not contest_id:
            console.print("[red]Cannot detect problem. Pass as argument or cd into problem directory.[/red]")
            raise SystemExit(1)
        problem_dir = cwd

    source = find_source_file(problem_dir, config.default_language)
    if not source:
        console.print(f"[red]No source file found in {problem_dir}[/red]")
        raise SystemExit(1)

    ext = source.suffix
    lang = config.languages.get(ext)
    if not lang:
        console.print(f"[red]Unsupported language: {ext}[/red]")
        raise SystemExit(1)

    lang_id = lang["cf_lang_id"]
    source_code = source.read_text()

    console.print(f"Submitting {contest_id}{problem_id} ({source.name}, lang_id={lang_id})...")

    if not client.is_logged_in():
        console.print("[red]Not logged in. Run 'cf login' first.[/red]")
        raise SystemExit(1)

    try:
        sub_id = client.submit(contest_id, problem_id, source_code, lang_id)
    except RuntimeError as e:
        console.print(f"[red]{e}[/red]")
        raise SystemExit(1)

    if not sub_id:
        console.print("[yellow]Submitted, but could not get submission ID. Check with 'cf status'.[/yellow]")
        return

    # Poll verdict
    console.print(f"Submission ID: {sub_id}")
    for _ in range(30):
        time.sleep(2)
        verdict = client.get_submission_verdict(contest_id, sub_id)
        if not verdict:
            continue
        v = verdict["verdict"]
        if "waiting" in v.lower() or "running" in v.lower() or "queue" in v.lower():
            console.print(f"  {v}...", end="\r")
            continue
        # Final verdict
        if "accepted" in v.lower():
            console.print(f"\n[green]Verdict: {v}  (time: {verdict['time']}, memory: {verdict['memory']})[/green]")
        else:
            console.print(f"\n[red]Verdict: {v}  (time: {verdict['time']}, memory: {verdict['memory']})[/red]")
        return

    console.print("\n[yellow]Timed out waiting for verdict. Check with 'cf status'.[/yellow]")


@main.command()
def status():
    """Show recent submission verdicts."""
    _, client = get_client()

    if not client.is_logged_in():
        console.print("[red]Not logged in. Run 'cf login' first.[/red]")
        raise SystemExit(1)

    with console.status("Fetching submissions..."):
        subs = client.get_status()

    if not subs:
        console.print("[yellow]No submissions found.[/yellow]")
        return

    table = Table(title="Recent Submissions")
    table.add_column("ID", style="cyan")
    table.add_column("Problem")
    table.add_column("Verdict")
    table.add_column("Time")
    table.add_column("Memory")
    for s in subs[:15]:
        verdict_style = "green" if "accepted" in s["verdict"].lower() else "red"
        table.add_row(s["id"], s["problem"], f"[{verdict_style}]{s['verdict']}[/{verdict_style}]", s["time"], s["memory"])
    console.print(table)


@main.command()
@click.argument("contest_id")
def standings(contest_id: str):
    """Show contest standings."""
    _, client = get_client()
    with console.status("Fetching standings..."):
        rows = client.get_standings(contest_id)

    if not rows:
        console.print("[yellow]No standings found.[/yellow]")
        return

    table = Table(title=f"Standings — Contest {contest_id}")
    table.add_column("Rank", style="cyan")
    table.add_column("Who")
    table.add_column("Score", style="green")
    for r in rows[:50]:
        table.add_row(r["rank"], r["who"], r["score"])
    console.print(table)


@main.command("open")
@click.argument("problem", required=False)
def open_cmd(problem: str | None):
    """Open problem page in browser."""
    config, _ = get_client()

    if problem:
        contest_id, problem_id = parse_problem_arg(problem)
    else:
        cwd = Path.cwd()
        contest_id, problem_id = detect_problem_from_cwd(cwd, config.workspace)
        if not contest_id:
            console.print("[red]Cannot detect problem. Pass as argument or cd into problem directory.[/red]")
            raise SystemExit(1)

    url = f"https://codeforces.com/contest/{contest_id}/problem/{problem_id}"
    console.print(f"Opening {url}")
    webbrowser.open(url)
