"""Every approved grant gets its own channel: Clew creates it, invites the
approver, and posts an AI brief (summary, amount, deadline, requirements —
cited, unknowns marked VERIFY). The team then works the grant there, with
Clew on hand via @mention."""

import asyncio
import json
import re
from logging import Logger

from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from listeners.events.tool_status import status_for
from storage import update_prospect

GRANT_BRIEF_PROMPT = """\
We just approved this grant prospect and opened a dedicated channel for it. \
Post a GRANT BRIEF for the team: (1) a plain-language summary of the funder/\
opportunity and why it fits us, (2) the award amount or range — only if \
supported by evidence, otherwise "VERIFY on the funder's site", (3) the \
deadline (same rule), (4) eligibility and application requirements you can \
verify, with everything unverified in a clearly-marked VERIFY list, and (5) \
suggested next steps. Research the funder with your search tools first. \
Keep it tight — this pins to the top of the channel.

PROSPECT:
{prospect_json}
"""


def channel_name_for(prospect_name: str) -> str:
    """Slack channel name: lowercase, [a-z0-9-], <=75 chars, grant- prefix."""
    slug = re.sub(r"[^a-z0-9]+", "-", prospect_name.lower()).strip("-")
    return f"grant-{slug}"[:75].rstrip("-")


async def create_grant_channel(
    client: AsyncWebClient,
    user_id: str,
    prospect: dict,
    team_id: str,
    logger: Logger,
    user_token: str | None = None,
) -> str | None:
    """Create the war-room channel, invite the approver, kick off the brief.
    Returns the channel id, or None when creation isn't possible (e.g. the
    bot lacks the channels:manage scope) — approval itself never fails."""
    base_name = channel_name_for(prospect["name"])
    channel_id = None
    for suffix in ("", "-2", "-3"):
        try:
            created = await client.conversations_create(
                name=f"{base_name[: 75 - len(suffix)]}{suffix}"
            )
            channel_id = created["channel"]["id"]
            break
        except SlackApiError as e:
            error = e.response.get("error", "")
            if error == "name_taken":
                continue
            if error == "missing_scope":
                logger.warning(
                    "Cannot create grant channels: bot lacks channels:manage. "
                    "Add the scope in the Slack app config and reinstall."
                )
                return None
            raise
    if not channel_id:
        return None

    await asyncio.to_thread(
        update_prospect, prospect["id"], grant_channel_id=channel_id
    )

    try:
        await client.conversations_invite(channel=channel_id, users=user_id)
    except SlackApiError:
        pass  # e.g. already_in_channel; the channel still works

    intro = await client.chat_postMessage(
        channel=channel_id,
        text=(
            f":thread: This is the war room for *{prospect['name']}* — "
            "approved from your shortlist. I'm pulling together a brief now. "
            "Mention @Clew here anytime for help with this grant."
        ),
    )

    # The brief runs the agent (search tools included) — post it in-channel.
    async def _tool_status(tool_name: str):
        label = status_for(tool_name)
        if label:
            try:
                await client.chat_update(channel=channel_id, ts=intro["ts"], text=label)
            except SlackApiError:
                pass

    prospect_json = json.dumps(
        {
            k: prospect.get(k)
            for k in (
                "name",
                "source",
                "program_area",
                "geography",
                "grant_size",
                "fit_rationale",
                "fit_sources",
                "deadline_date",
            )
        },
        default=str,
    )
    deps = AgentDeps(
        client=client,
        user_id=user_id,
        channel_id=channel_id,
        thread_ts=intro["ts"],
        message_ts=intro["ts"],
        team_id=team_id,
        user_token=user_token,
    )
    try:
        prompt_text = await prepend_org_profile(
            GRANT_BRIEF_PROMPT.format(prospect_json=prospect_json), team_id
        )
        brief, _ = await run_agent(prompt_text, deps=deps, on_tool_use=_tool_status)
        await client.chat_update(
            channel=channel_id,
            ts=intro["ts"],
            text=(
                f":thread: War room for *{prospect['name']}*. "
                "Mention @Clew here anytime for help with this grant."
            ),
        )
        if brief:
            posted = await client.chat_postMessage(channel=channel_id, text=brief)
            try:
                await client.pins_add(channel=channel_id, timestamp=posted["ts"])
            except SlackApiError:
                pass  # pinning is nice-to-have (needs pins:write)
    except Exception as e:
        logger.exception(f"Grant brief failed for {prospect['name']}: {e}")

    return channel_id
