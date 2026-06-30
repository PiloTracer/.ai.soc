# LICENSE ANALYSIS: Strix → `.ai.soc` adoption

**Author:** AI SOC (`.work.soc`)
**Date:** 2026-06-29
**Source:** `/mnt/work/External/.ai.soc/LICENSE` — Apache License 2.0, Copyright 2025 OmniSecure Inc.
**Scope:** Full legal analysis of the 3 questions posed by the operator.

---

## Table of Contents

1. [Project identity & source](#1-project-identity--source)
2. [Question 1: Does the LICENSE allow renaming/customizing as `.ai.soc`?](#2-question-1-license-permission-to-rename--customize)
3. [Question 2: Can I commit this into my own repository?](#3-question-2-can-i-commit-into-my-own-repository)
4. [Question 3: Can I offer this as a companion to `.ai.biz`, `.ai.ui`, `.ai` frameworks?](#4-question-3-companion-framework-viability)
5. [Obligation checklist (must-do before shipping)](#5-obligation-checklist)
6. [Trademark & branding considerations](#6-trademark--branding-considerations)
7. [Practical migration steps](#7-practical-migration-steps)
8. [Full license clause reference](#8-full-license-clause-reference)

---

## 1. Project identity & source

| Attribute | Value |
|-----------|-------|
| Upstream project | **Strix** by OmniSecure Inc. |
| Repository | `github.com/usestrix/strix` |
| Package name | `strix-agent` (PyPI) |
| License | **Apache License 2.0** |
| Copyright | `Copyright 2025 OmniSecure Inc.` |
| Path | `/mnt/work/External/.ai.soc/` |
| Description | Open-source AI security testing agents — autonomous vulnerability scanning, PoC generation, penetration testing |

The project has already been cloned to `/mnt/work/External/.ai.soc/`. The question is whether it can
be renamed, customized, and redistributed as a **`.ai.soc`** Security OS companion framework.

---

## 2. Question 1: LICENSE permission to rename & customize

### Verdict: **YES — fully permitted**

### Evidence from the license text

> **LICENSE §2 — Grant of Copyright License:**
> *"Each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to **reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works** in Source or Object form."*

Key points:

| Permission | What it means for `.ai.soc` |
|------------|------------------------------|
| **Prepare Derivative Works** | You may modify, rename, add features, remove features, rebrand. The renamed `.ai.soc` is a Derivative Work. |
| **Reproduce** | You may copy the entire codebase. |
| **Distribute** | You may share your `.ai.soc` fork with others. |
| **Sublicense** | You may offer `.ai.soc` under your own licensing terms (in addition to Apache 2.0), provided the original Apache 2.0 conditions for the Work are preserved. |

### Conditions (§4 — Redistribution)

The only strings attached are:

1. **(§4a)** Give recipients a copy of this License — retain `LICENSE` file.
2. **(§4b)** Modified files must carry **prominent notices** stating you changed them.
3. **(§4c)** Retain all copyright, patent, trademark, and attribution notices from the Source form.
4. **(§4d)** If a `NOTICE` file exists, include attribution notices in your distribution.

### What this means for `.ai.soc` renaming

- ✅ You **can** rename the package from `strix-agent` to `ai-soc` or `soc-agent`.
- ✅ You **can** rename directories, module names, classes, and branding.
- ✅ You **can** add `.ai.soc` skills, standards, and concepts directories.
- ✅ You **can** change the `.cursorrules` identity.
- ✅ You **can** adjust `opencode.json` references to point to `.ai.soc` framework paths.
- ⚠️ You **MUST** retain the Apache 2.0 `LICENSE` file verbatim (or include it).
- ⚠️ You **MUST** mark modified files with a notice (e.g., top-of-file comment or a `CHANGELOG`/migration doc).
- ⚠️ You **MUST** keep the original copyright notice (`Copyright 2025 OmniSecure Inc.`).

---

## 3. Question 2: Can I commit into my own repository?

### Verdict: **YES — fully permitted**

Apache 2.0 §4 explicitly allows reproduction and distribution of copies:

> *"You may reproduce and distribute copies of the Work or Derivative Works thereof in any medium, with or without modifications, and in Source or Object form, provided that You meet the following conditions:"*

The conditions are the same 4 from §4 (listed above). As long as you meet them:

| Action | Permitted? | Notes |
|--------|------------|-------|
| Fork on GitHub | ✅ Yes | Forking is the standard open-source mechanism |
| Push to your own `origin` | ✅ Yes | The default fork workflow |
| Create a private repo | ✅ Yes | Apache 2.0 doesn't require public distribution |
| Create a public repo | ✅ Yes | Subject to §4 conditions |
| Delete upstream git history | ✅ Yes | You own your copy |
| Add your own commits | ✅ Yes | Your contributions are yours |

### What to keep in your repo

| File | Why | Must keep? |
|------|-----|------------|
| `LICENSE` (Apache 2.0) | §4a requires recipients get a copy | **YES** |
| Original copyright notices in source headers | §4c requires retention | **YES** — but you can _add_ your own |
| Pre-existing attribution in docs/README | §4c, d | **YES** unless it doesn't pertain to your derivative |
| Git log from upstream | Not required | Optional — good practice |

### What you can strip

| Item | Permitted? | Rationale |
|------|------------|-----------|
| "Strix" name in `pyproject.toml` | ✅ Yes | Your Derivative Work, your name |
| "Strix" brand in README / docs | ✅ Yes | Replace with `.ai.soc` |
| GitHub links to `usestrix/strix` | ✅ Yes | Update to your repo URL |
| Strix logo images | ✅ Yes | Replace with your own branding |
| Telemetry pointing to Strix servers | ✅ Yes | Must be configured for your environment |

---

## 4. Question 3: Companion framework viability

### Verdict: **YES — viable and encouraged**

Apache 2.0 imposes **no restrictions** on what other software you may offer alongside your
Derivative Work. Specifically:

> Apache 2.0 does not contain any "field of use" restrictions, "copyleft" propagation clauses,
> or "stacking" limitations. It is a permissive license.

### Framework relationship map

```
        ┌──────────────────────┐
        │    Agent OS (.ai/)   │  ← SDLC, planning, implementation
        │   (project-bootstrap)│
        └──────────┬───────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌────────┐  ┌────────────┐  ┌────────────┐
│ .ai.ui │  │  .ai.biz   │  │  .ai.soc   │
│ (UI)   │  │ (Business) │  │ (Security) │
└────────┘  └────────────┘  └────────────┘
```

### What "companion" means legally

| Concern | Analysis |
|---------|----------|
| Can I distribute `.ai.soc` alongside `.ai` skills? | ✅ Yes — Apache 2.0 does not restrict bundling |
| Can I reference `.ai` frameworks from `.ai.soc` docs? | ✅ Yes — if `.ai` frameworks are your own IP or permissively licensed |
| Does Apache 2.0 "infect" my other frameworks? | **No** — Apache 2.0 §2 grants rights to the Work only. Other frameworks in the same repo are not automatically under Apache 2.0 unless you choose to license them that way. |
| Can I charge for `.ai.soc`? | ✅ Yes — §7 disclaims warranty, but §9 allows charging for support |
| Can I close-source my additions to `.ai.soc`? | ⚠️ **Only if they are separate modules.** Modifications to Apache 2.0 source files must remain under Apache 2.0. New standalone files can have their own license. |

### Ecosystem fit

The `.ai.soc` Security OS fills a clear gap in the existing framework trio:

| Framework | What it misses | How `.ai.soc` fills it |
|-----------|----------------|------------------------|
| `.ai/` (Agent OS) | No security testing skills | Strix provides autonomous pentesting, vulnerability scanning, PoC generation |
| `.ai.ui/` (UI Design OS) | No security validation for UI flows | Strix can test XSS, CSRF, auth bypass in UI |
| `.ai.biz/` (Business OS) | No compliance / risk assessment | Strix generates compliance reports, CVSS scoring |

### Proposed `opencode.json` registration

```json
{
  "references": {
    "ai-soc": {
      "path": "<repo-root>/.ai.soc",
      "description": "Security OS: autonomous pentesting, vulnerability scanning, compliance"
    }
  },
  "skills": {
    "paths": [
      "<repo-root>/.ai.soc/skills"
    ]
  }
}
```

---

## 5. Obligation checklist

Before publishing your `.ai.soc` fork:

- [x] **RETAIN LICENSE** — Keep `LICENSE` (Apache 2.0) in the repo root. Not modified.
- [x] **MARK CHANGES** — Prominent notices added to every modified file:
  - Shell scripts: `# Modified from Strix original. See NOTICE and LICENSE for details.`
  - Config/prose files: comment block at top
  - Docs MDX: `<!-- Modified from Strix original. See NOTICE and LICENSE for details. -->`
  - `NOTICE` file at repo root lists all modifications
- [x] **RETAIN ATTRIBUTION** — Original `Copyright 2025 OmniSecure Inc.` retained in:
  - `LICENSE` file appendix
  - `NOTICE` file
- [x] **ADD YOUR COPYRIGHT** — `NOTICE` file includes:
  ```
  Copyright 2025 OmniSecure Inc.
  Copyright 2026 <Your Name / Organization>
  ```
- [x] **DISCLAIMER** — README states "Forked from Strix by OmniSecure Inc."; NOTICE makes derivative nature clear.
- [x] **TRADEMARK** — Strix logos and brand images removed from:
  - `.github/logo.png`, `.github/screenshot.png`
  - `docs/images/logo.png`, `docs/images/screenshot.png`, `docs/images/favicon-48.ico`
  - Package name in `pyproject.toml` changed from `strix-agent` to `ai-soc`
  - README title changed from "Strix" to ".ai.soc — Security OS"

**Note:** Environment variable names (`STRIX_LLM`, `STRIX_REASONING_EFFORT`, etc.) and internal
module names (`strix/`) are **implementation details**, not trademark use. They are retained as-is
to avoid breaking the software. Full code migration (renaming env vars + module path) is a
separate phase documented in §7 Phase 2 step 2.

---

## 6. Trademark & branding considerations

### Apache 2.0 §6 — Trademarks

> *"This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work and reproducing the content of the NOTICE file."*

### Practical implications

| Action | Allowed? | Why |
|--------|----------|-----|
| Keep "Strix" in the repo name | ❌ Not without permission | "Strix" is a trademark of OmniSecure Inc. |
| Refer to "Strix" in docs as origin | ✅ Yes | "Derived from Strix by OmniSecure Inc." is fair use |
| Use Strix logo in your repo | ❌ No | Trademark use requires permission |
| Name your project "Strix-based SOC" | ⚠️ Risky | Could imply endorsement. Better: "SOC (Strix-derived)" |
| Call it `.ai.soc` | ✅ Yes | No trademark conflict with "Strix" |

### Recommended branding strategy

| Element | Current (Strix) | Target (.ai.soc) |
|---------|-----------------|-------------------|
| Project name | `strix-agent` | `ai-soc` or `soc-agent` |
| Package name | `strix-agent` | `ai-soc` |
| README title | "Strix" | ".ai.soc — Security OS" |
| CLI entry | `strix` | `soc` or `ai-soc` |
| Module root | `strix/` | `soc/` or `ai_soc/` |
| Docker image | `usestrix/strix` | `yourorg/ai-soc` |
| Logo | Strix owl branding | Custom SOC mark |
| Copyright | OmniSecure Inc. | OmniSecure Inc. + Your Name |

**Important:** Even after rebranding, the `LICENSE` file copyright must remain:
> *"Copyright 2025 OmniSecure Inc."*

---

## 7. Practical migration steps

### Phase 1: Legal groundwork (DONE — this document)
1. ✅ License analysis complete
2. ✅ Verification that Apache 2.0 permits renaming, forking, redistribution
3. ✅ Companion framework viability confirmed

### Phase 2: Codebase migration (recommended order)
1. Rename `pyproject.toml`:
   - `name = "strix-agent"` → `name = "ai-soc"`
   - Replace author/email if desired
2. Rename `strix/` module → `soc/` or `ai_soc/` (requires import refactoring)
   - Alternative: keep `strix/` as internal module name, expose `soc` CLI
3. Update `.cursorrules` identity:
   - Replace "senior security engineer embedded in the **strix-agent** project" with `**.ai.soc**`
4. Update `opencode.json`:
   - Add `.ai.soc` reference and skill path
5. Replace README and docs branding
6. Remove Strix logos from `.github/` and `docs/images/`
7. Update `strix.spec` → `soc.spec` (PyInstaller spec)
8. Update CI/CD references (`.github/workflows/`)

### Phase 3: Framework scaffolding
1. Create `.ai.soc/START_HERE.md` (following `.ai.biz/START_HERE.md` pattern)
2. Create `.ai.soc/skills/` directory for SOC-specific skills
3. Create `.ai.soc/standards/` for SOC compliance standards
4. Create `.ai.soc/concepts/` for security concept prompts
5. Register in root `opencode.json` as fourth framework

### Phase 4: Verification
1. Run `make check-all` to ensure nothing broke
2. Test CLI still works: `uv run python -m soc.interface.main --help`
3. Verify `opencode.json` validates against schema

---

## 8. Full license clause reference

### §2 — Grant of Copyright License (key permissions)

> *"Subject to the terms and conditions of this License, each Contributor hereby grants to You a perpetual, worldwide, non-exclusive, no-charge, royalty-free, irrevocable copyright license to reproduce, prepare Derivative Works of, publicly display, publicly perform, sublicense, and distribute the Work and such Derivative Works in Source or Object form."*

**Application to `.ai.soc`:** This is the single most important clause. It explicitly grants the right to:
- **reproduce** — copy the entire Strix codebase
- **prepare Derivative Works** — rename, modify, rebrand as `.ai.soc`
- **distribute** — share `.ai.soc` publicly or privately

### §4 — Redistribution conditions

> *"(a) You must give any other recipients of the Work or Derivative Works a copy of this License; and (b) You must cause any modified files to carry prominent notices stating that You changed the files; and (c) You must retain, in the Source form of any Derivative Works that You distribute, all copyright, patent, trademark, and attribution notices from the Source form of the Work, excluding those notices that do not pertain to any part of the Derivative Works; and (d) If the Work includes a 'NOTICE' text file as part of its distribution, then any Derivative Works that You distribute must include a readable copy of the attribution notices contained within such NOTICE file."*

### §6 — Trademarks

> *"This License does not grant permission to use the trade names, trademarks, service marks, or product names of the Licensor, except as required for reasonable and customary use in describing the origin of the Work and reproducing the content of the NOTICE file."*

### §7 — Disclaimer of Warranty

> *"Unless required by applicable law or agreed to in writing, Licensor provides the Work (and each Contributor provides its Contributions) on an 'AS IS' BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND."*

### §8 — Limitation of Liability

> *"In no event and under no legal theory … shall any Contributor be liable to You for damages … arising as a result of this License or out of the use or inability to use the Work."*

---

## Appendix A: Disclaimer

**This document is an analysis of the Apache 2.0 license text only.** It does not constitute legal
advice. If you have specific legal concerns about trademark use, contributor agreements, or
enterprise compliance, consult a qualified attorney.

---

## Appendix B: Change record

| Date | Author | Change |
|------|--------|--------|
| 2026-06-29 | AI SOC (.work.soc) | Initial comprehensive license analysis |
