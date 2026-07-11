import asyncio
import os
from urllib.parse import urljoin

from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.app_home_builder import build_app_home_view
from storage import get_org_profile, get_prospects_grouped_by_stage


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

    view = build_app_home_view(
        org_profile=org_profile,
        board=board,
        install_url=install_url,
        is_connected=is_connected,
    )
    await client.views_publish(user_id=user_id, view=view)
