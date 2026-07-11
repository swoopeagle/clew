import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.app_home_builder import _pipeline_summary
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
        pipeline = _pipeline_summary(grouped)
        if pipeline:
            blocks.append(
                {
                    "type": "context",
                    "elements": [{"type": "mrkdwn", "text": pipeline}],
                }
            )
        blocks.extend(
            build_board_blocks(grouped, workspace_url=await _get_workspace_url(client))
        )

        dm = await client.conversations_open(users=body["user"]["id"])
        await client.chat_postMessage(
            channel=dm["channel"]["id"],
            text="Your saved grants",
            blocks=blocks,
        )
    except Exception as e:
        logger.exception(f"Failed to show saved grants: {e}")
