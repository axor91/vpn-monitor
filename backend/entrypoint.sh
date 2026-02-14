#!/bin/sh
# Fix ownership of data dir (volume may be owned by root from previous builds)
# This runs as root, then drops to appuser via exec gosu/su-exec
chown -R appuser:appgroup /app/data 2>/dev/null || true
exec su -s /bin/sh appuser -c "uvicorn app.main:app --host 127.0.0.1 --port 8052 --workers 1"
