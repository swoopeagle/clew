"""War-room awareness: when a message comes from a channel Clew created for
an approved grant, prepend that grant's full context so the agent helps with
THIS grant without being told which one."""

import asyncio
import json
import re

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from storage import get_prospect_by_grant_channel

_CONTEXT_FIELDS = (
    "id",
    "name",
    "source",
    "program_area",
    "geography",
    "grant_size",
    "fit_rationale",
    "fit_sources",
    "stage",
    "deadline_date",
    "report_due_date",
)


async def prepend_grant_channel_context(text: str, channel_id: str | None) -> str:
    if not channel_id:
        return text
    prospect = await asyncio.to_thread(get_prospect_by_grant_channel, channel_id)
    if not prospect:
        return text

    grant_json = json.dumps({k: prospect.get(k) for k in _CONTEXT_FIELDS}, default=str)
    block = (
        "[GRANT WAR ROOM]\n"
        "This channel is dedicated to the following approved grant. Scope "
        "all help (applications, deadlines, requirements, research) to THIS "
        "grant — the user should never need to name it.\n"
        f"{grant_json}\n"
        "[END GRANT WAR ROOM]\n\n"
    )
    return block + text


async def prepend_channel_history(
    text: str,
    channel_id: str | None,
    client: AsyncWebClient,
    *,
    limit: int = 15,
) -> str:
    """For a grant war room, prepend a short transcript of the channel's recent
    messages so the agent is grounded in what the team has actually discussed
    here — not just the stored grant record. No-op outside war rooms; any
    failure (missing scope, not in channel) degrades silently to `text`."""
    if not channel_id:
        return text
    prospect = await asyncio.to_thread(get_prospect_by_grant_channel, channel_id)
    if not prospect:
        return text  # only war rooms get history injection

    try:
        resp = await client.conversations_history(channel=channel_id, limit=limit)
    except SlackApiError:
        return text

    lines: list[str] = []
    for msg in reversed(resp.get("messages") or []):  # API returns newest-first
        body = (msg.get("text") or "").strip()
        if not body:
            continue
        body = re.sub(r"\s+", " ", body)
        speaker = "Clew" if msg.get("bot_id") else f"<@{msg.get('user', 'unknown')}>"
        lines.append(f"{speaker}: {body}")
    if not lines:
        return text

    block = (
        "[CHANNEL HISTORY]\n"
        "Recent messages in this war room, oldest first. Ground your reply in "
        "what the team has already said here.\n"
        f"{chr(10).join(lines)}\n"
        "[END CHANNEL HISTORY]\n\n"
    )
    return block + text
