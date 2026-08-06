# Deploy .ai.soc to a project

**Thin-client (recommended):**
```bash
bash scripts/soc-deploy-basic.sh /path/to/target
```

**Update existing thin-client:**
```bash
bash scripts/soc-deploy-basic.sh /path/to/target --update
```

**Fat-client (vendored):**
```bash
bash scripts/soc-deploy-files.sh /path/to/target
```

**Status check:**
```bash
bash scripts/soc-deploy-basic.sh --status /path/to/target
```
