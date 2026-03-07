#!/usr/bin/env python3
"""
setup_changelogs.py
Helper script to deploy the Auto-Changelog system to all DaRipper91 repositories.

Usage:
    python setup_changelogs.py

Prerequisites:
    - gh CLI installed and authenticated (gh auth login)
    - python3 installed
"""

import subprocess
import json
import base64
import sys
import os

USERNAME = "DaRipper91"

# ── File 4: changelog-workflow.yml ─────────────────────────────────────────────
WORKFLOW_CONTENT = """name: Auto Changelog

on:
  push:
    branches:
      - main
      - master
    paths-ignore:
      - 'CHANGELOG.md'
      - '.github/**'
  workflow_dispatch:

permissions:
  contents: write

concurrency:
  group: changelog-${{ github.ref }}
  cancel-in-progress: false

jobs:
  update-changelog:
    name: Update CHANGELOG.md
    runs-on: ubuntu-latest
    timeout-minutes: 10

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.CHANGELOG_TOKEN || secrets.GITHUB_TOKEN }}

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install google-generativeai --quiet

      - name: Generate changelog entry
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
          GITHUB_TOKEN:   ${{ secrets.GITHUB_TOKEN }}
          REPO_NAME:      ${{ github.repository }}
          COMMIT_SHA:     ${{ github.sha }}
          PUSHER:         ${{ github.actor }}
          BRANCH:         ${{ github.ref_name }}
        run: python .github/scripts/update_changelog.py

      - name: Commit changelog
        run: |
          git config user.name  "changelog-bot"
          git config user.email "bot@users.noreply.github.com"
          git add CHANGELOG.md
          if git diff --cached --quiet; then
            echo "No changelog changes to commit."
          else
            git commit -m "docs: update CHANGELOG.md [skip ci]"
            git push
          fi
"""

# ── File 5: update_changelog.py ────────────────────────────────────────────────
# Using raw single-quotes to avoid backslash escaping issues
SCRIPT_CONTENT = r'''#!/usr/bin/env python3
"""
update_changelog.py
Generates a CHANGELOG.md entry on every push to main/master.
Place at: .github/scripts/update_changelog.py
"""

import subprocess
import os
import datetime
import re
import sys
from pathlib import Path

CHANGELOG_FILE  = Path("CHANGELOG.md")
MAX_DIFF_CHARS  = 12000
MAX_COMMITS     = 20
USE_AI          = bool(os.environ.get("GEMINI_API_KEY"))

REPO_NAME   = os.environ.get("REPO_NAME", "unknown/repo")
COMMIT_SHA  = os.environ.get("COMMIT_SHA", "")
PUSHER      = os.environ.get("PUSHER", "unknown")
BRANCH      = os.environ.get("BRANCH", "main")
SHORT_SHA   = COMMIT_SHA[:7] if COMMIT_SHA else "unknown"
NOW_UTC     = datetime.datetime.utcnow()
TIMESTAMP   = NOW_UTC.strftime("%Y-%m-%d %H:%M UTC")
DATE_LABEL  = NOW_UTC.strftime("%Y-%m-%d")


def run_git(args, fallback=""):
    try:
        return subprocess.check_output(["git"] + args, text=True, stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return fallback


def get_previous_sha():
    return run_git(["rev-parse", "HEAD~1"], fallback="HEAD~1")


def get_commits_since(since_sha):
    fmt = "%H|||%an|||%s|||%ad"
    raw = run_git(["log", f"{since_sha}..HEAD", f"--format={fmt}", "--date=short", f"--max-count={MAX_COMMITS}"])
    commits = []
    for line in raw.splitlines():
        if "|||" in line:
            parts = line.split("|||", 3)
            if len(parts) == 4:
                sha, author, msg, date = parts
                commits.append({"sha": sha[:7], "author": author, "message": msg.strip(), "date": date})
    return commits


def get_changed_files(since_sha):
    raw = run_git(["diff", "--name-status", f"{since_sha}..HEAD"])
    files = []
    for line in raw.splitlines():
        parts = line.split("\t", 1)
        if len(parts) == 2:
            files.append({"status": parts[0][0], "path": parts[1].strip()})
    return files


def get_diff(since_sha):
    diff = run_git(["diff", f"{since_sha}..HEAD", "--unified=3", "--no-color", "--diff-filter=ACMR"])
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[... diff trimmed for length ...]"
    return diff


def get_repo_description():
    for fname in ["README.md", "readme.md"]:
        p = Path(fname)
        if p.exists():
            for line in p.read_text(errors="ignore").splitlines():
                line = line.strip()
                if line and not line.startswith("#") and len(line) > 20:
                    return line[:200]
    return ""


STATUS_LABELS = {"A": "Added", "M": "Modified", "D": "Deleted", "R": "Renamed", "C": "Copied"}

EXT_GROUPS = {
    "Source Code": {".ts", ".tsx", ".js", ".jsx", ".py", ".go", ".rs", ".java", ".c", ".cpp", ".cs", ".rb", ".php", ".swift", ".kt"},
    "Styles":      {".css", ".scss", ".sass", ".less"},
    "Markup/Docs": {".md", ".mdx", ".html", ".htm", ".rst", ".txt"},
    "Config":      {".json", ".yaml", ".yml", ".toml", ".ini", ".env"},
    "Tests":       {".test.ts", ".test.js", ".spec.ts", ".spec.js", ".test.py"},
    "Assets":      {".png", ".jpg", ".jpeg", ".svg", ".gif", ".webp", ".ico"},
    "Build/Deploy":{".sh", "Dockerfile", "Makefile"},
}


def categorize_files(files):
    groups = {}
    for f in files:
        ext = Path(f["path"]).suffix.lower()
        cat = "Other"
        for group, exts in EXT_GROUPS.items():
            if ext in exts:
                cat = "Tests" if ("test" in f["path"].lower() or "spec" in f["path"].lower()) else group
                break
        groups.setdefault(cat, []).append(f)
    return groups


def generate_ai_section(commits, diff, repo_desc):
    if not USE_AI:
        return {
            "summary":    "_AI summary unavailable — set GEMINI_API_KEY secret to enable._",
            "fixed":      "_No AI analysis — commit messages above contain the details._",
            "next_steps": "_Add GEMINI_API_KEY to repository secrets for AI-powered suggestions._",
        }
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel("gemini-1.5-flash")
        commit_text = "\n".join(f"- [{c['sha']}] {c['message']} ({c['author']}, {c['date']})" for c in commits) or "No commits found."
        prompt = f"""You are a developer writing a changelog entry for a software project.

Repository: {REPO_NAME}
{f'Description: {repo_desc}' if repo_desc else ''}

Recent commits:
{commit_text}

Code diff (may be truncated):
```
{diff[:8000]}
```

Write exactly three sections. Be specific, technical, and concise.

Respond in this EXACT format with no other text:

SUMMARY:
- [what changed at a high level]
- [another key change if applicable]

FIXED:
- [specific bug or issue resolved — or "No fixes in this push." if none]

NEXT_STEPS:
- [logical next action based on what was changed]
- [another suggestion]
"""
        response = model.generate_content(prompt)
        text = response.text.strip()
        sections = {"summary": [], "fixed": [], "next_steps": []}
        current = None
        for line in text.splitlines():
            line = line.strip()
            if line.startswith("SUMMARY:"):      current = "summary"
            elif line.startswith("FIXED:"):      current = "fixed"
            elif line.startswith("NEXT_STEPS:"): current = "next_steps"
            elif line.startswith("- ") and current:
                sections[current].append(line)

        def fmt(bullets, fallback):
            return "\n".join(bullets) if bullets else fallback

        return {
            "summary":    fmt(sections["summary"],    "- Changes applied successfully."),
            "fixed":      fmt(sections["fixed"],      "- No specific fixes noted in this push."),
            "next_steps": fmt(sections["next_steps"], "- Review the changes and test in your environment."),
        }
    except Exception as e:
        print(f"  ⚠️  AI generation failed: {e}", file=sys.stderr)
        return {
            "summary":    "_AI generation failed — see commit messages above._",
            "fixed":      "_See commit messages._",
            "next_steps": "_Manual review recommended._",
        }


def build_entry(commits, files, ai, since_sha):
    repo_short = REPO_NAME.split("/")[-1] if "/" in REPO_NAME else REPO_NAME
    lines = [
        f"## [{DATE_LABEL}] — Push to `{BRANCH}` by @{PUSHER}\n",
        f"\n",
        f"> **Commit:** [`{SHORT_SHA}`](https://github.com/{REPO_NAME}/commit/{COMMIT_SHA})  \n",
        f"> **Time:** {TIMESTAMP}  \n",
        f"> **Comparing:** [`{since_sha[:7]}...{SHORT_SHA}`](https://github.com/{REPO_NAME}/compare/{since_sha[:7]}...{SHORT_SHA})\n",
        f"\n",
    ]

    lines += ["### 📋 Commits\n\n"]
    if commits:
        for c in commits:
            sha_link = f"[`{c['sha']}`](https://github.com/{REPO_NAME}/commit/{c['sha']})"
            lines.append(f"- {sha_link} — {c['message']} _{c['author']}_\n")
    else:
        lines.append("- _(No new commits detected)_\n")
    lines.append("\n")

    if files:
        groups = categorize_files(files)
        total = len(files)
        added = sum(1 for f in files if f["status"] == "A")
        mod   = sum(1 for f in files if f["status"] == "M")
        deld  = sum(1 for f in files if f["status"] == "D")
        lines += [f"### 📁 Files Changed  _{total} total ({added} added, {mod} modified, {deld} deleted)_\n\n"]
        for cat, cat_files in sorted(groups.items()):
            lines.append(f"**{cat}**\n")
            for f in cat_files:
                lines.append(f"- `{f['path']}` — {STATUS_LABELS.get(f['status'], f['status'])}\n")
            lines.append("\n")
    else:
        lines += ["### 📁 Files Changed\n\n- _(No file changes detected)_\n\n"]

    lines += [
        "### 💡 What Changed\n\n", ai["summary"] + "\n\n",
        "### 🔧 What Was Fixed\n\n", ai["fixed"] + "\n\n",
        "### 🚀 Suggested Next Steps\n\n", ai["next_steps"] + "\n\n",
        "---\n\n",
    ]
    return "".join(lines)


HEADER = """# Changelog

> Auto-generated on every push to `main`. Each entry includes commits,
> changed files grouped by type, an AI summary of what changed, what was
> fixed, and suggested next steps.
>
> **Format:** newest entries at the top.

---

"""


def load_existing():
    if not CHANGELOG_FILE.exists():
        return HEADER, ""
    content = CHANGELOG_FILE.read_text(encoding="utf-8")
    # Escaped regex for python string literal
    match = re.search(r'^## \[', content, re.MULTILINE)
    if match:
        return content[:match.start()], content[match.start():]
    return content, ""


def write_changelog(new_entry, existing_header, existing_entries):
    # Escaped regex for python string literal
    entry_blocks = re.split(r'(?=^## \[)', existing_entries, flags=re.MULTILINE)
    entry_blocks = [b for b in entry_blocks if b.strip()]
    kept = entry_blocks[:49]
    content = existing_header + new_entry + "\n".join(kept)
    CHANGELOG_FILE.write_text(content, encoding="utf-8")
    print(f"  ✅ Wrote CHANGELOG.md ({len(content):,} chars, {1 + len(kept)} entries)")


def main():
    print(f"📝 Changelog update: {REPO_NAME} @ {SHORT_SHA} [{BRANCH}]")
    print(f"   AI: {'enabled' if USE_AI else 'disabled — set GEMINI_API_KEY to enable'}")
    since_sha = get_previous_sha()
    commits   = get_commits_since(since_sha)
    files     = get_changed_files(since_sha)
    diff      = get_diff(since_sha)
    repo_desc = get_repo_description()
    print(f"   Commits: {len(commits)}, Files changed: {len(files)}")
    if not commits and not files:
        print("   Nothing to log. Exiting.")
        return
    ai      = generate_ai_section(commits, diff, repo_desc)
    entry   = build_entry(commits, files, ai, since_sha)
    header, existing = load_existing()
    write_changelog(entry, header, existing)
    print("✅ Done.")


if __name__ == "__main__":
    main()
'''


def run_command(cmd, input_data=None, silent=True):
    try:
        proc = subprocess.Popen(
            cmd, shell=False,
            text=True,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate(input=input_data)
        if proc.returncode != 0:
            if not silent:
                print(f"Error running: {cmd}\n{stderr}", file=sys.stderr)
            return None
        return stdout.strip()
    except Exception as e:
        if not silent:
            print(f"Exception running: {cmd}\n{e}", file=sys.stderr)
        return None

def put_file(repo, path, content, message):
    """Create or update a file via GitHub API."""
    # Check if file exists to get SHA
    check_cmd = ["gh", "api", f"repos/{USERNAME}/{repo}/contents/{path}"]
    existing = run_command(check_cmd, silent=True)

    sha = None
    if existing:
        try:
            data = json.loads(existing)
            if "sha" in data:
                sha = data["sha"]
                print(f"   ℹ️  Updating existing file: {path}")
            else:
                 # It might be a directory or something else?
                 pass
        except:
            pass
    else:
        print(f"   ✨ Creating new file: {path}")

    # Base64 encode content
    b64_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # Construct payload
    payload = {
        "message": message,
        "content": b64_content
    }
    if sha:
        payload["sha"] = sha

    payload_json = json.dumps(payload)

    # PUT request
    cmd = ["gh", "api", "--method", "PUT", f"repos/{USERNAME}/{repo}/contents/{path}", "--input", "-"]

    res = run_command(cmd, input_data=payload_json, silent=False)
    if res:
        print(f"   ✅ Success: {path}")
        return True
    else:
        print(f"   ❌ Failed to push: {path}")
        return False

def main():
    print(f"🚀 Starting Auto-Changelog Deployment for {USERNAME}...")

    # Check if gh is installed and authenticated
    status = run_command(["gh", "auth", "status"], silent=True)
    if status is None:
        print("❌ 'gh' CLI not found or not authenticated. Please run 'gh auth login'.")
        # For testing in sandbox where gh is missing, we might want to continue?
        # But for real usage, this is a hard stop.
        sys.exit(1)

    # List repos
    print("📋 Fetching repository list...")
    repos_json = run_command(["gh", "repo", "list", USERNAME, "--limit", "200", "--json", "name,defaultBranchRef,archived"], silent=False)
    if not repos_json:
        print("❌ Failed to fetch repos.")
        sys.exit(1)

    repos = json.loads(repos_json)
    print(f"   Found {len(repos)} repositories.")

    for repo in repos:
        name = repo["name"]
        if repo.get("archived"):
            print(f"⏭️  Skipping archived repo: {name}")
            continue

        if name == "repo-map":
            print(f"⏭️  Skipping repo-map (self)")
            continue

        print(f"\n📦 Processing: {name}")

        # Deploy workflow
        put_file(
            name,
            ".github/workflows/changelog-workflow.yml",
            WORKFLOW_CONTENT,
            "ci: add auto-changelog workflow"
        )

        # Deploy script
        put_file(
            name,
            ".github/scripts/update_changelog.py",
            SCRIPT_CONTENT,
            "ci: add changelog generation script"
        )

    print("\n🎉 Deployment complete!")

if __name__ == "__main__":
    main()
