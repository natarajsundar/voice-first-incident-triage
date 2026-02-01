# Contributing

This repo is intentionally small for hackathon/demo use.

## Suggested contributions
- Add OpenTelemetry instrumentation to the backend.
- Add a domain allowlist + confirmation UI for sensitive actions.
- Add a post-processing webhook receiver + “artifact store” for summaries.
- Add tests for client action validation.

## Development
- Backend: `cd backend && uvicorn main:app --reload`
- Frontend: `cd frontend && python -m http.server 5173`

## Security
Do not commit API keys. Use `.env` locally and keep secrets in your environment.
