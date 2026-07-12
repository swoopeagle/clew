import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.actions.origin import resolve_origin
from listeners.views.app_home_builder import _pipeline_funnel
from listeners.views.board_builder import build_board_blocks
from listeners.views.home_refresh import _get_workspace_url
from storage import get_prospects_grouped_by_stage


async def handle_show_saved(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    """Post the grant board right in the user's DM — no Home tab required."""
    await ack()
    try:
        team_id = context.team_id or "default"
        grouped = await asyncio.to_thread(get_prospects_grouped_by_stage, team_id)

        blocks = []
        funnel = _pipeline_funnel(grouped)
        if funnel:
            blocks.append(
                {"type": "section", "text": {"type": "mrkdwn", "text": funnel}}
            )
        blocks.extend(
            build_board_blocks(grouped, workspace_url=await _get_workspace_url(client))
        )

        channel_id, thread_ts = await resolve_origin(client, body)
        await client.chat_postMessage(
            channel=channel_id,
            thread_ts=thread_ts,
            text="Your saved grants",
            blocks=blocks,
        )
    except Exception as e:
        logger.exception(f"Failed to show saved grants: {e}")
