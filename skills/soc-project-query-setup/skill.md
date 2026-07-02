# SKILL: soc-project-query-setup

**Purpose:** Guide user through connecting their coding agent to tools-project, and teach it to query tasks, tickets, projects, and clients for context-aware work.

**Deploy to:** Security OS (`.ai`, `.ai.ui`, `.ai.biz`, `.ai.soc`) — optional integration.

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

If any prerequisite fails, stop and tell the user what to fix.

### Step 3 — Key creation (web UI)

Guide the user:

```
1. Open: <URL>/settings/api-keys
2. Click "+ New key"
3. Enter a label (e.g. "My laptop", "Agent OS integration")
4. Click "Create"
5. COPY the key now — it starts with "tools_project_"
```

Wait for the user to confirm they have the key. Do NOT ask them to paste it into chat.

### Step 4 — Create the key file

Tell the user to create `~/.tools-project-key` with their key:

```bash
# For local tools-project (no BASE_URL):
echo "tools_project_YOUR_KEY_HERE" > ~/.tools-project-key
chmod 600 ~/.tools-project-key

# For remote tools-project:
printf 'BASE_URL=https://project.cloudsys.win\ntools_project_YOUR_KEY_HERE\n' > ~/.tools-project-key
chmod 600 ~/.tools-project-key
```

**Critical:** Ask the user to replace `YOUR_KEY_HERE` with the actual key they copied. If the user is willing to paste the key into the conversation and asks you to write the file, run the command for them — but never log, display, or store the key value anywhere else. Always `chmod 600`.

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

### Step 6 — Deploy MCP server

**Detect if this project has an `opencode.json`:**

```bash
if test -f opencode.json; then
  echo "HAS_OPENCODE=yes"
else
  echo "HAS_OPENCODE=no"
fi
```

**Branch A — `opencode.json` exists in this project** (e.g. `.ai.soc`):
Copy the MCP server and register it in one reliable operation:

```bash
# 1. Copy the MCP server file
mkdir -p .opencode/mcp/project-mcp
cp /mnt/work/Projects/tools-project/.opencode/mcp/project-mcp/mcp_server.py \
   .opencode/mcp/project-mcp/

# 2. Add the MCP block to opencode.json using Python
#    (safe JSON manipulation — preserves all existing keys, validates input)
python3 << 'PYEOF'
import json
with open('opencode.json') as f:
    cfg = json.load(f)
cfg.setdefault('mcp', {})['tools-project'] = {
    "type": "local",
    "command": ["python3", ".opencode/mcp/project-mcp/mcp_server.py"],
    "enabled": True
}
with open('opencode.json', 'w') as f:
    json.dump(cfg, f, indent=2)
    f.write('\n')
PYEOF

# 3. Validate the result
python3 -c "import json; json.load(open('opencode.json')); print('opencode.json: valid')"
```

**Branch B — No `opencode.json` in this project** (e.g. `.ai`, `.ai.ui`, `.ai.biz`):
Explain:
> The MCP server and its registration belong in the **consuming project's** `opencode.json` (e.g. `tools-project/opencode.json`, or any project you deploy this OS into). They do not go in the framework's own config. When you deploy this OS to a project:
> 1. Copy `mcp_server.py` from tools-project to `.opencode/mcp/project-mcp/` in that project
> 2. Add the `mcp` block to that project's `opencode.json` (use the Branch A commands above, run from that project's root)

### Step 7 — Verify with completion checklist

Run each check and report the result:

| # | Check | How | Result |
|---|-------|-----|--------|
| 1 | Key file exists | `test -f ~/.tools-project-key` | pass / fail |
| 2 | Permissions 600 | `stat -c '%a' ~/.tools-project-key` shows `600` | pass / fail |
| 3 | API reachable | `curl -s <url>/healthz` returns 200 | pass / fail |
| 4 | Auth works | `curl -s <url>/v1/agent/projects -H "X-Api-Key: $(tail -n1 ~/.tools-project-key)"` returns projects | pass / fail |
| 5 | MCP server file present | `test -f .opencode/mcp/project-mcp/mcp_server.py` (or consuming project) | pass / skip |
| 6 | MCP registered in opencode.json | `python3 -c "import json; c=json.load(open('opencode.json')); print('yes' if 'tools-project' in c.get('mcp',{}) else 'no')"` (or consuming project's config) | pass / skip |
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
