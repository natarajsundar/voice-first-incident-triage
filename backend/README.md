# Backend

This is a tiny FastAPI service that:
1) Mints a LiveKit token by calling the Vocal Bridge token endpoint.
2) Returns `{ livekit_url, token, room_name, ... }` to the browser.
3) Optionally exposes a small `/api/policy` endpoint to help the client validate inbound actions.

## Run
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export VOCAL_BRIDGE_API_KEY=vb_...
uvicorn main:app --reload --port 8000
```
