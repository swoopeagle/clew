"""Read-only JSON API for the Clew web board.

The Slack app and its SQLite file remain the single source of truth; this
just exposes the same state the agent's MCP tools write, so the web board
can render it. No write endpoints — all actions stay in Slack.
"""

import asyncio
import hashlib
import hmac
import os
from datetime import datetime, timezone

from aiohttp import web

from storage import (
    count_tasks_by_prospect,
    get_org_profile,
    get_prospects_grouped_by_stage,
    list_org_ids,
)

STAGES = (
    "qualified",
    "approved",
    "applied",
    "submitted",
    "awarded",
    "declined",
    "passed",
)


def board_link(org_id: str) -> str:
    """Signed, org-scoped URL for the web board. Each workspace only ever
    hands out its own link (via Slack buttons), so one org can't reach
    another's board. Unsigned base URL when no secret is configured."""
    base = os.environ.get("CLEW_BOARD_URL", "https://clew-board.vercel.app")
    secret = os.environ.get("CLEW_BOARD_SECRET")
    if not secret:
        return base
    sig = hmac.new(secret.encode(), org_id.encode(), hashlib.sha256).hexdigest()[:20]
    return f"{base}?org={org_id}&sig={sig}"


def _authorized(request: web.Request) -> bool:
    token = os.environ.get("CLEW_API_TOKEN")
    if not token:
        return True
    provided = request.headers.get("Authorization", "")
    return hmac.compare_digest(provided, f"Bearer {token}")


async def handle_board(request: web.Request) -> web.Response:
    if not _authorized(request):
        return web.json_response({"error": "unauthorized"}, status=401)

    team_id = request.query.get("team", "") or await _default_team_id()
    profile = await asyncio.to_thread(get_org_profile, team_id)
    grouped = await asyncio.to_thread(get_prospects_grouped_by_stage, team_id)
    tasks = await asyncio.to_thread(count_tasks_by_prospect, team_id)

    return web.json_response(
        {
            "org_profile": profile,
            "board": {stage: grouped.get(stage, []) for stage in STAGES},
            "pipeline": {stage: len(grouped.get(stage, [])) for stage in STAGES},
            # keys stringified: JSON objects can't have int keys
            "tasks": {str(pid): counts for pid, counts in tasks.items()},
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )


async def _default_team_id() -> str:
    configured = os.environ.get("CLEW_TEAM_ID")
    if configured:
        return configured
    org_ids = await asyncio.to_thread(list_org_ids)
    return org_ids[0] if org_ids else "default"


async def start_web_api() -> None:
    """Serve GET /api/board on CLEW_WEB_API_PORT (default 3001)."""
    port = int(os.environ.get("CLEW_WEB_API_PORT", 3001))
    api = web.Application()
    api.add_routes([web.get("/api/board", handle_board)])
    runner = web.AppRunner(api)
    await runner.setup()
    await web.TCPSite(runner, host="0.0.0.0", port=port).start()
