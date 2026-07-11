import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.org_profile_builder import build_org_profile_modal
from storage import get_org_profile


async def handle_open_org_profile(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        team_id = context.team_id or "default"
        existing = await asyncio.to_thread(get_org_profile, team_id)
        await client.views_open(
            trigger_id=body["trigger_id"], view=build_org_profile_modal(existing)
        )
    except Exception as e:
        logger.exception(f"Failed to open org profile modal: {e}")
