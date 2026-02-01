#!/usr/bin/env python3
"""Quick observability helper for Vocal Bridge.

This script shells out to the official `vb` CLI to fetch call logs as JSON and prints
a small health summary (counts by status, latest sessions).

Prereqs:
  pip install vocal-bridge
  vb auth login

Usage:
  python tools/observe_vb_logs.py --n 50
  python tools/observe_vb_logs.py --status failed --n 100
"""

import argparse
import json
import subprocess
from collections import Counter
from datetime import datetime
from typing import Any, Dict, List, Tuple


def run(cmd: List[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise SystemExit(f"Command failed ({p.returncode}): {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout


def extract_sessions(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if isinstance(payload, dict):
        # Common patterns: {"sessions":[...]} or {"data":[...]}
        for k in ("sessions", "data", "items"):
            v = payload.get(k)
            if isinstance(v, list):
                return [x for x in v if isinstance(x, dict)]
        # Otherwise, maybe it is a single session object
        if "session_id" in payload or "id" in payload:
            return [payload]
    return []


def pick(d: Dict[str, Any], *keys: str, default=None):
    for k in keys:
        if k in d and d[k] is not None:
            return d[k]
    return default


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="Number of logs to fetch")
    ap.add_argument("--offset", type=int, default=0)
    ap.add_argument("--status", type=str, default=None, help="Filter by status (e.g., completed|failed)")
    args = ap.parse_args()

    cmd = ["vb", "logs", "list", "-n", str(args.n), "--offset", str(args.offset), "--json"]
    if args.status:
        cmd.extend(["--status", args.status])

    raw = run(cmd)
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        raise SystemExit("vb output was not valid JSON. Try running without --json to inspect output.")

    sessions = extract_sessions(payload)
    if not sessions:
        print("No sessions found.")
        return

    status_counts = Counter(str(pick(s, "status", "state", default="unknown")).lower() for s in sessions)
    print("\n== VoiceOps Bridge: Vocal Bridge call log summary ==")
    print(f"Fetched sessions: {len(sessions)}")
    print("By status:")
    for k, v in status_counts.most_common():
        print(f"  - {k}: {v}")

    print("\nLatest sessions:")
    for s in sessions[: min(10, len(sessions))]:
        sid = pick(s, "session_id", "id", default="?")
        st = pick(s, "status", "state", default="?")
        started = pick(s, "started_at", "start_time", "created_at", default=None)
        dur = pick(s, "duration_seconds", "duration", default=None)
        print(f"  - {sid} | {st} | started={started} | duration={dur}")


if __name__ == "__main__":
    main()
