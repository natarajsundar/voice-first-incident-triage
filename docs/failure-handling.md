# Failure handling — VoiceOps Bridge

Voice apps fail in different ways than normal web apps: network jitter, mic permissions, token expiry, and tool outages.

This doc defines the main failure modes and recommended mitigations.

---

## 1) Token minting failures (backend)
**Symptoms**
- `/api/voice-token` returns 4xx/5xx
- Client stuck on “connecting…”

**Mitigations**
- Retry with exponential backoff on network/5xx (cap attempts)
- Surface a user-friendly error (“Token service unavailable”)
- Add circuit breaker to avoid thundering herd if upstream is down
- Rate-limit token mint calls per IP/user

---

## 2) Token expiry (time-based)
**Symptoms**
- LiveKit disconnects around TTL boundary
- Client sees “token expired”

**Mitigations**
- Track `expires_in` and refresh before expiry
- Reconnect by fetching a new token (same session_id)
- If in-call reconnection fails, fall back to “call ended, please reconnect”

---

## 3) WebRTC connectivity issues
**Symptoms**
- Can’t connect from certain networks
- Audio cuts out

**Mitigations**
- Show LiveKit connection state in UI
- Allow manual reconnect
- Reduce CPU load: avoid unnecessary audio processing in browser
- Provide “text fallback” channel if needed

---

## 4) Microphone permissions denied
**Symptoms**
- Connects but no outgoing audio

**Mitigations**
- Prompt the user before enabling mic
- Detect permission denial and show instructions
- Offer a “listen-only” mode (no mic) for demos

---

## 5) STT/TTS degradation
**Symptoms**
- Agent hears wrong words
- Long response latency

**Mitigations**
- Add a “slow mode” message: “I’m experiencing latency, please repeat…”
- Encourage short, structured phrases for incident commands
- Provide UI shortcuts for key actions (checklist/runbook buttons)

---

## 6) MCP tool failures (downstream outages)
**Symptoms**
- Ticket creation fails
- Slack message not sent

**Mitigations**
- Treat tools as optional: agent continues triage without them
- Provide deterministic error messages (“Jira is unavailable; I can draft text instead”)
- Retry idempotent operations; never retry non-idempotent writes without confirmation

---

## 7) Client action abuse / malformed payloads
**Symptoms**
- Unexpected data-channel messages
- UI tries to navigate to unknown domains

**Mitigations**
- Strict allowlist of action names
- Payload size bounds
- Domain allowlist for URLs
- Log and ignore unknown actions

---

## 8) Feedback loops
**Symptoms**
- Agent and app trigger each other repeatedly (infinite loop)

**Mitigations**
- Classify app→agent events as `notify` by default
- Debounce repeated events
- Add loop detection: if same action repeats N times in M seconds, suppress and alert

