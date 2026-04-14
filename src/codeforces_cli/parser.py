from bs4 import BeautifulSoup


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
    """Parse contest list from /contests page."""
    soup = BeautifulSoup(html, "lxml")
    rows = []
    table = soup.find("div", class_="datatable")
    if not table:
        return rows

    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < 2:
            continue
        name = cells[0].get_text(strip=True)
        time_str = cells[1].get_text(strip=True) if len(cells) > 1 else ""
        contest_id = ""
        link = cells[0].find("a")
        if link and link.get("href"):
            parts = link["href"].strip("/").split("/")
            if len(parts) >= 2:
                contest_id = parts[-1]
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
