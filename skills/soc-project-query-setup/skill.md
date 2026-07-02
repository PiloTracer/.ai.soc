# SKILL: soc-project-query-setup

**Purpose:** Guide user through connecting their coding agent to tools-project, and teach it to query tasks, tickets, projects, and clients for context-aware work.

**Deploy to:** Any Agent OS framework (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`) — optional integration.

**Tutorial companion:** `.work/docs/tutorials/LLM-2-API_SETUP.md` (step-by-step setup walkthrough)

---

## Hard rules

1. **Optional integration.** This skill is never required. The user must explicitly ask to set it up or the director must ask first.
2. **Read-only.** The API provides read-only access. No mutations, no writes, no data modification.
3. **Key security.** Never log the API key. Never store it in shell history. `/tmp` is forbidden for key material. The `~/.tools-project-key` file must be `chmod 600`.
4. **Verify before claiming done.** Run a live query to the API and show the actual response. Never claim "connected" without evidence.

---

## Modes

| Invocation | Mode |
|-----------|------|
| `@soc-project-query-setup install` | Full guided setup: generate key → create file → test → register MCP |
| `@soc-project-query-setup status` | Check if connected (key file exists? API reachable? MCP tools listed?) |
| `@soc-project-query-setup key` | Guide the user through web UI → key creation → `~/.tools-project-key` |
| `@soc-project-query-setup test` | Verify connectivity by listing projects |
| `@soc-project-query-setup register-mcp` | Register MCP server in consuming project's opencode.json |
| `@soc-project-query-setup help` | Show available tools and usage patterns for this OS |
| `@soc-project-query-setup` (no verb) | Default to `status` mode |

---

## Install protocol

### Step 1 — Detect OS context

Read the current OS identity from START_HERE.md or `.cursorrules`:

| Detected | OS | What it can do |
|----------|----|----------------|
| `.ai/` skills | Engineering OS | Query tasks/tickets for code work, build commit messages, verify HANDOFF vs live state, load project context before new features |
| `.ai.ui/` skills | UI Design OS | Check which tickets need UI work, get client/project context for screen design, search for existing components |
| `.ai.biz/` skills | Business OS | List all projects/clients for portfolio review, identify clients needing attention, find content to share |
| `.ai.soc/` skills | Security OS | Find tickets flagged for security review, check task status for pen test findings, search for vulnerability patterns |

Store this in an `OS_CONTEXT` variable for tailoring the rest of the protocol.

### Step 2 — Prerequisites gate

Check and report:

1. Is `python3` available? (required for MCP server)
2. Is there a running tools-project instance?
   - Local: try `curl -s http://localhost:8300/healthz`
   - Remote: ask user for URL
3. Can the user reach the web UI?
   - Local: `http://localhost:18513/settings/api-keys`
   - Remote: `https://<user-provided-url>/settings/api-keys`

If any prerequisite fails, stop and tell the user what to fix. If tools-project is not running locally, guide the user to start it from the tools-project repo:
```bash
cd /mnt/work/Projects/tools-project
docker compose up -d
```
Or if they don't have tools-project deployed, direct them to the tools-project repository for installation instructions.

### Step 3 — Key creation (web UI)

Guide the user:

```
1. Open: <URL>/settings/api-keys
2. Click "+ New key"
3. Enter a label (e.g. "My laptop", "Agent OS integration")
4. Click "Create"
5. COPY the key now — it starts with "tools_project_" — this is the ONLY time it's shown
```

Wait for the user to confirm they have the key. Do NOT ask them to paste it into chat. If they cannot access the web UI, offer to navigate them through the settings menu.

### Step 4 — Create the key file

The key lives at `~/.tools-project-key` with `chmod 600`. Two scenarios:

**Scenario A — User pasted the key in chat (with explicit permission):**
Execute the write yourself using a heredoc (never echo the key into shell history):

```bash
cat > ~/.tools-project-key << 'KEYEOF'
BASE_URL=https://project.cloudsys.win
tools_project_<key>
KEYEOF
chmod 600 ~/.tools-project-key
```

For local tools-project (no BASE_URL needed):
```bash
cat > ~/.tools-project-key << 'KEYEOF'
tools_project_<key>
KEYEOF
chmod 600 ~/.tools-project-key
```

**Scenario B — User has the key but did NOT paste it:**
Tell the user to run this (replace `<key>` with their actual key):

```bash
cat > ~/.tools-project-key << 'KEYEOF'
tools_project_<key>
KEYEOF
chmod 600 ~/.tools-project-key
```

**Critical:** Never log, echo, or display the key value. Never store it in shell history (use heredoc or `cat >`). The file must be `chmod 600`.

### Step 5 — Test connectivity

Run a live query and show the result:

```bash
curl -s http://localhost:8300/v1/agent/projects \
  -H "X-Api-Key: $(head -n2 ~/.tools-project-key | tail -n1)"
```

For remote:
```bash
BASE_URL=$(grep BASE_URL= ~/.tools-project-key | cut -d= -f2-)
KEY=$(tail -n1 ~/.tools-project-key)
curl -s "$BASE_URL/v1/agent/projects" -H "X-Api-Key: $KEY"
```

Expected: `{ "ok": true, "data": [...] }` with project names. Show the actual output.

If `401 Unauthorized` — the key is wrong or revoked. Go back to Step 3.
If `403 Forbidden` — the user is not a superuser. Tell them to contact their admin.
If `Connection refused` — API is not running. Stop and tell user.

### Step 6a — Copy the MCP server file

The MCP server script must exist in the consuming project's `.opencode/mcp/project-mcp/` directory.

- **If the consuming project has its own `.opencode/` tree** (e.g. `.ai.soc` does): copy the server now:
  ```bash
  mkdir -p .opencode/mcp/project-mcp
  cp /mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py \
     .opencode/mcp/project-mcp/
  ```
- **If the consuming project does NOT have `.opencode/`** (e.g. `.ai`, `.ai.ui`, `.ai.biz` frameworks themselves): explain:
  > This step is done in the **consuming project** (e.g. `tools-project/` or any app that uses this OS), not in the framework repo itself. When you deploy this OS to a project, copy the MCP server there.

### Step 6b — Register MCP in opencode.json

**If the consuming project has its own `opencode.json`** (e.g. `.ai.soc` at `/mnt/work/Projects/.ai.soc/opencode.json`):
Read the current file, then add the `mcp` block preserving all existing keys:

```json
{
  ...existing content...,
  "mcp": {
    "tools-project": {
      "type": "local",
      "command": ["python3", ".opencode/mcp/project-mcp/mcp_server.py"],
      "enabled": true
    }
  }
}
```

After writing, validate with `python3 -c "import json; json.load(open('opencode.json'))"`.

**If it does NOT have `opencode.json`** (like `.ai`, `.ai.ui`, `.ai.biz` framework repos):
Explain:
> The MCP server registration lives in the **consuming project's** opencode.json (e.g. `tools-project/opencode.json`, or any project that deploys this OS). It does not belong in the framework's own config. When you deploy this OS to a project, add the MCP block to THAT project's opencode.json. The reference guide has the exact block.

### Step 7 — Verify with completion checklist

Run each check and report the result:

| # | Check | How | Result |
|---|-------|-----|--------|
| 1 | Key file exists | `test -f ~/.tools-project-key` | pass / fail |
| 2 | Permissions 600 | `stat -c '%a' ~/.tools-project-key` shows `600` | pass / fail |
| 3 | API reachable | `curl -s <url>/healthz` returns 200 | pass / fail |
| 4 | Auth works | `curl -s <url>/v1/agent/projects -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)"` returns projects | pass / fail |
| 5 | MCP server file present | `test -f .opencode/mcp/project-mcp/mcp_server.py` (or consuming project) | pass / skip |
| 6 | MCP registered in opencode.json | `grep -q tools-project opencode.json` (or consuming project's config) | pass / skip |
| 7 | python3 available | `which python3` | pass / fail |

### Step 8 — Show OS-specific usage patterns

```
Connected to tools-project. Found N projects.

Your {OS_NAME} agents can now:

  {OS-specific capabilities from the table in Step 1}

To use this from any skill, add this prerequisite line
to the skill's preamble:

  Prerequisites: tools-project MCP server registered
  (provides list_projects, get_project_context,
  get_task_info, get_ticket_info, search_entities tools)

Reference: .work/docs/agent-query-api.md
Tutorial:  .work/docs/tutorials/LLM-2-API_SETUP.md
```

---

## Status protocol

Run `~/.tools-project-key` check and a live query. Report:

```
Key file:    {present/missing} ({path})
Permissions: {chmod} (should be 600)
API:         {reachable/unreachable} {url}
Auth:        {ok / 401 / 403}
Projects:    {count} accessible
MCP tools:   {count} registered ({names})
```

---

## Key protocol (standalone)

Same as Steps 3-4 from Install protocol. Lighter — no MCP registration, no API test (user runs `test` or `status` after).

---

## Test protocol

Same as Step 5 from Install protocol. Returns a yes/no + response snippet.

---

## Help protocol

Show the 5 MCP tools available and their descriptions. Then show one domain-specific example for the current OS:

| OS | Example |
|----|---------|
| Engineering | "What's the status of ticket TPR-T-12?" → `get_ticket_info(ref="TPR-T-12")` |
| UI Design | "What projects need UI work?" → `list_projects` + `get_task_info(status="todo")` |
| Business | "Which clients need attention?" → `list_projects` + `get_project_context()` per project |
| Security | "Find tickets related to rate limiting" → `search_entities(q="rate limit")` |

---

## Reference

| Doc | Path |
|-----|------|
| Full API + MCP guide | `.work/docs/agent-query-api.md` |
| Step-by-step tutorial | `.work/docs/tutorials/LLM-2-API_SETUP.md` |
| Feature SPEC | `.work/features/agent-query-api/20260701-SPEC.md` |
| MCP server source | `.opencode/mcp/project-mcp/mcp_server.py` |

---

## Anti-patterns to refuse

- Claiming "connected" without a live API response
- Writing the key file without `chmod 600` after
- Asking the user to paste their API key into chat
- Storing the key in `/tmp` or any non-`~/.tools-project-key` location
- Logging the key value in any output
- Registering MCP in the framework's own config (it belongs in the consuming project's opencode.json)
