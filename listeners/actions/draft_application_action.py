import asyncio
import json
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from listeners.actions.origin import resolve_origin
from listeners.events.tool_status import status_for
from listeners.views.agent_message import build_agent_message_blocks
from storage import get_prospect

DRAFT_APPLICATION_PROMPT = """\
Help us apply for this approved grant prospect. Produce your APPLICATION HELP \
deliverable: fit summary, application outline (need statement, program \
description, outcomes/evaluation, budget narrative bullets), 2-3 reusable \
boilerplate paragraphs in our voice, and a requirements checklist with \
anything unverified marked "VERIFY on the funder's site". Research the funder \
with your search tools first if useful.

PROSPECT:
{prospect_json}
"""


async def handle_draft_application(
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
        if not prospect:
            return

        user_id = body["user"]["id"]
        team_id = context.team_id or "default"

        channel_id, origin_thread = await resolve_origin(client, body)
        initial = await client.chat_postMessage(
            channel=channel_id,
            thread_ts=origin_thread,
            text=f":writing_hand: Drafting an application outline for {prospect['name']}…",
        )
        thread_ts = initial["ts"]

        deps = AgentDeps(
            client=client,
            user_id=user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=thread_ts,
            user_token=context.user_token,
            team_id=team_id,
        )

        async def _tool_status(tool_name: str):
            label = status_for(tool_name)
            if label:
                await client.chat_update(channel=channel_id, ts=thread_ts, text=label)

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
        prompt_text = await prepend_org_profile(
            DRAFT_APPLICATION_PROMPT.format(prospect_json=prospect_json), team_id
        )
        response_text, _ = await run_agent(
            prompt_text, deps=deps, on_tool_use=_tool_status
        )

        await client.chat_update(
            channel=channel_id,
            ts=thread_ts,
            text=f":writing_hand: Application help for {prospect['name']}",
        )
        if response_text:
            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=f"Application help for {prospect['name']}",
                blocks=build_agent_message_blocks(response_text),
            )
    except Exception as e:
        logger.exception(f"Failed to draft application: {e}")
