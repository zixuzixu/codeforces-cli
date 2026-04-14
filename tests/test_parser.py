from pathlib import Path
from codeforces_cli.parser import (
    parse_sample_tests,
    parse_contest_problems,
    parse_contest_list,
    parse_standings,
    parse_csrf_token,
)


def test_parse_sample_tests():
    html = """
    <div class="sample-test">
        <div class="input"><pre class="input">3
1 2 3</pre></div>
        <div class="output"><pre>6</pre></div>
        <div class="input"><pre class="input">2
5 5</pre></div>
        <div class="output"><pre>10</pre></div>
    </div>
    """
    tests = parse_sample_tests(html)
    assert len(tests) == 2
    assert tests[0] == ("3\n1 2 3", "6")
    assert tests[1] == ("2\n5 5", "10")


def test_parse_contest_problems():
    html = """
    <table class="problems">
        <tr>
            <td class="id"><a href="/contest/1920/problem/A">A</a></td>
            <td><div><div><a href="/contest/1920/problem/A">Satisfying Constraints</a></div></div></td>
        </tr>
        <tr>
            <td class="id"><a href="/contest/1920/problem/B">B</a></td>
            <td><div><div><a href="/contest/1920/problem/B">Summation Game</a></div></div></td>
        </tr>
    </table>
    """
    problems = parse_contest_problems(html)
    assert len(problems) == 2
    assert problems[0]["id"] == "A"
    assert problems[0]["name"] == "Satisfying Constraints"
    assert problems[1]["id"] == "B"


def test_parse_csrf_token():
    html = '<input type="hidden" name="csrf_token" value="abc123def"/>'
    token = parse_csrf_token(html)
    assert token == "abc123def"


def test_parse_csrf_token_missing():
    token = parse_csrf_token("<html></html>")
    assert token is None
