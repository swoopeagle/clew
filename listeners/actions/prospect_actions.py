import asyncio
import os
from datetime import datetime, timezone
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.home_refresh import publish_home
from listeners.views.lifecycle_builders import (
    build_awarded_modal,
    build_deadline_modal,
    build_declined_modal,
)
from listeners.views.prospect_card_builder import build_decided_card_blocks
from storage import get_prospect, update_prospect


async def _warm_path_hint(user_token: str | None, funder_name: str) -> str | None:
    """Best-effort Real-Time Search check. Returns None (not a fabricated
    'no mentions found') whenever search isn't available or errors out."""
    if not user_token:
        return None
    try:
        user_client = AsyncWebClient(
            token=user_token,
            base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api/"),
        )
        resp = await user_client.search_messages(query=funder_name, count=3)
        matches = resp.get("messages", {}).get("matches", [])
        if not matches:
            return None
        return (
            f":mag: Found {len(matches)} prior workspace mention(s) of {funder_name}."
        )
    except Exception:
        return None


async def handle_approve_prospect(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        # Open the modal first — trigger_id expires 3 seconds after the click.
        await client.views_open(
            trigger_id=body["trigger_id"], view=build_deadline_modal(prospect_id)
        )

        await asyncio.to_thread(update_prospect, prospect_id, stage="approved")
        prospect = await asyncio.to_thread(get_prospect, prospect_id)

        if prospect.get("slack_channel_id") and prospect.get("slack_message_ts"):
            await client.chat_update(
                channel=prospect["slack_channel_id"],
                ts=prospect["slack_message_ts"],
                text=f"Approved: {prospect['name']}",
                blocks=build_decided_card_blocks(
                    prospect, ":white_check_mark: *Approved*"
                ),
            )

        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to approve prospect: {e}")


async def handle_pass_prospect(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        await asyncio.to_thread(update_prospect, prospect_id, stage="passed")
        prospect = await asyncio.to_thread(get_prospect, prospect_id)

        if prospect.get("slack_channel_id") and prospect.get("slack_message_ts"):
            await client.chat_update(
                channel=prospect["slack_channel_id"],
                ts=prospect["slack_message_ts"],
                text=f"Passed: {prospect['name']}",
                blocks=build_decided_card_blocks(prospect, ":x: *Passed*"),
            )

        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to pass prospect: {e}")


async def handle_refresh_home(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to refresh home: {e}")


async def _advance_stage_and_refresh(
    body: dict, client: AsyncWebClient, context: AsyncBoltContext, new_stage: str
) -> None:
    prospect_id = int(body["actions"][0]["value"])
    await asyncio.to_thread(update_prospect, prospect_id, stage=new_stage)
    team_id = context.team_id or "default"
    await publish_home(client, body["user"]["id"], team_id, context.user_token)


async def handle_mark_applied(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        await _advance_stage_and_refresh(body, client, context, "applied")
    except Exception as e:
        logger.exception(f"Failed to mark applied: {e}")


async def handle_mark_submitted(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        await _advance_stage_and_refresh(body, client, context, "submitted")
    except Exception as e:
        logger.exception(f"Failed to mark submitted: {e}")


async def handle_mark_awarded(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        prospect = await asyncio.to_thread(get_prospect, prospect_id)
        hint = await _warm_path_hint(context.user_token, prospect["name"])
        await client.views_open(
            trigger_id=body["trigger_id"], view=build_awarded_modal(prospect_id, hint)
        )
    except Exception as e:
        logger.exception(f"Failed to open awarded modal: {e}")


async def handle_mark_declined(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        prospect = await asyncio.to_thread(get_prospect, prospect_id)
        hint = await _warm_path_hint(context.user_token, prospect["name"])
        await client.views_open(
            trigger_id=body["trigger_id"], view=build_declined_modal(prospect_id, hint)
        )
    except Exception as e:
        logger.exception(f"Failed to open declined modal: {e}")


async def handle_mark_reported(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        await asyncio.to_thread(
            update_prospect,
            prospect_id,
            reported_at=datetime.now(timezone.utc).isoformat(),
        )
        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to mark reported: {e}")
