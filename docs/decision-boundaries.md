# Decision boundaries — VoiceOps Bridge

Decision boundaries are the explicit rules that determine:
- what the agent is allowed to do,
- when it must ask for confirmation,
- what it must never do,
- and how the app enforces those rules.

This project assumes two enforcement layers:
1) **Prompt + tool definitions** (agent-level)
2) **Client policy validation** (app-level)

---

## 1) Capability boundaries

### Allowed by default (safe, read-only)
- Explain triage steps and best practices
- Ask clarifying questions
- Open runbooks / dashboards (navigate actions)
- Show incident checklists
- Draft updates (but **do not send** without confirmation)

### Allowed with confirmation (write / irreversible)
- Notify stakeholders (Slack, email)
- Create or update a ticket (Jira, ServiceNow)
- Page on-call / escalate
- Post status-page updates
- Trigger mitigations (rollback, flag flip, traffic shift)

### Never allowed (hard ban)
- Execute destructive actions *without explicit, recorded confirmation*
- Exfiltrate secrets (API keys, tokens)
- Request or store sensitive personal data (SSNs, bank info, passwords)
- Generate instructions that violate your company’s incident policy

---

## 2) Confirmation policy (two-step)
For any action in `requires_confirmation`:
1) Agent must state: **intent + consequences**
2) User must confirm with an unambiguous “yes” (or click a UI confirm)

If confirmation is missing or ambiguous:
- agent must ask again or abort

---

## 3) Tool routing boundaries (MCP)
If MCP tools are enabled, use a “least privilege” model:
- Read tools: dashboards, incident metadata, runbooks
- Write tools: tickets, messaging, paging

**Rule**: never call write tools unless the user confirmation state is `confirmed`.

---

## 4) Client Actions boundaries (Agent → App)
The app only executes actions on an allowlist:

- `navigate`
- `open_runbook`
- `show_checklist`
- `draft_update`

All other actions are logged but ignored.

**Payload constraints**
- Max payload size: 8KB (configurable)
- Must be valid JSON
- URLs must be `https://` and match an allowed domain list (recommended for prod)

---

## 5) “Respond vs Notify” boundary (App → Agent)
Inbound events should be classified:
- **respond**: agent speaks immediately (use sparingly)
- **notify**: agent absorbs silently (default)

This prevents feedback loops where:
agent → app action → app → agent event → agent speaks → repeat.

---

## 6) Safe completion boundaries
If the agent is uncertain:
- it must ask clarifying questions rather than guessing
- it should offer a “next best action” checklist

If the user requests an out-of-scope action:
- agent should explain limits and provide safe alternatives

---

## 7) Examples

### Example: Draft Slack update (allowed)
Agent publishes:
```json
{ "type": "client_action", "action": "draft_update", "payload": { "text": "Investigating elevated 5xx on checkout..." } }
```

### Example: Send Slack update (confirmation required)
Agent says:
> I can send this update to #incidents. This will notify the whole team. Should I send it?

Only if confirmed:
- agent calls MCP `send_slack_message` (write tool)

