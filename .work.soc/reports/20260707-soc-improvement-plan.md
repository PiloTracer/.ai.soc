# Security OS — Improvement Plan (2026-07-07)

**Reference source:** `.ai` Agent OS v0.5.3 (commits c2a810d..cc25b3b, 2026-07-01 to 2026-07-06)

---

## Applied changes

### 1. Change-safety layer (NEW)

Added from reference's change-safety and gate-verification layer:

| Artifact | Source reference | Status |
|----------|-----------------|--------|
| `scripts/touch-scope-verify.sh` | `scripts/touch-scope-verify.sh` | ✅ Created |
| `scripts/blast-radius-check.sh` | `scripts/blast-radius-check.sh` | ✅ Created |
| `scripts/gate-verify.sh` | `scripts/gate-verify.sh` | ✅ Created |
| `.cursorrules` § Change safety | `.cursorrules` § Change safety | ✅ Updated |

### 2. Git hooks + hygiene (NEW)

Added from reference's Co-authored-by enforcement:

| Artifact | Source reference | Status |
|----------|-----------------|--------|
| `hooks/prepare-commit-msg` | `hooks/prepare-commit-msg` | ✅ Created |
| `hooks/commit-msg` | `hooks/commit-msg` | ✅ Created |
| `hooks/pre-commit` | `hooks/pre-commit` | ✅ Created |
| `hooks/post-commit` | `hooks/post-commit` | ✅ Created |
| `scripts/install-git-hooks.sh` | `scripts/install-git-hooks.sh` | ✅ Created |

### 3. SKILL_DEPENDENCIES.md (NEW — was missing)

| Artifact | Source reference | Status |
|----------|-----------------|--------|
| `skills/SKILL_DEPENDENCIES.md` | `skills/SKILL_DEPENDENCIES.md` | ✅ Created |

Defines work tree paths (`{WORK_SOC_ROOT}`, `{HANDOFF_SOC}`, etc.), dependency matrix for all 6 skills, blocked report shape, and canonical verb vocabulary.

### 4. .quick/ guides (NEW — was missing)

| Artifact | Source reference | Status |
|----------|-----------------|--------|
| `.quick/session-lifecycle.md` | `.quick/session-lifecycle.md` | ✅ Created |
| `.quick/directors.md` | `.quick/directors.md` | ✅ Created |
| `.quick/deploy-to-project.md` | `.quick/deploy-to-project.md` | ✅ Created |

---

## Deferred items (not applied)

| Item | Reason |
|------|--------|
| `standards/` directory | Needs SOC-specific security standards (testing, classification, reporting) — requires domain expertise to author |
| `concepts/` directory | Needs SOC-specific concepts (threat-modeling, risk-rating, disclosure workflows) — domain-dependent |
| `docs/adoption/FROM_AGENT_OS.md` | Adoption guide needs SOC-specific context — create when first consumer repo is bootstrapped |
| `probe-protocol.md` | Only applies if SOC adopts plan-foundation/plan-master patterns — currently no planning skills exist |
| `release.sh` | Release workflow depends on CI/CD pipeline not yet established |

---

## Next actions

1. **Install hooks** — `bash scripts/install-git-hooks.sh` from repo root
2. **Update `framework-verify.sh`** — add self-tests for touch-scope-verify, blast-radius-check, gate-verify
3. **Verify** — `bash scripts/framework-verify.sh` passes before next commit
4. **Add `standards/`** — create SECURITY_TESTING_STANDARD, FINDINGS_CLASSIFICATION.md, REPORTING_STANDARD.md when domain guidance is ready
5. **Add `skills/README.md` depth** — add naming protocol and flow diagram matching `.ai`/`.ai.ui`/`.ai.biz` conventions

---

## Cross-validation notes

All changes adapted to `.ai.soc`'s domain:
- Work tree paths use `.work.soc/` prefix
- Commit refs use `SOC-` prefix
- Scripts are standalone (no dependency on `.ai/` scripts)
- SKILL_DEPENDENCIES.md references only the 6 SOC OS skills (deploy-basic, deploy-files, deploy-repo, session-soc, soc-director, soc-gateway)
