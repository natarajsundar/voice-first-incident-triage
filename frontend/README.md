# Frontend

Static HTML demo that:
- Fetches a LiveKit token from the backend (`/api/voice-token`)
- Connects to the room using `livekit-client`
- Plays agent audio
- Receives agent→app actions over the data channel (`topic=client_actions`)

Run:
```bash
python -m http.server 5173
```
Open http://localhost:5173
