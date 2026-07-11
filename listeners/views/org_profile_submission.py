import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.home_refresh import publish_home
from storage import upsert_org_profile


def _int_or_none(s: str | None) -> int | None:
    try:
        return int(s) if s else None
    except ValueError:
        return None


async def handle_org_profile_submission(
    ack: Ack,
    body: dict,
    view: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        values = view["state"]["values"]
        team_id = context.team_id or "default"

        await asyncio.to_thread(
            upsert_org_profile,
            org_id=team_id,
            mission=values["mission"]["value"]["value"],
            geography=values["geography"]["value"]["value"],
            program_areas=values["program_areas"]["value"]["value"],
            grant_size_min=_int_or_none(values["grant_size_min"]["value"].get("value")),
            grant_size_max=_int_or_none(values["grant_size_max"]["value"].get("value")),
            exclusions=values["exclusions"]["value"].get("value"),
        )

        user_id = body["user"]["id"]
        await publish_home(client, user_id, team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to save org profile: {e}")
