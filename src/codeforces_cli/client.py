from curl_cffi import requests as cffi_requests
from codeforces_cli.config import Config
from codeforces_cli.parser import (
    parse_csrf_token,
    parse_sample_tests,
    parse_problem_statement,
    parse_contest_problems,
    parse_contest_list,
    parse_standings,
    parse_submission_verdict,
)

BASE_URL = "https://codeforces.com"


class CodeforcesClient:
    def __init__(self, config: Config):
        self.config = config
        self.base_url = BASE_URL
        self.session = cffi_requests.Session(impersonate="chrome")
        # Load saved session cookies
        cookies = config.load_session()
        if cookies:
            for name, value in cookies.items():
                self.session.cookies.set(name, value, domain=".codeforces.com")

    def _get(self, path: str) -> cffi_requests.Response:
        return self.session.get(f"{self.base_url}{path}")

    def _post(self, path: str, data: dict) -> cffi_requests.Response:
        return self.session.post(f"{self.base_url}{path}", data=data)

    def is_logged_in(self) -> bool:
        resp = self._get("/")
        return "/enter" not in resp.text and "/profile/" in resp.text

    def login_with_cookies(self, cookie_string: str) -> bool:
        """Login by importing cookies from browser.

        cookie_string: raw cookie header value from browser DevTools,
        e.g. "JSESSIONID=abc; cf_clearance=xyz; ..."
        """
        # Parse cookie string
        cookies = {}
        for pair in cookie_string.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, value = pair.split("=", 1)
                cookies[name.strip()] = value.strip()

        # Set cookies on session
        for name, value in cookies.items():
            self.session.cookies.set(name, value, domain=".codeforces.com")

        # Verify login
        resp = self._get("/")
        if "/enter" not in resp.text and "/profile/" in resp.text:
            self.config.save_session(cookies)
            return True
        return False

    def get_contest_list(self) -> list[dict]:
        resp = self._get("/contests")
        return parse_contest_list(resp.text)

    def get_contest_problems(self, contest_id: str) -> list[dict]:
        resp = self._get(f"/contest/{contest_id}")
        return parse_contest_problems(resp.text)

    def get_problem_page(self, contest_id: str, problem_id: str) -> str:
        """Fetch raw HTML for a problem page."""
        resp = self._get(f"/contest/{contest_id}/problem/{problem_id}")
        return resp.text

    def get_problem_samples(self, contest_id: str, problem_id: str) -> list[tuple[str, str]]:
        html = self.get_problem_page(contest_id, problem_id)
        return parse_sample_tests(html)

    def get_problem_statement(self, contest_id: str, problem_id: str) -> str:
        html = self.get_problem_page(contest_id, problem_id)
        return parse_problem_statement(html)

    def get_standings(self, contest_id: str) -> list[dict]:
        resp = self._get(f"/contest/{contest_id}/standings")
        return parse_standings(resp.text)

    def get_status(self, contest_id: str | None = None) -> list[dict]:
        if contest_id:
            resp = self._get(f"/contest/{contest_id}/my")
        else:
            resp = self._get("/submissions/my")
        return parse_submission_verdict(resp.text)

    def submit(self, contest_id: str, problem_id: str, source_code: str, lang_id: int) -> str:
        """Submit solution. Returns submission ID."""
        submit_url = f"/contest/{contest_id}/submit"
        resp = self._get(submit_url)
        csrf = parse_csrf_token(resp.text)
        if not csrf:
            raise RuntimeError(
                "Could not find csrf_token on submit page.\n"
                "This usually means Cloudflare blocked the request.\n"
                "Try: cf login  (to refresh your session cookies)"
            )

        data = {
            "csrf_token": csrf,
            "ftaa": "",
            "bfaa": "",
            "action": "submitSolutionFormSubmitted",
            "submittedProblemIndex": problem_id,
            "programTypeId": str(lang_id),
            "source": source_code,
        }
        resp = self._post(f"/contest/{contest_id}/submit?csrf_token={csrf}", data=data)

        if "You have submitted exactly the same code before" in resp.text:
            raise RuntimeError("Duplicate submission — you submitted this exact code before")
        if "submit" in resp.url and "my" not in resp.url:
            raise RuntimeError("Submission failed. Check your login status.")

        verdict_data = parse_submission_verdict(resp.text)
        if verdict_data:
            return verdict_data[0]["id"]
        return ""

    def get_submission_verdict(self, contest_id: str, submission_id: str) -> dict | None:
        """Poll a specific submission's verdict."""
        resp = self._get(f"/contest/{contest_id}/my")
        verdicts = parse_submission_verdict(resp.text)
        for v in verdicts:
            if v["id"] == submission_id:
                return v
        return None
