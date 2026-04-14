import re
from bs4 import BeautifulSoup


def parse_problem_statement(html: str) -> str:
    """Extract problem statement as readable plain text from a problem page."""
    soup = BeautifulSoup(html, "lxml")
    stmt = soup.find("div", class_="problem-statement")
    if not stmt:
        return ""

    parts = []

    # Header: title, limits
    header = stmt.find("div", class_="header")
    if header:
        title = header.find("div", class_="title")
        tl = header.find("div", class_="time-limit")
        ml = header.find("div", class_="memory-limit")
        if title:
            parts.append(title.get_text(strip=True))
        limits = []
        if tl:
            limits.append(tl.get_text(strip=True).replace("time limit per test", "Time: "))
        if ml:
            limits.append(ml.get_text(strip=True).replace("memory limit per test", "Memory: "))
        if limits:
            parts.append(" | ".join(limits))
        parts.append("")

    # Body sections
    for div in stmt.find_all("div", recursive=False):
        cls = div.get("class", [])
        if "header" in cls or "sample-tests" in cls:
            continue

        if "input-specification" in cls:
            parts.append("Input")
            parts.append("-" * 40)
        elif "output-specification" in cls:
            parts.append("Output")
            parts.append("-" * 40)
        elif "note" in cls:
            parts.append("Note")
            parts.append("-" * 40)
        elif not cls:
            # Main problem description
            parts.append("Description")
            parts.append("-" * 40)

        text = div.get_text("\n", strip=True)
        # Clean up LaTeX $$$...$$$
        text = re.sub(r"\$\$\$([^$]*)\$\$\$", r"\1", text)
        parts.append(text)
        parts.append("")

    # Sample tests section
    samples = parse_sample_tests(html)
    if samples:
        parts.append("Examples")
        parts.append("-" * 40)
        for i, (inp, out) in enumerate(samples, 1):
            parts.append(f"Input {i}:")
            parts.append(inp)
            parts.append(f"Output {i}:")
            parts.append(out)
            parts.append("")

    return "\n".join(parts)


def parse_sample_tests(html: str) -> list[tuple[str, str]]:
    """Parse sample input/output pairs from a problem page."""
    soup = BeautifulSoup(html, "lxml")
    sample_div = soup.find("div", class_="sample-test")
    if not sample_div:
        return []

    inputs = sample_div.find_all("div", class_="input")
    outputs = sample_div.find_all("div", class_="output")

    tests = []
    for inp, out in zip(inputs, outputs):
        in_text = inp.find("pre").get_text("\n").strip()
        out_text = out.find("pre").get_text("\n").strip()
        tests.append((in_text, out_text))
    return tests


def parse_contest_problems(html: str) -> list[dict]:
    """Parse problem list from a contest page."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="problems")
    if not table:
        return []

    problems = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        id_cell = cells[0]
        id_link = id_cell.find("a")
        if not id_link:
            continue
        problem_id = id_link.get_text(strip=True)

        name = ""
        if len(cells) > 1:
            name_link = cells[1].find("a")
            if name_link:
                name = name_link.get_text(strip=True)

        problems.append({"id": problem_id, "name": name})
    return problems


def parse_contest_list(html: str) -> list[dict]:
    """Parse contest list from /contests page.

    The page has multiple datatables:
    - Table 0: upcoming contests (no links in name cell)
    - Table 1: past contests (links with /contest/<id> in name cell)
    """
    soup = BeautifulSoup(html, "lxml")
    tables = soup.find_all("div", class_="datatable")
    rows = []

    for table in tables:
        for tr in table.find_all("tr")[1:]:
            cells = tr.find_all("td")
            if len(cells) < 4:
                continue

            # Extract contest name — it's text before the first <a> tag
            name_cell = cells[0]
            name = ""
            for child in name_cell.children:
                if hasattr(child, "name") and child.name == "a":
                    break
                text = child.get_text(strip=True) if hasattr(child, "get_text") else str(child).strip()
                if text:
                    name = text
                    break
            if not name:
                name = name_cell.get_text(strip=True)

            # Extract contest ID from first link href
            contest_id = ""
            name_link = name_cell.find("a")
            if name_link and name_link.get("href"):
                parts = name_link["href"].strip("/").split("/")
                if "contest" in parts:
                    idx = parts.index("contest")
                    if idx + 1 < len(parts):
                        contest_id = parts[idx + 1]

            # Time is in cells[2] (cells[1] is writers)
            time_str = cells[2].get_text(strip=True) if len(cells) > 2 else ""

            rows.append({"id": contest_id, "name": name, "time": time_str})

    return rows


def parse_standings(html: str) -> list[dict]:
    """Parse standings table from contest standings page."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="standings")
    if not table:
        return []

    rows = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 3:
            continue
        rank = cells[0].get_text(strip=True)
        who = cells[1].get_text(strip=True)
        score = cells[2].get_text(strip=True)
        rows.append({"rank": rank, "who": who, "score": score})
    return rows


def parse_csrf_token(html: str) -> str | None:
    """Extract csrf_token from a page."""
    soup = BeautifulSoup(html, "lxml")
    tag = soup.find("input", attrs={"name": "csrf_token"})
    if tag:
        return tag.get("value")
    meta = soup.find("meta", attrs={"name": "X-Csrf-Token"})
    if meta:
        return meta.get("content")
    return None


def parse_submission_verdict(html: str) -> list[dict]:
    """Parse recent submissions from user's submission page."""
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", class_="status-frame-datatable")
    if not table:
        return []

    submissions = []
    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue
        sub_id = cells[0].get_text(strip=True)
        problem = cells[3].get_text(strip=True)
        verdict_cell = cells[4]
        verdict = verdict_cell.get_text(strip=True)
        time_val = cells[5].get_text(strip=True) if len(cells) > 5 else ""
        memory_val = cells[6].get_text(strip=True) if len(cells) > 6 else ""
        submissions.append({
            "id": sub_id,
            "problem": problem,
            "verdict": verdict,
            "time": time_val,
            "memory": memory_val,
        })
    return submissions
