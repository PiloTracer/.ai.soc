---
name: soc-deploy-files
description: >-
  Deploy .ai.soc (Security OS) files into a target project. Two directions:
  (1) in-place bootstrap — invoked from a TARGET project, copies the source
  .ai.soc in without overwriting existing files, then scaffolds .work.soc/ +
  .cursorrules SOC block; (2) outbound copy — invoked from the source .ai.soc
  repo, copies into an explicit <path>. `update` mode additionally performs a
  rules-aware merge of existing-but-differing files (append new rules, update
  shared sections, preserve target customizations; never wholesale-replace).
  Copies only git-tracked / non-ignored files (anything in .gitignore is never
  copied). The in-place scaffold writes SOC_SOURCE pointing at the LOCAL
  deployed copy (fat-client = self-contained) and ends with a verify pass.
  Arguments are normalized: verbs accept an optional `--` prefix and may
  appear before or after the target path. Use soc-deploy-files (default),
  soc-deploy-files update, soc-deploy-files copy - <path>, soc-deploy-files status.
---

# soc-deploy-files

Two-direction deploy of the `.ai.soc` framework into a target project so the project can use Security OS skills. **Default = no-overwrite**: existing target files are preserved by construction.

**Shell:** `bash <source>/scripts/soc-deploy-files.sh <target-path> [mode]`
**Scaffold shell:** `REPO_ROOT=<target> bash <source>/templates/bootstrap.sh`

**Canonical path:** `.ai.soc/skills/soc-deploy-files/skill.md` · **Shell:** `.ai.soc/scripts/soc-deploy-files.sh`

**Security invariant:** The script enumerates files via `git ls-files --cached --others --exclude-standard` from the **source** `.ai.soc` repo root, so anything `.gitignore` excludes (credentials, private context, `tmp/`, …) is never copied — enforced by construction, not a hand-maintained list. The source must be a git repo with `.ai.soc/` as its root.

**Source not modified.** soc-deploy-files only writes to the **target**. The source `.ai.soc` is read-only.

**Contrast with `soc-deploy-repo`:** `soc-deploy-files` copies only the `.ai.soc/` directory (no VCS artifacts). Use `@soc-deploy-repo clone` when you need the full repo including `.git` and `.github/`.

---

## Parse invocation

**Argument normalization:** verbs accept an optional `--` prefix, the target path may appear before or after the verb, and quoting the path is optional. `@soc-deploy-files "/path" update` ≡ `@soc-deploy-files /path --update` ≡ `@soc-deploy-files --update /path`.

| User says | Direction | Mode |
|-----------|-----------|------|
| `@soc-deploy-files` | in-place (cwd is target) | copy no-overwrite + scaffold no-overwrite + verify |
| `@soc-deploy-files update` (= `--update`) | in-place | copy no-overwrite + scaffold no-overwrite + **rules-aware merge** of differing existing files + verify |
| `@soc-deploy-files copy - /path/to/repo` | outbound (source = this repo) | copy no-overwrite to `/path/to/repo/.ai.soc` |
| `@soc-deploy-files copy - /path/to/repo --force` | outbound | copy with idempotent overwrite (legacy) |
| `@soc-deploy-files status` (= `--status`) | report | report whether `.ai.soc/` exists at known deploy locations |

**Default:** `status` if no verb matches. **Aliases:** `bootstrap`, `fat` → bare `@soc-deploy-files`.

---

## I0 — Pre-checks (both directions)

| Condition | Action |
|-----------|--------|
| Source is not a git repo, or `.ai.soc/` is not the git root | **Block**: report; soc-deploy-files relies on `git ls-files` as the authority |
| Target parent dir does not exist | **Block**: report missing path |
| Destination exists and is not a dir | **Block**: report conflict |
| Destination already has `.ai.soc/` | Proceed with **no-overwrite**; report skipped count (default) |
| `--force` requested and destination populated | Warn that target customizations will be overwritten; require explicit `--force` in the same invocation |

### Source resolution (in-place direction)

When invoked from a **target** project (cwd has no `.ai.soc/scripts/soc-deploy-files.sh`):

1. **Auto:** if the script can be located at a known source path (user named it, or the `SOC_SOURCE` env), use it.
2. **Ask once:** if source is unknown, ask the user for the source `.ai.soc` path (e.g. `/mnt/work/Projects/.ai.soc`). Do not guess.
3. Source determined → run the shell from the **target** directory:
   ```bash
   cd <target> && bash <source>/scripts/soc-deploy-files.sh . <mode>
   ```

---

## I1 — Copy mode (no-overwrite by default)

1. `bash <source>/scripts/soc-deploy-files.sh "<resolved-target>"` (default) — or `--force` / `--update`.
2. **File set:** `git ls-files --cached --others --exclude-standard` from the source repo root.
3. **Skill-level omissions:** `.github/`, `.gitignore`, `.gitattributes`, `.cursorrules`. Deploy scripts (`scripts/soc-deploy-*.sh`) **are** included so the fat-client target can self-verify and self-update via its local copy.
4. **No-overwrite default:** `rsync --ignore-existing` skips any file already present in the target.

---

## I2 — Scaffold (in-place direction only)

When invoked in-place (bare `@soc-deploy-files` or `@soc-deploy-files update`), after the copy pass the script **automatically chains**:

1. `.work.soc/` scaffold via `REPO_ROOT=<target> bash <source>/templates/bootstrap.sh`
2. SOC block in `.cursorrules` via `bash <source>/scripts/soc-deploy-basic.sh <target>` — which writes `SOC_SOURCE=<target>/.ai.soc` (the **local** deployed copy, so the fat-client is self-contained) and ends with a **verify pass** of the target (see soc-deploy-basic § I4)

No separate `@soc-deploy-basic` invocation is required after in-place `@soc-deploy-files`.

**Outbound `copy - <path>` does NOT scaffold** — run `@soc-deploy-basic` in the target after copy.

---

## I3 — update-merge protocol (`@soc-deploy-files update` only)

After I1 (no-overwrite copy) the script prints a **merge candidate list**: every file present in both source and target whose content differs. The agent then performs a **rules-aware merge** for each candidate.

| Class | Merge rule |
|-------|------------|
| Skills (`skills/<id>/skill.md`) | Append new sections; update shared sections; never drop target-only verbs/tables |
| Standards (`standards/*.md`) | Append new sections; update shared text; preserve dated overrides |
| Framework docs (README, concepts, etc.) | Append new sections; update shared paragraphs; preserve target examples |
| Templates (`templates/**`) | Prefer source version (framework-owned); if target edited intentionally, keep target + record |
| Scripts (`scripts/**`) | Prefer source version (mechanical); overwrite → record in report |

**Preserve invariants (never drop):**
- Target-only skill folders not present in source (custom skills).
- Target additions to any table (rows the source doesn't have).
- Target date-stamped filenames (`YYYYMMDD-*`).

**Merge procedure per candidate:**
1. Read source version and target version.
2. Diff structurally (sections by `##`/`###` headings, list rows / table rows).
3. For each **shared** section whose source text changed: apply source change **but** keep target-only rows/lines inside it.
4. For each **source-only** section absent in target: append it.
5. For each **target-only** section absent in source: keep unchanged.
6. Write merged result to target. Record `merged: <path>` in report.
7. **Never** wholesale-replace a file the target already owned.

---

## Completion

| # | Check | Result |
|---|-------|--------|
| 1 | Source repo is a git repo with `.ai.soc/` as root | pass |
| 2 | Destination `.ai.soc/` exists after copy | |
| 3 | No `.gitignored` content in destination | |
| 4 | `.github/` excluded from destination | |
| 5 | `.cursorrules` SOC block present (from scaffold) | |
| 6 | No-overwrite honored | |
| 7 | Scaffold ran into target (in-place only) | |
| 8 | `update`: merge candidate list processed | |
| 9 | Fat-client `.cursorrules` points `SOC_SOURCE` at the local `.ai.soc`; verify pass clean | |

## Next commands (in target project)

```text
@soc-session start
```
