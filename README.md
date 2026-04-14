# codeforces-cli

Codeforces CLI tool. Login, browse contests, download problems with test cases, test locally, submit, and check verdicts.

## Install

```bash
git clone https://github.com/zixuzixu/codeforces-cli.git
cd codeforces-cli
uv tool install .
```

## Login

Codeforces uses Cloudflare Turnstile, so login works by importing cookies from your browser:

1. Open [codeforces.com](https://codeforces.com) in your browser and log in
2. Open DevTools (F12) → Console → run `document.cookie`
3. Copy the output

```bash
cf login
# Paste the cookie string when prompted
```

## Commands

### Contests

```bash
cf contest list              # upcoming and recent contests
cf contest info 1920         # problem list for contest 1920
cf standings 1920            # contest standings
```

### Download Problems

```bash
cf download 1920             # download all problems + test cases for contest 1920
cf parse 1920A               # download single problem
```

Downloads to `~/cf/<contest>/<problem>/`:

```
~/cf/1920/A/
├── problem.txt    # problem statement
├── main.cpp       # source template
├── in1.txt        # sample input
└── out1.txt       # expected output
```

### Test Locally

```bash
cd ~/cf/1920/A
# edit main.cpp, then:
cf test                      # run against all sample cases
cf run                       # compile, run, show input/output/expected side by side
```

Both commands save actual output to `ans1.txt`, `ans2.txt`, etc.

### Submit

```bash
cf submit                    # submit from current directory
cf submit 1920A              # submit specific problem
cf status 1920               # check recent verdicts
```

### Other

```bash
cf open 1920A                # open problem in browser
```

## Multi-language Support

Auto-detects language from file extension. Defaults configurable in `~/.cf/config.json`:

| Extension | Compiler | CF Language ID |
|-----------|----------|---------------|
| `.cpp` | `g++ -std=c++20 -O2` | 91 (GNU G++20) |
| `.py` | `python3` | 31 (Python 3) |
| `.java` | `javac` + `java` | 36 (Java 21) |

Custom templates: place files in `~/.cf/templates/` (e.g., `main.cpp`, `main.py`).

## Configuration

Config file: `~/.cf/config.json`

```json
{
  "workspace": "~/cf",
  "default_language": ".cpp",
  "test_timeout": 5,
  "languages": {
    ".cpp": {
      "compile": "g++ -std=c++20 -O2 -o {output} {source}",
      "run": "./{output}",
      "cf_lang_id": 91
    }
  }
}
```
