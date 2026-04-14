import json
import os
from pathlib import Path

DEFAULT_LANGUAGES = {
    ".cpp": {
        "compile": "g++ -std=c++20 -O2 -o {output} {source}",
        "run": "./{output}",
        "cf_lang_id": 91,
    },
    ".py": {
        "compile": None,
        "run": "python3 {source}",
        "cf_lang_id": 31,
    },
    ".java": {
        "compile": "javac {source}",
        "run": "java -cp . {classname}",
        "cf_lang_id": 36,
    },
}

DEFAULT_TEMPLATES = {
    ".cpp": '#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n    ios::sync_with_stdio(false);\n    cin.tie(nullptr);\n    \n    return 0;\n}\n',
    ".py": "import sys\ninput = sys.stdin.readline\n\n",
    ".java": 'import java.util.*;\n\npublic class Main {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        \n    }\n}\n',
}


class Config:
    def __init__(self, config_dir: Path | None = None):
        self.config_dir = config_dir or Path.home() / ".cf"
        self.config_file = self.config_dir / "config.json"
        self.session_file = self.config_dir / "session.json"
        self.templates_dir = self.config_dir / "templates"

        self.workspace = Path.home() / "cf"
        self.default_language = ".cpp"
        self.languages = dict(DEFAULT_LANGUAGES)
        self.test_timeout = 5

        if self.config_file.exists():
            self._load()

    def _load(self):
        data = json.loads(self.config_file.read_text())
        if "workspace" in data:
            self.workspace = Path(data["workspace"]).expanduser()
        if "default_language" in data:
            self.default_language = data["default_language"]
        if "test_timeout" in data:
            self.test_timeout = data["test_timeout"]
        if "languages" in data:
            for ext, overrides in data["languages"].items():
                if ext in self.languages:
                    self.languages[ext].update(overrides)
                else:
                    self.languages[ext] = overrides

    def save(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        data = {
            "workspace": str(self.workspace),
            "default_language": self.default_language,
            "test_timeout": self.test_timeout,
            "languages": self.languages,
        }
        self.config_file.write_text(json.dumps(data, indent=2))

    def get_template(self, ext: str) -> str:
        ext_name = {".cpp": "main.cpp", ".py": "main.py", ".java": "Main.java"}
        custom = self.templates_dir / ext_name.get(ext, f"main{ext}")
        if custom.exists():
            return custom.read_text()
        return DEFAULT_TEMPLATES.get(ext, "")

    def save_session(self, cookies: dict):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.session_file.write_text(json.dumps(cookies, indent=2))
        os.chmod(self.session_file, 0o600)

    def load_session(self) -> dict | None:
        if self.session_file.exists():
            return json.loads(self.session_file.read_text())
        return None
