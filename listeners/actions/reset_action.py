"""Demo-testing reset: DM Clew "reset clew" → confirmation card → wipe the
org profile + prospects and archive the grant war-room channels.

Channels are ARCHIVED, not deleted — Slack's standard API has no hard
delete for bots (Enterprise admin only). Archived rooms leave the sidebar;
a re-approved grant with the same name gets a -2 suffix."""

import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.home_refresh import publish_home
from storage import get_prospects_grouped_by_stage, reset_org

RESET_PHRASES = {"reset clew", "clew reset", "/reset"}


def is_reset_request(text: str) -> bool:
    return text.strip().lower() in RESET_PHRASES


async def build_reset_confirmation_blocks(team_id: str) -> list[dict]:
    grouped = await asyncio.to_thread(get_prospects_grouped_by_stage, team_id)
    prospects = sum(len(rows) for rows in grouped.values())
    war_rooms = sum(
        1 for rows in grouped.values() for row in rows if row.get("grant_channel_id")
    )
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    ":broom: *Reset Clew for this workspace?*\n"
                    f"This wipes the org profile and *{prospects} prospect(s)*, "
                    f"and archives *{war_rooms} war-room channel(s)*. "
                    "This can't be undone."
                ),
            },
        },
        {
            "type": "actions",
            "block_id": "clew_reset_actions",
            "elements": [
                {
                    "type": "button",
                    "style": "danger",
                    "text": {"type": "plain_text", "text": "Yes, reset everything"},
                    "action_id": "clew_confirm_reset",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Cancel"},
                    "action_id": "clew_cancel_reset",
                },
            ],
        },
    ]


async def handle_confirm_reset(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        team_id = context.team_id or "default"
        result = await asyncio.to_thread(reset_org, team_id)

        archived = 0
        for channel_id in result["grant_channel_ids"]:
            try:
                await client.conversations_archive(channel=channel_id)
                archived += 1
            except SlackApiError as e:
                logger.warning(
                    f"Could not archive {channel_id}: {e.response.get('error')}"
                )

        await publish_home(client, body["user"]["id"], team_id, context.user_token)

        container = body.get("container") or {}
        await client.chat_update(
            channel=container.get("channel_id"),
            ts=container.get("message_ts"),
            text=(
                f":broom: *Reset done.* Profile cleared, "
                f"{result['prospect_count']} prospect(s) wiped, "
                f"{archived} channel(s) archived. Say hi to start fresh!"
            ),
        )
    except Exception as e:
        logger.exception(f"Failed to reset org: {e}")


async def handle_cancel_reset(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        container = body.get("container") or {}
        await client.chat_update(
            channel=container.get("channel_id"),
            ts=container.get("message_ts"),
            text="Reset cancelled — nothing was touched.",
        )
    except Exception as e:
        logger.exception(f"Failed to cancel reset: {e}")
