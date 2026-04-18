# FRIDAY OS — Desktop shell

Slim Tauri + React + Vite wrapper. Points at a running FRIDAY A2A server and
gives you a chat UI in a native window.

## Prerequisites

- Node 20+
- Rust toolchain + Tauri prereqs: https://v2.tauri.app/start/prerequisites/
- A running FRIDAY A2A server (default `http://localhost:8001`)

## Run

```bash
# Terminal 1 — start FRIDAY
pip install -e ".[a2a]"
python -m friday.core.a2a.server  # or: uvicorn friday.core.a2a.server:build_app --factory --port 8001

# Terminal 2 — desktop shell
cd desktop
npm install
npm run tauri dev
```

## Point at a different FRIDAY instance

```bash
VITE_FRIDAY_URL=http://192.168.1.42:8001 npm run tauri dev
```
