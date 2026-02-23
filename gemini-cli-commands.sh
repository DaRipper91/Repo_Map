#!/usr/bin/env bash
# gemini-cli-commands.sh
# Gemini CLI Reference Commands for repo-map & repository management
# github.com/DaRipper91
#
# Prerequisites:
#   npm install -g @google/gemini-cli
#   gemini auth
#
# Usage: Copy individual commands as needed. Run from your repo-map directory.
# ─────────────────────────────────────────────────────────────────────────────

REPO_MAP_DIR="$HOME/repo-map"
REPOS_DIR="$HOME/repos"
USERNAME="DaRipper91"

# ═════════════════════════════════════════════════════════════════════════════
# SECTION A: PROFILE-LEVEL ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

# A1: Full profile overview — pipe repo list to Gemini for instant analysis
gh repo list $USERNAME --limit 100 \
  --json name,description,pushedAt,diskUsage,languages \
  | gemini 'Analyze this GitHub repository list.
    1. Group repos by apparent purpose/technology
    2. Flag repos that appear to be duplicates
    3. Flag repos with no push in 12+ months (stale)
    4. Suggest which to archive, merge, or keep
    Output as a clean markdown table with columns: Repo | Group | Status | Action'


# A2: Summarize the latest sync changes
cat "$REPO_MAP_DIR/_meta/change-report.md" \
  | gemini 'Summarize these repository changes in plain English.
    What was added, modified, or removed?
    Are there any patterns worth noting?
    Keep it to 3-5 sentences.'


# A3: Technology stack overview across all repos
cat "$REPO_MAP_DIR/README.md" \
  | gemini 'Based on this repo map summary, answer:
    1. What technology stacks are most common?
    2. Which repos look like they could be combined?
    3. Are there obvious gaps or redundancies?
    4. What is the most neglected part of this profile?
    Be concise and direct.'


# A4: Weekly activity digest from sync log
cat "$REPO_MAP_DIR/_meta/sync-log.md" \
  | gemini 'This is a GitHub repo sync log.
    Summarize the past week of activity:
    - Which repos are most active?
    - Which repos appear stale?
    - How many total files were added/changed overall?
    - Any anomalies or unusual patterns?
    Output as a brief digest, 10 lines max.'


# ═════════════════════════════════════════════════════════════════════════════
# SECTION B: SINGLE FILE REVIEWS
# ═════════════════════════════════════════════════════════════════════════════

# B1: Review a specific file for performance + quality (edit FILEPATH)
FILEPATH="$REPOS_DIR/my-app/src/components/Dashboard.tsx"
cat "$FILEPATH" \
  | gemini 'Review this file for:
    1. PERFORMANCE: unnecessary re-renders, missing memo, expensive ops
    2. ACCESSIBILITY: missing ARIA, keyboard nav, semantic HTML
    3. CODE QUALITY: dead code, missing error handling, poor patterns
    Format: [HIGH/MED/LOW] Line N: Issue — Fix
    Be specific and concise.'


# B2: Quick syntax/logic check
FILEPATH="$REPOS_DIR/my-app/src/utils/helpers.ts"
cat "$FILEPATH" \
  | gemini 'Review this TypeScript file.
    Find: bugs, type issues, missing edge cases, unused exports.
    Respond with a numbered list. If no issues, say "Looks clean."'


# B3: Generate a docstring/JSDoc comment for a file
FILEPATH="$REPOS_DIR/my-app/src/services/api.ts"
cat "$FILEPATH" \
  | gemini 'For each exported function in this file, write a JSDoc comment.
    Include: @param, @returns, @throws if applicable.
    Return ONLY the JSDoc comments, one per function, in order.'


# ═════════════════════════════════════════════════════════════════════════════
# SECTION C: DIRECTORY-LEVEL REVIEWS
# ═════════════════════════════════════════════════════════════════════════════

# C1: Review all TS/TSX files in a directory (adjust path)
TARGET_DIR="$REPOS_DIR/my-app/src"
find "$TARGET_DIR" \( -name '*.ts' -o -name '*.tsx' \) \
  | head -15 \
  | xargs -I{} sh -c 'echo "=== {} ==="; cat "{}"' \
  | gemini 'Review these TypeScript files for code quality.
    Group findings by file. Focus on:
    - Duplicate logic between files
    - Missing TypeScript types
    - Error handling gaps
    - Performance anti-patterns
    Use format: FILE: issue (severity)'


# C2: Find duplicate logic across a codebase
TARGET_DIR="$REPOS_DIR/my-app/src"
find "$TARGET_DIR" -name '*.ts' -o -name '*.tsx' \
  | head -20 \
  | xargs -I{} sh -c 'echo "=== {} ==="; cat "{}"' \
  | gemini 'Identify duplicated or very similar logic across these files.
    For each duplication: name it, show which files, suggest how to consolidate.
    If no duplicates, say "No significant duplication found."'


# ═════════════════════════════════════════════════════════════════════════════
# SECTION D: REPO MAP FILE ANALYSIS
# ═════════════════════════════════════════════════════════════════════════════

# D1: Compare two repos using their map files
REPO_A="$REPO_MAP_DIR/repos/project-alpha"
REPO_B="$REPO_MAP_DIR/repos/project-beta"
cat "$REPO_A/README.md" "$REPO_B/README.md" \
  | gemini 'Compare these two repository overviews.
    1. Do they serve similar or overlapping purposes?
    2. What does each have that the other lacks?
    3. Would combining them make sense? If so, which is the better primary?
    4. What is the recommended action? Be direct.'


# D2: Generate file descriptions for a pending map.md
MAPFILE="$REPO_MAP_DIR/repos/my-repo/src/map.md"
CONTENT=$(cat "$MAPFILE")
UPDATED=$(echo "$CONTENT" | gemini \
  'In this markdown file, replace each line:
   - **Description:** *(pending AI description pass)*
   with a real 3-4 sentence technical description based on the filename,
   path, and directory context visible in this file.
   Return the COMPLETE file with ONLY those lines replaced.
   Do not add any commentary, preamble, or markdown fences.')
echo "$UPDATED" > "$MAPFILE"
echo "✅ Updated: $MAPFILE"


# D3: Batch description pass — process all pending map.md files
find "$REPO_MAP_DIR/repos" -name 'map.md' | while read mapfile; do
    if grep -q 'pending AI description pass' "$mapfile"; then
        echo "📝 Processing: $mapfile"
        CONTENT=$(cat "$mapfile")
        UPDATED=$(echo "$CONTENT" | gemini \
            'Replace each occurrence of:
             - **Description:** *(pending AI description pass)*
             with a real 3-4 sentence technical description based on the
             filename and directory context in this map.
             Return ONLY the complete updated file. No commentary.')
        echo "$UPDATED" > "$mapfile"
        echo "   ✅ Done"
        sleep 2  # Avoid rate limiting
    fi
done
echo "🎉 Description pass complete."


# ═════════════════════════════════════════════════════════════════════════════
# SECTION E: PACKAGE & DEPENDENCY AUDITS
# ═════════════════════════════════════════════════════════════════════════════

# E1: Audit package.json for outdated/vulnerable deps
REPO="$REPOS_DIR/my-app"
cat "$REPO/package.json" \
  | gemini 'Audit this package.json.
    List:
    1. Packages likely outdated (major version behind current)
    2. Packages with known security concerns
    3. Packages that could be replaced with modern built-ins or lighter alternatives
    4. Any dev dependencies that should be moved to prod or vice versa
    Be specific with version numbers where you know them.'


# E2: Check all package.json files across cloned repos
find "$REPOS_DIR" -maxdepth 2 -name 'package.json' \
  | xargs -I{} sh -c 'echo "=== {} ==="; cat "{}"' \
  | gemini 'Review these package.json files from multiple repos.
    Identify:
    1. Packages used in multiple repos that should be standardized to one version
    2. Any repo using a dramatically outdated version of a common package
    3. Packages appearing only once that seem out of place
    Output as a table: Package | Repos | Version Spread | Concern'


# ═════════════════════════════════════════════════════════════════════════════
# SECTION F: COMMIT MESSAGE & PR ASSISTANCE
# ═════════════════════════════════════════════════════════════════════════════

# F1: Generate a commit message for staged changes
git -C "$REPOS_DIR/my-app" diff --cached \
  | gemini 'Write a conventional commit message for these changes.
    Format: type(scope): description
    Types: feat, fix, refactor, docs, style, test, chore
    Keep under 72 characters. Add a brief body if needed.
    Return ONLY the commit message, nothing else.'


# F2: Generate a PR description from a branch diff
REPO="$REPOS_DIR/my-app"
git -C "$REPO" log main..HEAD --oneline \
  | gemini 'Write a GitHub Pull Request description for these commits.
    Include: Summary, Changes Made, Testing Notes, Screenshots needed (yes/no).
    Keep it professional and concise.'


# ═════════════════════════════════════════════════════════════════════════════
# SECTION G: UTILITIES
# ═════════════════════════════════════════════════════════════════════════════

# G1: Export repo inventory to CSV with Gemini-generated summaries
gh repo list $USERNAME --limit 100 \
  --json name,description,pushedAt,diskUsage,isPrivate \
  | gemini 'Convert this JSON to a clean CSV with headers:
    name,description,last_push,size_kb,is_private,suggested_action
    For suggested_action, add: keep / archive / review based on age and size.
    Return ONLY the CSV, no markdown fences.' \
  > "$REPO_MAP_DIR/_meta/repo-inventory.csv"
echo "✅ Saved to _meta/repo-inventory.csv"


# G2: Quick README quality check
REPO="$REPOS_DIR/my-app"
cat "$REPO/README.md" \
  | gemini 'Rate this README.md on a scale of 1-10 and explain why.
    Check for: project description, installation steps, usage examples,
    contribution guide, license info.
    List what is missing and how to improve it.'
