# Observability — VoiceOps Bridge

A voice agent system spans multiple subsystems:
- client device (browser audio, mic permissions)
- WebRTC transport (LiveKit)
- voice stack (STT/LLM/TTS)
- tool calls / MCP
- post-processing
- your backend token service

This doc defines **what to measure**, **how to correlate**, and **how to debug**.

---

## 1) Correlation: the `session_id`
Every voice interaction should have a unique `session_id` that appears in:
- backend logs (token mint)
- client console logs (connect/disconnect)
- Vocal Bridge call logs and transcripts (where available)
- post-processing artifacts (summary, ticket ids)

In this repo the backend generates `session_id` if not provided.

---

## 2) Signals

### A) Logs (structured)
Backend logs (recommend JSON):
- request_id
- session_id
- latency_ms
- upstream_status (token endpoint status code)
- error_class

Client logs:
- LiveKit connection state transitions
- mic permission granted/denied
- audio track subscribed events
- client_action events received/executed

### B) Metrics
**Backend**
- `token_mint_success_total`
- `token_mint_error_total{status_code}`
- `token_mint_latency_ms` (p50/p95/p99)
- `rate_limited_total`

**Client**
- `connect_success_total`
- `connect_failure_total`
- `reconnect_attempt_total`

**Voice session (platform)**
- call duration
- call outcomes: completed / failed
- STT/agent/tool error counts (if exposed via platform debug events)

### C) Traces
If you add OpenTelemetry later:
- Span: `GET /api/voice-token`
- Attributes: `session_id`, `participant`, `expires_in`
- Propagate `session_id` to any async job that handles post-processing.

---

## 3) Debugging workflow

### A) Fast path: check call logs + stats
If you use the official CLI, you can:
- list recent call sessions
- view transcripts and status
- pull basic stats

### B) Live debugging: debug event stream
Enable debug mode for the agent and stream events during a call.
Useful events include:
- user transcription
- agent responses
- tool calls/results
- errors

### C) Recording-based analysis
If recording is enabled, download a session recording and review:
- turn-taking latency
- interruptions / barge-in behavior
- misrecognitions

---

## 4) Alerts (what should page you)
- spike in failed calls over 5 minutes
- token endpoint error rate > 1%
- repeated reconnect loops (client)
- post-processing failures (if workflows enabled)

---

## 5) Redaction / privacy
- Avoid storing raw transcripts long-term unless required.
- Redact secrets and sensitive data from logs.
- If you store recordings, limit access and define retention.

