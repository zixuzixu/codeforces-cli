import asyncio
import atexit
import os
import shutil
import subprocess
import threading
import time

import nodriver as uc
from nodriver import cdp

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

_xvfb_proc = None


def _ensure_display():
    """Start Xvfb if no display is available."""
    global _xvfb_proc
    if os.environ.get("DISPLAY"):
        return
    if not shutil.which("Xvfb"):
        raise RuntimeError(
            "No display and Xvfb not found. Install xvfb:\n"
            "  sudo apt install xvfb"
        )
    for display_num in range(99, 200):
        if not os.path.exists(f"/tmp/.X{display_num}-lock"):
            break
    display = f":{display_num}"
    _xvfb_proc = subprocess.Popen(
        ["Xvfb", display, "-screen", "0", "1280x720x24", "-nolisten", "tcp"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    os.environ["DISPLAY"] = display
    atexit.register(_stop_xvfb)
    time.sleep(0.3)
    if _xvfb_proc.poll() is not None:
        raise RuntimeError(
            f"Xvfb failed to start on display {display} "
            f"(exit code {_xvfb_proc.returncode})"
        )


def _stop_xvfb():
    global _xvfb_proc
    if _xvfb_proc:
        _xvfb_proc.terminate()
        try:
            _xvfb_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _xvfb_proc.kill()
            _xvfb_proc.wait(timeout=2)
        _xvfb_proc = None


class _LoopThread:
    """A dedicated thread running an asyncio event loop for nodriver."""

    def __init__(self):
        self._loop = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._ready = threading.Event()
        self._thread.start()
        self._ready.wait()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._ready.set()
        self._loop.run_forever()

    def run(self, coro, timeout=120):
        """Submit a coroutine and block until it returns."""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result(timeout=timeout)

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


class CodeforcesClient:
    def __init__(self, config: Config):
        self.config = config
        self._loop_thread = None
        self._browser = None
        self._page = None
        self._started = False
        atexit.register(self.close)

    def _ensure_browser(self):
        if not self._started:
            _ensure_display()
            self._loop_thread = _LoopThread()
            self._loop_thread.run(self._start_browser())
            self._started = True

    async def _start_browser(self):
        self._browser = await uc.start(headless=False)
        self._page = await self._browser.get("about:blank")

        cookies = self.config.load_session()
        if cookies:
            for name, value in cookies.items():
                await self._page.send(cdp.network.set_cookie(
                    name=name, value=value,
                    domain=".codeforces.com", path="/",
                ))

    def close(self):
        if self._browser:
            try:
                self._browser.stop()
            except Exception:
                pass
            self._browser = None
        if self._loop_thread:
            try:
                self._loop_thread.stop()
            except Exception:
                pass
            self._loop_thread = None
        self._started = False

    # ── HTTP helpers ───────────────────────────────────────────────

    def _get(self, path: str) -> str:
        self._ensure_browser()
        return self._loop_thread.run(self._async_get(path))

    async def _async_get(self, path: str) -> str:
        self._page = await self._browser.get(f"{BASE_URL}{path}")
        # Wait for page to fully load (Cloudflare challenge + JS rendering)
        for _ in range(30):
            await self._page.sleep(1)
            html = await self._page.get_content()
            if "Just a moment" in html:
                continue
            # Wait for document to finish loading
            ready = await self._page.evaluate("document.readyState")
            if ready == "complete" and len(html) > 2000:
                return html
        html = await self._page.get_content()
        if "Just a moment" in html:
            raise RuntimeError(
                "Cloudflare challenge did not resolve after 30s.\n"
                "Try: cf login  (to refresh your session cookies)"
            )
        return html

    def _post(self, path: str, data: dict) -> dict:
        self._ensure_browser()
        return self._loop_thread.run(self._async_post(path, data))

    async def _async_post(self, path: str, data: dict) -> dict:
        result = await self._page.evaluate(
            """async (url, data) => {
                const params = new URLSearchParams();
                for (const [k, v] of Object.entries(data)) params.append(k, v);
                const resp = await fetch(url, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: params.toString(),
                });
                return {text: await resp.text(), url: resp.url};
            }""",
            f"{BASE_URL}{path}", data,
        )
        if isinstance(result, dict) and "Just a moment" in result.get("text", ""):
            raise RuntimeError(
                "Cloudflare blocked the POST request.\n"
                "Try: cf login  (to refresh your session cookies)"
            )
        return result

    # ── Auth ──────────────────────────────────────────────────────

    def is_logged_in(self) -> bool:
        html = self._get("/")
        return "/enter" not in html and "/profile/" in html

    def login_with_cookies(self, cookie_string: str) -> bool:
        self._ensure_browser()
        cookies = {}
        for pair in cookie_string.split(";"):
            pair = pair.strip()
            if "=" in pair:
                name, value = pair.split("=", 1)
                cookies[name.strip()] = value.strip()

        async def _set():
            for name, value in cookies.items():
                await self._page.send(cdp.network.set_cookie(
                    name=name, value=value,
                    domain=".codeforces.com", path="/",
                ))
        self._loop_thread.run(_set())

        html = self._get("/")
        if "/enter" not in html and "/profile/" in html:
            self.config.save_session(cookies)
            return True
        return False

    # ── Contest / Problem ─────────────────────────────────────────

    def get_contest_list(self) -> list[dict]:
        return parse_contest_list(self._get("/contests"))

    def get_contest_problems(self, contest_id: str) -> list[dict]:
        return parse_contest_problems(self._get(f"/contest/{contest_id}"))

    def get_problem_page(self, contest_id: str, problem_id: str) -> str:
        return self._get(f"/contest/{contest_id}/problem/{problem_id}")

    def get_problem_samples(self, contest_id: str, problem_id: str) -> list[tuple[str, str]]:
        return parse_sample_tests(self.get_problem_page(contest_id, problem_id))

    def get_problem_statement(self, contest_id: str, problem_id: str) -> str:
        return parse_problem_statement(self.get_problem_page(contest_id, problem_id))

    def get_standings(self, contest_id: str) -> list[dict]:
        return parse_standings(self._get(f"/contest/{contest_id}/standings"))

    # ── Submissions ───────────────────────────────────────────────

    def get_status(self, contest_id: str | None = None) -> list[dict]:
        if contest_id:
            html = self._get(f"/contest/{contest_id}/my")
        else:
            html = self._get("/submissions/my")
        return parse_submission_verdict(html)

    def submit(self, contest_id: str, problem_id: str, source_code: str, lang_id: int) -> str:
        """Submit solution. Returns submission ID."""
        html = self._get(f"/contest/{contest_id}/submit")
        csrf = parse_csrf_token(html)
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
        resp = self._post(f"/contest/{contest_id}/submit?csrf_token={csrf}", data)

        if "You have submitted exactly the same code before" in resp["text"]:
            raise RuntimeError("Duplicate submission — you submitted this exact code before")
        if "submit" in resp["url"] and "my" not in resp["url"]:
            raise RuntimeError("Submission failed. Check your login status.")

        verdict_data = parse_submission_verdict(resp["text"])
        if verdict_data:
            return verdict_data[0]["id"]
        return ""

    def get_submission_verdict(self, contest_id: str, submission_id: str) -> dict | None:
        verdicts = parse_submission_verdict(self._get(f"/contest/{contest_id}/my"))
        for v in verdicts:
            if v["id"] == submission_id:
                return v
        return None
