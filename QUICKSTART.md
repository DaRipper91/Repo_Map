# 🗂️ Repo-Map Quick Start & Cheat Sheet
**GitHub Profile Mirror & Repository Management System**  
**Profile:** DaRipper91 | **Repo:** github.com/DaRipper91/repo-map

---

## ⚡ Setup in 5 Minutes

```bash
# 1. Create the repo
gh repo create DaRipper91/repo-map --public
gh repo clone DaRipper91/repo-map && cd repo-map

# 2. Copy the files from this bundle into repo-map/:
#    sync_repo_map.py      → root of repo
#    sync.yml              → .github/workflows/sync.yml

# 3. Add GH_TOKEN secret
#    github.com/DaRipper91/repo-map/settings/secrets/actions
#    → New secret → Name: GH_TOKEN → Value: your PAT

# 4. Push and trigger first sync
git add -A && git commit -m "🚀 setup" && git push
gh workflow run sync.yml && gh run watch
```

---

## 📁 Files in This Bundle

| File | Purpose |
|------|---------|
| `repo-map-guide.docx` | Full reference manual (this is everything) |
| `sync_repo_map.py` | Drop into root of repo-map — main sync script |
| `sync.yml` | Drop into `.github/workflows/` — cron automation |
| `jules-prompts.md` | Copy prompts into Jules at jules.google.com |
| `gemini-cli-commands.sh` | Shell commands using Gemini CLI |
| `QUICKSTART.md` | This file |

---

## 🕐 Cron Schedule

```
0 0,6,12,18 * * *   →   Midnight, 6am, 12pm, 6pm UTC (4x daily)
```

Change the schedule in `sync.yml` under the `cron:` key.

---

## 🔧 Most Used Commands

```bash
# Sync
gh workflow run sync.yml              # Trigger manual sync
gh run watch                          # Watch sync live
python sync_repo_map.py --verbose     # Run sync locally

# Repo management
gh repo list DaRipper91 --limit 100  # List all repos
gh repo archive DaRipper91/REPO      # Archive a repo
gh repo delete DaRipper91/REPO       # Delete (permanent!)

# Check API limits
gh api rate_limit | jq '.rate'

# Quick analysis with Gemini CLI
gh repo list DaRipper91 --limit 100 --json name,description,pushedAt \
  | gemini 'Group these repos by purpose and flag duplicates'
```

---

## 🤖 AI Tools Summary

### Jules (jules.google.com) — For batch async tasks:
- **Prompt 1:** Detect duplicate repos → generates `_meta/consolidation-plan.md`
- **Prompt 2:** Fill in file descriptions → updates all `map.md` placeholders
- **Prompt 3:** Code review → generates `_meta/reviews/[repo]-review.md`
- **Prompt 4:** Merge two repos → moves source into `legacy/` in target
- **Prompt 5:** Stale repo audit
- **Prompt 6:** Tech stack mapping

### Gemini CLI — For interactive/piped analysis:
- Section A: Profile-level analysis
- Section B: Single file reviews
- Section C: Directory reviews
- Section D: Map file analysis + description generation
- Section E: Dependency audits
- Section F: Commit messages & PR descriptions

---

## 📖 Full Guide
See `repo-map-guide.docx` for the complete reference including:
- All setup steps with detailed instructions
- Complete cron reference table with UTC conversion
- All troubleshooting scenarios
- Workflow playbooks (audit, dedup sprint, review sprint)
- Full gh CLI + git command reference
