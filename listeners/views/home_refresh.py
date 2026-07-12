import asyncio
import os
from urllib.parse import urljoin

from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.app_home_builder import build_app_home_view
from storage import (
    get_org_profile,
    get_prospects_grouped_by_stage,
    list_open_tasks_by_org,
)


_workspace_url: str | None = None


async def _get_workspace_url(client: AsyncWebClient) -> str | None:
    """Workspace base URL (for message permalinks), cached after first call."""
    global _workspace_url
    if _workspace_url is None:
        try:
            auth = await client.auth_test()
            _workspace_url = auth.get("url") or ""
        except Exception:
            _workspace_url = ""
    return _workspace_url or None


async def _get_visible_channels(client: AsyncWebClient) -> dict | None:
    """Live snapshot of what Clew can see — the public channels it belongs to
    and a DM count — for the App Home transparency section. Queried fresh each
    time (Slack membership is the source of truth). Returns None on failure so
    the section is simply omitted. Private channels aren't listed (the bot lacks
    groups:read), but it can only be in ones it was explicitly added to."""
    try:
        pub = await client.users_conversations(types="public_channel", limit=200)
        names = sorted(c.get("name", "?") for c in pub.get("channels", []))
        dms = await client.users_conversations(types="im", limit=200)
        return {"channels": names, "dm_count": len(dms.get("channels", []))}
    except Exception:
        return None


async def publish_home(
    client: AsyncWebClient, user_id: str, team_id: str, user_token: str | None = None
) -> None:
    """(Re)publish the App Home view for a user. Called on app_home_opened
    and again after any action that changes org profile or board state,
    since Slack does not auto-refresh App Home."""
    install_url = None
    is_connected = False
    if os.environ.get("SLACK_CLIENT_ID"):
        if user_token:
            is_connected = True
        else:
            redirect_uri = os.environ.get("SLACK_REDIRECT_URI", "")
            install_url = urljoin(redirect_uri, "/slack/install")

    org_profile = await asyncio.to_thread(get_org_profile, team_id)
    board = await asyncio.to_thread(get_prospects_grouped_by_stage, team_id)
    open_tasks = await asyncio.to_thread(list_open_tasks_by_org, team_id)

    view = build_app_home_view(
        org_profile=org_profile,
        board=board,
        install_url=install_url,
        is_connected=is_connected,
        workspace_url=await _get_workspace_url(client),
        team_id=team_id,
        visible_channels=await _get_visible_channels(client),
        open_tasks=open_tasks,
    )
    await client.views_publish(user_id=user_id, view=view)
