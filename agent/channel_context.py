"""War-room awareness: when a message comes from a channel Clew created for
an approved grant, prepend that grant's full context so the agent helps with
THIS grant without being told which one."""

import asyncio
import json

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
