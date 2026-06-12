#!/bin/sh
set -e
# Volume may be owned by root from a previous build — fix it while still root,
# then drop privileges with gosu (exec replaces PID 1, so SIGTERM reaches
# uvicorn for a clean shutdown).
chown -R appuser:appgroup /app/data 2>/dev/null || true

HOST="${VPN_HOST:-127.0.0.1}"
PORT="${VPN_PORT:-8052}"

exec gosu appuser uvicorn app.main:app --host "$HOST" --port "$PORT" --workers 1
