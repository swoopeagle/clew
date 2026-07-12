#!/usr/bin/env bash
# Keep Clew alive for judging weekend.
#
#   bash scripts/run_clew.sh
#
# What it does:
#   - caffeinate: the Mac won't sleep while this script runs (bot stays reachable)
#   - auto-restart: if app_oauth.py crashes, it comes back in a few seconds
#   - runs app_oauth.py (Socket Mode bot + OAuth + board API on :3001), which is
#     the runner we use once OAuth is installed. Do NOT also run app.py — two
#     Socket Mode connections = every event handled twice.
#
# Leave this running in a Terminal tab through Sunday 5PM PDT. Ctrl-C to stop.
# Note: the OAuth install is persisted to data/installations, so warm-path
# search keeps working across restarts. The :3000 tunnel is only needed to
# (re)install OAuth, not for normal running.

set -u
cd "$(dirname "$0")/.."

# Prevent sleep for as long as this script lives.
caffeinate -dimsu &
CAFFEINATE_PID=$!
cleanup() { kill "$CAFFEINATE_PID" 2>/dev/null || true; }
trap cleanup EXIT INT TERM

while true; do
  echo "[run_clew] $(date '+%H:%M:%S') starting app_oauth.py"
  .venv/bin/python app_oauth.py
  code=$?
  echo "[run_clew] $(date '+%H:%M:%S') app_oauth.py exited (code $code) — restarting in 3s"
  sleep 3
done
