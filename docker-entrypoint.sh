#!/usr/bin/env bash
set -e

"${VENV_PATH}/bin/supervisord" --configuration /etc/supervisord.conf &
SUPERVISOR_PID=$!

function shutdown {
  kill -s SIGTERM "${SUPERVISOR_PID}" 2>/dev/null || true
  wait "${SUPERVISOR_PID}" 2>/dev/null || true
}
trap shutdown SIGTERM SIGINT

echo "[entrypoint] Waiting for X display ${DISPLAY} to come up..."
for i in $(seq 1 30); do
  if xdpyinfo -display "${DISPLAY}" >/dev/null 2>&1; then
    echo "[entrypoint] Display ready."
    break
  fi
  sleep 1
done

echo "[entrypoint] Open http://localhost:7900 (password: secret) in your browser to see Chrome."
cd /app
python3 main.py

shutdown
