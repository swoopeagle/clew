import asyncio
import json
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.home_refresh import publish_home
from storage import get_prospect, update_prospect


def _prospect_id_from_metadata(view: dict) -> int:
    return json.loads(view["private_metadata"])["prospect_id"]


async def handle_deadline_submission(
    ack: Ack,
    body: dict,
    view: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = _prospect_id_from_metadata(view)
        deadline = view["state"]["values"]["deadline_date"]["value"].get(
            "selected_date"
        )
        if deadline:
            await asyncio.to_thread(
                update_prospect, prospect_id, deadline_date=deadline
            )
            # Keep the war-room topic in sync with the chosen deadline.
            prospect = await asyncio.to_thread(get_prospect, prospect_id)
            if prospect and prospect.get("grant_channel_id"):
                from listeners.grant_channel import set_grant_channel_topic

                await set_grant_channel_topic(
                    client, prospect["grant_channel_id"], prospect
                )

        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to save deadline: {e}")


async def handle_awarded_submission(
    ack: Ack,
    body: dict,
    view: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = _prospect_id_from_metadata(view)
        values = view["state"]["values"]
        report_due = values["report_due_date"]["value"].get("selected_date")
        retro_note = values.get("retro_note", {}).get("value", {}).get("value")

        fields = {"stage": "awarded"}
        if report_due:
            fields["report_due_date"] = report_due
        if retro_note:
            fields["retro_note"] = retro_note
        await asyncio.to_thread(update_prospect, prospect_id, **fields)

        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to save awarded outcome: {e}")


async def handle_declined_submission(
    ack: Ack,
    body: dict,
    view: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = _prospect_id_from_metadata(view)
        values = view["state"]["values"]
        retro_note = values.get("retro_note", {}).get("value", {}).get("value")

        fields = {"stage": "declined"}
        if retro_note:
            fields["retro_note"] = retro_note
        await asyncio.to_thread(update_prospect, prospect_id, **fields)

        team_id = context.team_id or "default"
        await publish_home(client, body["user"]["id"], team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to save declined outcome: {e}")
