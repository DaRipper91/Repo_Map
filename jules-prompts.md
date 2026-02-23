# Jules AI Prompts — Repo-Map Management
# github.com/DaRipper91 | jules.google.com
# Copy the prompt text (between the lines) into Jules, attaching the repo-map repo.

================================================================================
PROMPT 1: DUPLICATE REPOSITORY DETECTION
================================================================================
Context: Run this after your first sync. Attach the repo-map repository to Jules.

I have a GitHub profile (DaRipper91) with multiple repositories,
some of which may be duplicates or serve overlapping purposes.

The repos/ directory in this repository contains a README.md and map.md
files for each repository in my profile. Each README.md has the repo name,
description, file count, last push date, and directory structure.

Please:
1. Read all README.md files in the repos/ directory
2. Group repositories that appear to serve the same purpose or overlap
3. For each group, identify the primary repo (most recently pushed / most complete)
4. List what unique content exists in secondary repos that must be preserved
5. Recommend an action for each: archive / delete / merge-into-primary

Save your output as a new file: _meta/consolidation-plan.md

Format each group exactly like this:
---
## Group: [Short Purpose Description]

**Primary:** `repo-name`
- Reason: [why this is primary]

**Duplicates/Overlaps:**
- `repo-name-2` — [why it overlaps]
- `repo-name-3` — [why it overlaps]

**Unique content to migrate before action:**
- From `repo-name-2`: [files, features, or patterns to preserve]

**Recommended action:** [archive / delete / merge-into-primary]
---


================================================================================
PROMPT 2: AI FILE DESCRIPTION PASS (per repo)
================================================================================
Context: Run this once per repo to fill in pending descriptions.
Replace [REPO_NAME] with the actual repository name before running.

In the repos/[REPO_NAME]/ directory of this repository, every map.md file
contains file entries with this placeholder line:
  - **Description:** *(pending AI description pass)*

Please update ALL map.md files in repos/[REPO_NAME]/ only.

For each file entry, replace the placeholder with a real 3–4 sentence
technical description. Base your description on:
- The filename and extension
- The directory path and its purpose
- Related files visible in the same map.md
- Common patterns for files of that type (e.g., index.ts is usually an entry point)

Rules:
- Keep descriptions technical and factual
- Do NOT add commentary outside the description field
- Do NOT modify any other fields (Repo, Branch, Path, Type)
- Return exactly the same file structure with only the Description lines changed
- Commit all updated map.md files with message: "docs: AI description pass for [REPO_NAME]"


================================================================================
PROMPT 3: CODE REVIEW & SUGGESTIONS
================================================================================
Context: Run this for any repo you want feedback on.
Replace [REPO_NAME] with the actual repository name before running.

Please perform a comprehensive review of the repository: [REPO_NAME]
at github.com/DaRipper91/[REPO_NAME]

Focus on these four areas:

**PERFORMANCE**
- Unnecessary re-renders or expensive computations
- Missing memoization (React.memo, useMemo, useCallback)
- Unoptimized database queries or missing indexes
- Large bundle sizes or missing code splitting
- N+1 query patterns or inefficient loops

**UI / UX**
- Missing ARIA labels or accessibility attributes
- Keyboard navigation issues
- Responsive design gaps (breakpoints, mobile layout)
- Inconsistent spacing, typography, or color usage
- Loading states and error boundary coverage

**CODE QUALITY**
- Dead code or unused imports/variables
- Duplicated logic that could be abstracted
- Missing error handling (unhandled promises, empty catch blocks)
- Outdated patterns (class components, old API usage)
- Functions that are too long or have too many responsibilities

**DEPENDENCIES**
- Outdated packages (check package.json or requirements.txt)
- Known vulnerable packages
- Packages that could be replaced with modern built-ins

Save all findings as: _meta/reviews/[REPO_NAME]-review.md

Format each finding like:
### [HIGH/MED/LOW] File: `path/to/file`, Line: N
**Issue:** [Description of the problem]
**Why:** [Why this is a problem]
**Fix:** [Specific recommendation]
```
[Optional: code example showing the fix]
```


================================================================================
PROMPT 4: MERGE TWO REPOSITORIES
================================================================================
Context: Use after confirming a duplicate pair. Jules will add source content
to the target repo WITHOUT deleting the source.
Replace [SOURCE_REPO] and [TARGET_REPO] before running.

I want to absorb the content of [SOURCE_REPO] into [TARGET_REPO].

SOURCE: github.com/DaRipper91/[SOURCE_REPO]
TARGET: github.com/DaRipper91/[TARGET_REPO]

Please perform these steps in TARGET_REPO:

1. Identify all files in SOURCE_REPO that do NOT exist in TARGET_REPO
2. Copy those unique files into TARGET_REPO under the path:
   legacy/[SOURCE_REPO]/[original path]
3. For files that exist in BOTH repos (conflicts), do NOT overwrite TARGET_REPO.
   Instead, create a diff file at:
   legacy/[SOURCE_REPO]/conflicts/[filename].txt
   containing both versions side by side with clear labels.
4. Create a file: legacy/[SOURCE_REPO]/MERGE_LOG.md documenting:
   - Date of merge
   - Files copied (with original and new paths)
   - Files that had conflicts (with instructions for manual resolution)
5. Update TARGET_REPO's root README.md to note:
   "This repo absorbed [SOURCE_REPO] on [date]. See legacy/[SOURCE_REPO]/"
6. Commit all changes with message:
   "merge: absorbed [SOURCE_REPO] into legacy/"

Do NOT delete or modify SOURCE_REPO.
Do NOT overwrite any existing TARGET_REPO files.


================================================================================
PROMPT 5: STALE REPO AUDIT
================================================================================
Context: Identify repos that may be abandoned or outdated.

Review the repos/ directory in this repository.

For each repo README.md, note the "Last Push" date.

Please create a report at _meta/stale-repo-audit.md that:

1. Lists all repos that have not been pushed to in 6+ months
2. For each stale repo, assess based on file count and description:
   - Is this likely a finished/complete project? (keep, maybe archive)
   - Is this likely an abandoned experiment? (candidate for deletion)
   - Is this a utility others might depend on? (keep, add archive warning)
3. Rank from "safest to delete" to "definitely keep"
4. Provide a one-line recommendation per repo

Format:
| Repo | Last Push | Assessment | Recommendation |
|------|-----------|------------|----------------|
| repo-name | 2024-01-15 | Abandoned experiment | Delete after backup |


================================================================================
PROMPT 6: TECHNOLOGY STACK MAPPING
================================================================================
Context: Get a bird's eye view of your tech stack across all repos.

Read all map.md files in the repos/ directory of this repository.

Based on file extensions and directory names, create a technology
inventory at _meta/tech-stack-map.md that shows:

1. All programming languages used (by file extension frequency)
2. All frameworks detected (by config files like package.json, requirements.txt,
   Gemfile, go.mod, Cargo.toml, etc.)
3. Which repos use which tech stack
4. Any consistency gaps (e.g., 5 repos use TypeScript but 2 still use plain JS)
5. Suggested standardization opportunities

Format as tables and summary sections.
