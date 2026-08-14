# Agent OS Framework — source marker

This file marks the repository root as the **Agent OS framework source repo** (self-hosted `.ai`).

- **Detection:** `session-control` and deploy skills treat a repo as framework source ⇔ this file exists at the repo root. Absence ⇒ consumer project.
- **Never modify:** this file is a protected surface (`standards/PROTECTED_SURFACES.json`, `.cursorrules` §Protected Files). Its content is fixed; do not edit, rename, or delete it.
- **Never deployed:** `deploy-files` explicitly excludes it; `deploy-basic` never writes root files; it must never appear in a consumer project.
