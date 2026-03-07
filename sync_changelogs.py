#!/usr/bin/env python3
"""
sync_changelogs.py
Mirrors CHANGELOG.md from every repo into repo-map and builds a cross-profile index.
Called automatically at the end of sync_repo_map.py.
"""

import subprocess
import json
import base64
import datetime
import re
from pathlib import Path

USERNAME    = "DaRipper91"
OUTPUT_DIR  = Path("repos")
META_DIR    = Path("_meta")
INDEX_FILE  = META_DIR / "changelog-index.md"


def run(cmd, silent=True):
    try:
        return subprocess.check_output(cmd, shell=False, text=True,
                                       stderr=subprocess.DEVNULL).strip()
    except subprocess.CalledProcessError:
        return None


def fetch_changelog(username, repo_name, branch="main"):
    """Fetch CHANGELOG.md content via GitHub API. Returns text or None."""
    raw = run(
        ["gh", "api", f"repos/{username}/{repo_name}/contents/CHANGELOG.md"]
    )
    if raw:
        try:
            data = json.loads(raw)
            content = data.get("content", "")
            return base64.b64decode(content.replace("\n", "")).decode("utf-8", errors="ignore")
        except Exception:
            pass
    return None


def extract_latest_entry(changelog_text):
    """Pull date and summary from the most recent ## [date] entry."""
    if not changelog_text:
        return None, None
    matches = list(re.finditer(r'^## \[(\d{4}-\d{2}-\d{2})\]', changelog_text, re.MULTILINE))
    if not matches:
        return None, None
    first = matches[0]
    date_label = first.group(1)
    entry_block = changelog_text[first.start():matches[1].start()] if len(matches) > 1 else changelog_text[first.start():]
    summary_match = re.search(r'###\s+💡\s+What Changed\s*\n(.*?)(?=###|\Z)', entry_block, re.DOTALL)
    summary = ""
    if summary_match:
        bullets = [l.strip() for l in summary_match.group(1).strip().splitlines() if l.strip().startswith("-")][:2]
        summary = " ".join(b.lstrip("- ") for b in bullets)[:200]
    return date_label, summary


def run_sync(repos, username=None):
    """Mirror changelogs and build index. Called from sync_repo_map.py."""
    if username:
        global USERNAME
        USERNAME = username

    META_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)

    now_str = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    index_rows = []
    synced = 0
    missing = 0

    for repo in repos:
        name   = repo.get("name", "")
        branch = (repo.get("defaultBranchRef") or {}).get("name", "main")
        content = fetch_changelog(USERNAME, name, branch)
        dest    = OUTPUT_DIR / name / "CHANGELOG.md"

        if content:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")
            date_label, summary = extract_latest_entry(content)
            index_rows.append({
                "repo": name, "date": date_label or "unknown",
                "summary": summary or "_No summary extracted._", "has_change": True,
            })
            synced += 1
            print(f"   ✅ {name}: changelog mirrored")
        else:
            if dest.exists():
                dest.unlink()
            index_rows.append({
                "repo": name, "date": "—",
                "summary": "_No CHANGELOG.md in this repo._", "has_change": False,
            })
            missing += 1

    index_rows.sort(key=lambda r: r["date"], reverse=True)

    lines = [
        "# Changelog Index\n\n",
        f"> Mirrored from all repos in [{USERNAME}](https://github.com/{USERNAME}).  \n",
        f"> Last updated: {now_str}  \n",
        f"> Repos with changelog: {synced} / {synced + missing}\n\n",
        "---\n\n",
        "| Repo | Latest Entry | Summary |\n",
        "|------|-------------|--------|\n",
    ]
    for row in index_rows:
        link = f"[{row['repo']}](../{row['repo']}/CHANGELOG.md)" if row["has_change"] else row["repo"]
        lines.append(f"| {link} | {row['date']} | {row['summary']} |\n")

    lines += ["\n---\n\n", "## Repos Without a Changelog\n\n",
              "_These repos have no CHANGELOG.md. Add `changelog-workflow.yml` to enable._\n\n"]
    for row in index_rows:
        if not row["has_change"]:
            lines.append(f"- `{row['repo']}`\n")

    INDEX_FILE.write_text("".join(lines), encoding="utf-8")
    print(f"   📄 Changelog index: {synced} mirrored, {missing} without changelog")
    return synced, missing
