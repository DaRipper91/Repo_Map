#!/usr/bin/env python3
"""
sync_repo_map.py — Repo-Map Sync Script
GitHub Profile Mirror for DaRipper91

Runs every 2 hours via GitHub Actions.
Mirrors all repos as structured Markdown file maps.
At the end, calls sync_changelogs to mirror all CHANGELOG.md files.

Usage:
    python sync_repo_map.py
    python sync_repo_map.py --verbose
    python sync_repo_map.py --repo my-specific-repo
"""

import subprocess
import json
import os
import sys
import datetime
import hashlib
import argparse
from pathlib import Path

# ── Configuration ──────────────────────────────────────────────────────────────
USERNAME    = "DaRipper91"
OUTPUT_DIR  = Path("repos")
META_DIR    = Path("_meta")
REVIEWS_DIR = META_DIR / "reviews"
PREV_HASH   = META_DIR / ".last_hashes.json"
LOG_FILE    = META_DIR / "sync-log.md"
CHANGE_FILE = META_DIR / "change-report.md"

# ── Argument Parsing ───────────────────────────────────────────────────────────
def get_args():
    parser = argparse.ArgumentParser(description="Sync GitHub profile to repo-map")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--repo", type=str, help="Only sync a single repo by name")
    parser.add_argument("--dry-run", action="store_true", help="Don't write any files")
    return parser.parse_args()

# Global args used by log() and save_hashes()
args = argparse.Namespace(verbose=False, dry_run=False, repo=None)

def log(msg):
    if args and args.verbose:
        print(f"  {msg}")

def run(cmd, silent=False):
    try:
        result = subprocess.check_output(cmd, shell=False, text=True, stderr=subprocess.PIPE)
        return result.strip()
    except subprocess.CalledProcessError as e:
        if not silent:
            cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
            print(f"  ⚠️  Command failed: {cmd_str}\n     {e.stderr.strip()}", file=sys.stderr)
        return None

# ── Setup ──────────────────────────────────────────────────────────────────────
for d in [OUTPUT_DIR, META_DIR, REVIEWS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

def load_hashes():
    if PREV_HASH.exists():
        try:
            return json.loads(PREV_HASH.read_text())
        except json.JSONDecodeError:
            return {}
    return {}

def save_hashes(h):
    if not args.dry_run:
        PREV_HASH.write_text(json.dumps(h, indent=2))

prev_hashes = load_hashes()
curr_hashes = {}
LOG         = []
CHANGES     = []
total_files = 0
start       = datetime.datetime.now(datetime.timezone.utc)
now         = start
now_str     = now.strftime("%Y-%m-%d %H:%M UTC")

print(f"🔄 Repo-Map Sync starting: {now_str}")
print(f"   Profile: {USERNAME}")

# ── Fetch repo list ────────────────────────────────────────────────────────────
if args.repo:
    repo_data_raw = run(["gh", "api", f"repos/{USERNAME}/{args.repo}"])
    if not repo_data_raw:
        print(f"❌ Could not fetch repo: {args.repo}")
        sys.exit(1)
    try:
        repo_item = json.loads(repo_data_raw)
        repos = [{
            "name": repo_item.get("name"),
            "defaultBranchRef": {"name": repo_item.get("default_branch")},
            "pushedAt": repo_item.get("pushed_at"),
            "description": repo_item.get("description")
        }]
    except json.JSONDecodeError:
        print(f"❌ Failed to parse repo data for: {args.repo}")
        sys.exit(1)
else:
    repo_json = run([
        "gh", "repo", "list", USERNAME, "--limit", "200",
        "--json", "name,defaultBranchRef,pushedAt,description"
    ])
    if not repo_json:
        print("❌ Failed to fetch repo list. Is gh authenticated?")
        sys.exit(1)
    repos = json.loads(repo_json)

print(f"   Repos found: {len(repos)}")

repo_summary = []

for repo in repos:
    name   = repo.get("name", "")
    branch = (repo.get("defaultBranchRef") or {}).get("name", "main")
    desc   = (repo.get("description") or "No description provided.").strip()
    pushed = (repo.get("pushedAt") or "unknown")[:10]

    log(f"Processing: {name} [{branch}]")

    tree_raw = run(
        ["gh", "api", f"repos/{USERNAME}/{name}/git/trees/{branch}?recursive=1"],
        silent=True
    )
    if not tree_raw:
        msg = f"⚠️ Skipped {name} — could not fetch tree"
        print(f"   {msg}")
        LOG.append(msg)
        continue

    try:
        tree_data = json.loads(tree_raw)
    except json.JSONDecodeError:
        LOG.append(f"⚠️ Skipped {name} — malformed tree response")
        continue

    if tree_data.get("truncated"):
        LOG.append(f"⚠️ {name} — tree truncated. Only partial map available.")

    files = [f for f in tree_data.get("tree", []) if f.get("type") == "blob"]
    total_files += len(files)

    dir_map = {}
    for f in files:
        parent = str(Path(f["path"]).parent)
        dir_map.setdefault(parent, []).append(f["path"])

    repo_out = OUTPUT_DIR / name
    repo_out.mkdir(parents=True, exist_ok=True)

    for dir_path, file_list in dir_map.items():
        out_path = repo_out / dir_path / "map.md"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        lines = [
            f"# File Map: `{dir_path}`\n\n",
            f"**Repo:** [{name}](https://github.com/{USERNAME}/{name})  \n",
            f"**Branch:** `{branch}`  \n",
            f"**Directory:** `{dir_path}`  \n",
            f"**File Count:** {len(file_list)}  \n\n",
            "---\n\n",
        ]

        for fp in sorted(file_list):
            fname = Path(fp).name
            ext   = Path(fp).suffix.lower()
            lines.append(f"## {fname}\n\n")
            lines.append(f"- **Repo:** `{name}`\n")
            lines.append(f"- **Branch:** `{branch}`\n")
            lines.append(f"- **Path:** `{fp}`\n")
            lines.append(f"- **Type:** `{ext or 'no extension'}`\n")
            lines.append(f"- **Description:** *(pending AI description pass)*\n\n")

        content = "".join(lines)
        h = hashlib.md5(content.encode()).hexdigest()
        key = f"{name}/{dir_path}"

        if key in prev_hashes:
            if prev_hashes[key] != h:
                CHANGES.append(f"🔄 Modified: `{name}/{dir_path}` ({len(file_list)} files)")
        else:
            CHANGES.append(f"✅ New: `{name}/{dir_path}` ({len(file_list)} files)")

        curr_hashes[key] = h
        if not args.dry_run:
            out_path.write_text(content, encoding="utf-8")

    dir_links = "\n".join(
        [f"- [{d}/](./{d}/map.md) — {len(dir_map[d])} files" for d in sorted(dir_map.keys())]
    )
    readme_content = (
        f"# {name}\n\n"
        f"**Profile:** [{USERNAME}](https://github.com/{USERNAME})  \n"
        f"**Branch:** `{branch}`  \n"
        f"**Last Push:** {pushed}  \n"
        f"**Files Indexed:** {len(files)}  \n"
        f"**Directories:** {len(dir_map)}  \n\n"
        f"**Description:** {desc}\n\n"
        f"---\n\n"
        f"## 📁 Directories\n\n"
        f"{dir_links}\n\n"
        f"---\n\n"
        f"*Generated by repo-map sync. Last updated: {now_str}*\n"
    )
    if not args.dry_run:
        Path("README.md").write_text("".join(readme_lines), encoding="utf-8")

    # ── Write sync log entry ───────────────────────────────────────────────────────
    log_entry = f"### Sync: {now_str}\n\n"
    log_entry += f"- **Repos:** {len(repos)}\n"
    log_entry += f"- **Files:** {total_files:,}\n"
    log_entry += f"- **Changes:** {len(CHANGES)}\n"
    log_entry += f"- **Duration:** {duration}s\n\n"
    log_entry += "\n".join([f"  - {l}" for l in LOG]) + "\n\n---\n\n"

    if not args.dry_run:
        existing_log = LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else "# Sync Log\n\n"
        header = "# Sync Log\n\n"
        updated_log = header + log_entry + existing_log.replace(header, "", 1)
        LOG_FILE.write_text(updated_log, encoding="utf-8")

    # ── Write change report ────────────────────────────────────────────────────────
    change_report = (
        f"# Change Report\n\n"
        f"**Run:** {now_str}  \n"
        f"**Repos Scanned:** {len(repos)}  \n"
        f"**Changes Found:** {len(CHANGES)}  \n\n"
        "---\n\n"
        + (("\n".join(CHANGES)) if CHANGES else "_No changes detected this run._")
        + "\n"
    )
    LOG.append(f"✅ {name}: {len(files)} files, {len(dir_map)} dirs")
    print(f"   ✅ {name}: {len(files)} files")

for old_key in prev_hashes:
    if old_key not in curr_hashes:
        CHANGES.append(f"🗑️ Removed: `{old_key}`")

save_hashes(curr_hashes)
duration = int((datetime.datetime.now(datetime.timezone.utc) - start).total_seconds())

change_block = "\n".join(CHANGES) if CHANGES else "_No changes detected._"

readme_lines = [
    "# 🗂️ DaRipper91 — Repo Map\n\n",
    f"> Auto-synced text-only mirror of all GitHub repositories for [{USERNAME}](https://github.com/{USERNAME}).\n\n",
    "---\n\n",
    f"**Last Sync:** {now_str}  \n",
    f"**Repos Mapped:** {len(repos)}  \n",
    f"**Total Files Indexed:** {total_files:,}  \n",
    f"**Sync Duration:** {duration}s  \n\n",
    "## 📊 Changes This Run\n\n",
    change_block + "\n\n",
    "## 📁 Repositories\n\n",
    "| Repo | Branch | Files | Last Push |\n",
    "|------|--------|-------|-----------|\n",
    "\n".join(repo_summary) + "\n\n",
    "## 🔗 Meta\n\n",
    "- [Sync Log](./_meta/sync-log.md)\n",
    "- [Change Report](./_meta/change-report.md)\n",
    "- [Changelog Index](./_meta/changelog-index.md)\n\n",
    "---\n\n",
    "*Synced automatically every 2 hours via GitHub Actions.*\n",
]
if not args.dry_run:
    Path("README.md").write_text("".join(readme_lines), encoding="utf-8")

log_entry = f"### Sync: {now_str}\n\n"
log_entry += f"- **Repos:** {len(repos)}\n"
log_entry += f"- **Files:** {total_files:,}\n"
log_entry += f"- **Changes:** {len(CHANGES)}\n"
log_entry += f"- **Duration:** {duration}s\n\n"
log_entry += "\n".join([f"  - {l}" for l in LOG]) + "\n\n---\n\n"

if not args.dry_run:
    existing_log = LOG_FILE.read_text(encoding="utf-8") if LOG_FILE.exists() else "# Sync Log\n\n"
    header = "# Sync Log\n\n"
    updated_log = header + log_entry + existing_log.replace(header, "", 1)
    LOG_FILE.write_text(updated_log, encoding="utf-8")

change_report = (
    f"# Change Report\n\n"
    f"**Run:** {now_str}  \n"
    f"**Repos Scanned:** {len(repos)}  \n"
    f"**Changes Found:** {len(CHANGES)}  \n\n"
    "---\n\n"
    + (("\n".join(CHANGES)) if CHANGES else "_No changes detected this run._")
    + "\n"
)
if not args.dry_run:
    CHANGE_FILE.write_text(change_report, encoding="utf-8")

print(f"\n✅ Sync complete. Repos: {len(repos)}, Files: {total_files:,}, Changes: {len(CHANGES)}, Duration: {duration}s")

# ── Changelog mirror ───────────────────────────────────────────────────────────
print('\n📋 Syncing changelogs...')
import sync_changelogs
sync_changelogs.run_sync(repos, USERNAME)
