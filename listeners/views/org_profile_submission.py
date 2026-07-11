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


def parse_org_profile_values(values: dict) -> tuple[dict, dict]:
    """Parse the org-profile modal state into storage fields.

    Returns (fields, errors). ``errors`` maps block_ids to messages for
    ``ack(response_action="errors")``; ``fields`` serialize to the existing
    org_profile columns (program_areas stays one comma-joined string).
    """
    selected = [
        o["value"]
        for o in values["program_areas"]["value"].get("selected_options") or []
    ]
    other_raw = values["program_areas_other"]["value"].get("value") or ""
    others = [s.strip() for s in other_raw.split(",") if s.strip()]
    seen = {s.lower() for s in selected}
    program_areas = ", ".join(selected + [o for o in others if o.lower() not in seen])

    grant_size_min = _int_or_none(values["grant_size_min"]["value"].get("value"))
    grant_size_max = _int_or_none(values["grant_size_max"]["value"].get("value"))

    errors: dict[str, str] = {}
    if not program_areas:
        errors["program_areas"] = (
            "Pick at least one program area (or add one under “Other”)."
        )
    if (
        grant_size_min is not None
        and grant_size_max is not None
        and grant_size_min > grant_size_max
    ):
        errors["grant_size_max"] = "Maximum must be at least the minimum grant size."

    fields = {
        "mission": values["mission"]["value"]["value"],
        "geography": values["geography"]["value"]["value"],
        "program_areas": program_areas,
        "grant_size_min": grant_size_min,
        "grant_size_max": grant_size_max,
        "exclusions": values["exclusions"]["value"].get("value"),
    }
    return fields, errors


async def handle_org_profile_submission(
    ack: Ack,
    body: dict,
    view: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    fields, errors = parse_org_profile_values(view["state"]["values"])
    if errors:
        await ack(response_action="errors", errors=errors)
        return
    await ack()
    try:
        team_id = context.team_id or "default"
        await asyncio.to_thread(upsert_org_profile, org_id=team_id, **fields)

        user_id = body["user"]["id"]
        await publish_home(client, user_id, team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to save org profile: {e}")
