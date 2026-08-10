---
name: soc-deploy-repo
description: >-
  Full git-based deploy of .ai.soc into a target directory. Two modes:
  clone (git clone with full history via origin remote) or archive
  (git archive extract including .github, .gitignore, .cursorrules).
  Use clone for a full git mirror; use archive when no remote is available
  or when updating an existing target. Archive deploys end with a verify
  pass of the deployed tree's .cursorrules. Arguments are normalized: verbs
  accept an optional `--` prefix and may appear before or after the target
  path. soc-deploy-repo clone - <path>, soc-deploy-repo archive - <path>,
  soc-deploy-repo status, soc-deploy-repo verify [path].
---

# soc-deploy-repo

**Shell:** `bash .ai.soc/scripts/soc-deploy-repo.sh [--status [path] | <clone|archive> <target-path>]`

Deploys the entire `.ai.soc` repository (including `.git/`, `.github/`, `.gitignore`, and root `.cursorrules`) into a target directory. Two modes cover both git-mirror and snapshot deployments.

**Canonical path:** `.ai.soc/skills/soc-deploy-repo/skill.md` · **Shell:** `.ai.soc/scripts/soc-deploy-repo.sh`

**Contrast with `soc-deploy-files`:** `soc-deploy-repo` includes VCS artifacts. Use `@soc-deploy-files copy` when you only need the `.ai.soc/` directory without git history or `.github/`.

---

## Parse invocation

**Argument normalization:** verbs accept an optional `--` prefix and may appear before or after the target path. `@soc-deploy-repo archive - /path` ≡ shell `soc-deploy-repo.sh /path archive` ≡ `soc-deploy-repo.sh /path --archive` ≡ `soc-deploy-repo.sh --archive /path`.

| User says | Mode |
|-----------|------|
| `@soc-deploy-repo clone - /path/to/repo` | Full `git clone` from origin remote to target path |
| `@soc-deploy-repo archive - /path/to/repo` | `git archive HEAD \| tar xf` — full tree, no `.git` + verify pass |
| `@soc-deploy-repo status` (= `--status`) | Report source remote, HEAD, optional target deploy state |
| `@soc-deploy-repo verify [path]` (= `--verify`) | Read-only audit of target `.cursorrules` + `.work.soc/` (delegates to soc-deploy-basic verify); exit 1 on hard failure |

**Shell (read-only):** `bash scripts/soc-deploy-repo.sh status [target-path]` · `bash scripts/soc-deploy-repo.sh verify [target-path]`

**Default:** `status` if no verb matches.

---

## I0 — Pre-checks

| Condition | Action |
|-----------|--------|
| Target parent dir does not exist | **Block**: report missing path |
| No git remote in source (clone mode) | **Block**: suggest `archive` mode instead |
| Target already has `.git` (clone mode) | Report existing; exit (clone requires fresh target) |
| Target exists as non-dir | **Block**: report conflict |

---

## I1 — Clone mode

1. `bash scripts/soc-deploy-repo.sh clone "<resolved-path>"`
2. Requires git remote `origin` on source repo.
3. Target must not exist or must be empty.
4. Full `git clone` preserves all branches and tags.

**When to use:** You need the full repository with git history, CI/CD workflows (`.github/`), and version tracking in the target.

---

## I2 — Archive mode

1. `bash scripts/soc-deploy-repo.sh archive "<resolved-path>"`
2. Uses `git archive HEAD` — no remote required.
3. Includes `.github/`, `.gitignore`, `.cursorrules` (everything except `.git` directory).
4. Idempotent — re-runs safely overwrite files.

**When to use:** No remote available, or target already exists and you want to update its tree while keeping VCS artifacts.

---

## Completion

| # | Check | Clone | Archive |
|---|-------|-------|---------|
| 1 | Source repo has origin remote (or archive mode) | pass | pass |
| 2 | Target path exists and is populated | | |
| 3 | `.git/` present (clone) / `.github/` present (archive) | | |
| 4 | `.cursorrules` present at target root | | |
| 5 | Verify pass clean (archive: automatic; clone: run `verify` after checkout) | | |
| 6 | User informed of next steps | | |

## Next commands (in target project)

```text
@soc-deploy-basic
@soc-session start
```

**OpenCode:** Security OS does not ship `opencode.json`. When co-installed with Agent OS, skills are registered in the parent `.ai/opencode.json`.
