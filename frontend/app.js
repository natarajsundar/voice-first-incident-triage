import { Room, RoomEvent, Track } from 'https://cdn.jsdelivr.net/npm/livekit-client/dist/livekit-client.esm.mjs';

const connectBtn = document.getElementById('connectBtn');
const disconnectBtn = document.getElementById('disconnectBtn');
const sendContextBtn = document.getElementById('sendContextBtn');
const statusEl = document.getElementById('status');
const audioMount = document.getElementById('audioMount');
const actionsLog = document.getElementById('actionsLog');
const draft = document.getElementById('draft');
const checklist = document.getElementById('checklist');

let room = null;

function setStatus(text) {
  statusEl.textContent = text;
}

function logAction(obj) {
  const line = JSON.stringify(obj, null, 2);
  actionsLog.textContent = (actionsLog.textContent + '\n' + line).trim();
}

function safeJsonParse(text) {
  try { return JSON.parse(text); } catch { return null; }
}

function applyAgentAction(action, payload) {
  switch (action) {
    case 'navigate': {
      const url = payload?.url;
      if (typeof url === 'string' && url.startsWith('http')) {
        window.open(url, '_blank', 'noopener,noreferrer');
      }
      break;
    }
    case 'open_runbook': {
      const url = payload?.url || 'https://example.com/runbook';
      window.open(url, '_blank', 'noopener,noreferrer');
      break;
    }
    case 'show_checklist': {
      // Optionally replace checklist with items
      const items = Array.isArray(payload?.items) ? payload.items : null;
      if (items) {
        checklist.innerHTML = '';
        for (const it of items) {
          const li = document.createElement('li');
          li.textContent = String(it);
          checklist.appendChild(li);
        }
      }
      break;
    }
    case 'draft_update': {
      if (typeof payload?.text === 'string') {
        draft.value = payload.text;
      }
      break;
    }
    default:
      // Unknown actions should be ignored by default (defense-in-depth)
      break;
  }
}

async function fetchToken() {
  const res = await fetch('http://localhost:8000/api/voice-token');
  if (!res.ok) throw new Error(`Failed token: ${res.status}`);
  return await res.json();
}

async function connect() {
  setStatus('connecting...');
  connectBtn.disabled = true;

  const tokenData = await fetchToken();
  room = new Room();

  room.on(RoomEvent.TrackSubscribed, (track) => {
    if (track.kind === Track.Kind.Audio) {
      const el = track.attach();
      el.autoplay = true;
      audioMount.innerHTML = '';
      audioMount.appendChild(el);
    }
  });

  room.on(RoomEvent.DataReceived, (payload, participant, kind, topic) => {
    if (topic !== 'client_actions') return;
    const decoded = new TextDecoder().decode(payload);
    const data = safeJsonParse(decoded);
    if (!data) return;

    logAction({ from: participant?.identity, ...data });

    // Expected shape:
    // { type: 'client_action', action: 'navigate', payload: {...} }
    if (data.type === 'client_action' && typeof data.action === 'string') {
      applyAgentAction(data.action, data.payload || {});
    }
  });

  room.on(RoomEvent.ConnectionStateChanged, (state) => setStatus(String(state)));
  room.on(RoomEvent.Disconnected, () => {
    setStatus('disconnected');
    connectBtn.disabled = false;
    disconnectBtn.disabled = true;
    sendContextBtn.disabled = true;
  });

  await room.connect(tokenData.livekit_url, tokenData.token);
  await room.localParticipant.setMicrophoneEnabled(true);

  disconnectBtn.disabled = false;
  sendContextBtn.disabled = false;
  setStatus('connected');
}

async function disconnect() {
  disconnectBtn.disabled = true;
  sendContextBtn.disabled = true;
  if (room) await room.disconnect();
  room = null;
}

async function sendContext() {
  if (!room) return;

  // Example: send context as a "notify" event (agent absorbs silently)
  const message = JSON.stringify({
    type: 'client_action',
    action: 'incident_context',
    payload: {
      service: 'checkout',
      region: 'us-east-1',
      signal: 'elevated_5xx',
      started_at: new Date().toISOString(),
    },
  });

  await room.localParticipant.publishData(
    new TextEncoder().encode(message),
    { reliable: true, topic: 'client_actions' }
  );

  logAction({ to: 'agent', ...safeJsonParse(message) });
}

connectBtn.addEventListener('click', () => connect().catch((e) => {
  console.error(e);
  setStatus('error');
  connectBtn.disabled = false;
}));
disconnectBtn.addEventListener('click', () => disconnect().catch(console.error));
sendContextBtn.addEventListener('click', () => sendContext().catch(console.error));
