#!/bin/sh
# The Claude Code CLI refuses bypassPermissions as root, and the Railway
# volume mounts root-owned — so: fix volume ownership as root, then drop
# to the unprivileged user for the actual app.
set -e
mkdir -p /app/data
chown -R clew:clew /app/data
exec runuser -u clew -- python app_oauth.py
