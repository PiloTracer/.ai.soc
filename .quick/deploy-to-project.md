# Deploy .ai.soc to a project

**Thin-client (recommended):**
```bash
bash scripts/soc-deploy-basic.sh /path/to/target
```

**Update existing thin-client:**
```bash
bash scripts/soc-deploy-basic.sh /path/to/target update
```

**Fat-client (vendored, self-contained):**
```bash
bash scripts/soc-deploy-files.sh /path/to/target
```

**Status check:**
```bash
bash scripts/soc-deploy-basic.sh status /path/to/target
```

**Verify a deployed target (read-only audit; exit 1 on failure):**
```bash
bash scripts/soc-deploy-basic.sh verify /path/to/target
```
Checks `.cursorrules` SOC block, `SOC_SOURCE` correctness/reachability, stale
skill handles, `.work.soc/` skeleton, and sister frameworks under the resolved
WORK_ROOT. Runs automatically at the end of every deploy/update/archive.

**Argument normalization:** verbs work with or without `--`, in any position
relative to the path. These are exactly equivalent:
```bash
bash scripts/soc-deploy-basic.sh /path/to/target update
bash scripts/soc-deploy-basic.sh /path/to/target --update
bash scripts/soc-deploy-basic.sh --update /path/to/target
```
