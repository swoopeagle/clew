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


def _with_context_note(view: dict, note: str) -> dict:
    """Return a copy of the modal with a context note prepended."""
    return {
        **view,
        "blocks": [
            {"type": "context", "elements": [{"type": "mrkdwn", "text": note}]},
            *view["blocks"],
        ],
    }


def _drafting_view(source: str) -> dict:
    return {
        "type": "modal",
        "callback_id": "clew_ai_drafting",
        "title": {"type": "plain_text", "text": "Your Org Profile"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        f":sparkles: *Drafting your profile from {source}…*\n"
                        "This takes about 15 seconds. You'll review every "
                        "field before anything is saved."
                    ),
                },
            }
        ],
    }


async def handle_ai_draft_profile(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    view_id = body["view"]["id"]
    values = body["view"]["state"]["values"]
    website = (values.get("ai_website", {}).get("value", {}) or {}).get("value") or ""
    notes = (values.get("ai_notes", {}).get("value", {}) or {}).get("value") or ""

    try:
        if not website.strip() and not notes.strip():
            await client.views_update(
                view_id=view_id,
                view=_with_context_note(
                    build_org_profile_modal(None),
                    ":warning: Add your website or a few notes first, then "
                    "click Draft.",
                ),
            )
            return

        source = "your website" if website.strip() else "your notes"
        await client.views_update(view_id=view_id, view=_drafting_view(source))

        # Imported lazily: profile_draft pulls in the agent SDK query path,
        # which listeners otherwise don't need at import time.
        from agent.profile_draft import draft_org_profile

        draft = await draft_org_profile(website, notes)

        if draft:
            await client.views_update(
                view_id=view_id,
                view=_with_context_note(
                    build_org_profile_modal(draft),
                    ":sparkles: *Drafted by AI* — review and edit before saving.",
                ),
            )
        else:
            await client.views_update(
                view_id=view_id,
                view=_with_context_note(
                    build_org_profile_modal(None),
                    ":warning: Couldn't draft from that — check the URL or "
                    "add more detail, or just fill the form below.",
                ),
            )
    except Exception as e:
        logger.exception(f"Failed to AI-draft org profile: {e}")
