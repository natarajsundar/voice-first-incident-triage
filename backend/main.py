import os
import time
import uuid
from typing import Optional, Dict, Any

import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

VOCAL_BRIDGE_API_KEY = os.environ.get("VOCAL_BRIDGE_API_KEY")
VOCAL_BRIDGE_API_URL = os.environ.get("VOCAL_BRIDGE_API_URL", "http://vocalbridgeai.com").rstrip("/")
REQUEST_TIMEOUT_S = float(os.environ.get("VOCAL_BRIDGE_TIMEOUT_S", "10"))

app = FastAPI(
    title="VoiceOps Bridge API",
    version="0.1.0",
    description="Token proxy + minimal APIs for a Vocal Bridge / LiveKit voice agent demo.",
)

# Dev-friendly CORS (tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ALLOW_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class VoiceTokenResponse(BaseModel):
    livekit_url: str
    token: str
    room_name: str
    participant_identity: str
    expires_in: int
    agent_mode: Optional[str] = None


@app.get("/healthz")
def healthz() -> Dict[str, Any]:
    return {"ok": True, "service": "voiceops-bridge-api", "time": int(time.time())}


@app.get("/api/voice-token", response_model=VoiceTokenResponse)
def get_voice_token(
    participant_name: str = Query(default="Web User", max_length=64),
    session_id: Optional[str] = Query(default=None, max_length=128),
) -> Dict[str, Any]:
    """Mint a short-lived LiveKit token via Vocal Bridge.

    IMPORTANT:
    - Keep VOCAL_BRIDGE_API_KEY server-side.
    - The client only receives the LiveKit URL + token.
    """
    if not VOCAL_BRIDGE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing VOCAL_BRIDGE_API_KEY")

    # If caller doesn't provide a session_id, we generate one for correlation.
    sess = session_id or f"vo-{uuid.uuid4()}"

    url = f"{VOCAL_BRIDGE_API_URL}/api/v1/token"
    try:
        resp = requests.post(
            url,
            headers={
                "X-API-Key": VOCAL_BRIDGE_API_KEY,
                "Content-Type": "application/json",
            },
            json={
                "participant_name": participant_name,
                "session_id": sess,
            },
            timeout=REQUEST_TIMEOUT_S,
        )
    except requests.RequestException as e:
        raise HTTPException(status_code=502, detail=f"Token request failed: {e}") from e

    if resp.status_code >= 400:
        # Avoid leaking secrets in error messages
        raise HTTPException(status_code=resp.status_code, detail=f"Token endpoint error: {resp.text[:300]}")

    data = resp.json()
    # Add our generated session id for client correlation if upstream didn't echo it
    data.setdefault("session_id", sess)
    return data


# Optional: a tiny policy endpoint used by the UI for local action validation
@app.get("/api/policy")
def get_policy() -> Dict[str, Any]:
    return {
        "allowed_agent_actions": ["navigate", "open_runbook", "show_checklist", "draft_update"],
        "requires_confirmation": ["notify_stakeholders", "create_ticket", "page_oncall"],
        "max_action_payload_bytes": 8_192,
    }
