# Deploy .ai.soc to a project

**Thin-client (recommended):**
```bash
bash scripts/deploy-basic.sh /path/to/target
```

**Update existing thin-client:**
```bash
bash scripts/deploy-basic.sh /path/to/target --update
```

**Fat-client (vendored):**
```bash
bash scripts/deploy-files.sh copy /path/to/target
```

**Status check:**
```bash
bash scripts/deploy-basic.sh --status /path/to/target
```
