import asyncio
import json
import os
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from listeners.actions.origin import resolve_origin
from listeners.events.tool_status import status_for
from listeners.views.agent_message import build_agent_message_blocks
from storage import get_prospect

DRAFT_APPLICATION_PROMPT = """\
Help us apply for this approved grant prospect. RESEARCH FIRST: fetch the \
prospect's application_url and the funder's own website with fetch_webpage \
(plus your search tools) to find the actual application portal, current \
deadline, and stated requirements — do NOT skip this step. Then produce your \
APPLICATION HELP deliverable, and START it with "🔗 Apply here:" giving the \
exact application URL and confirmed deadline (or, if you truly couldn't find \
the portal after fetching, say which pages you checked). Follow with: fit \
summary, application outline (need statement, program description, \
outcomes/evaluation, budget narrative bullets), 2-3 reusable boilerplate \
paragraphs in our voice, and a checklist of the funder's stated requirements \
— mark an item "VERIFY on the funder's site" only if you fetched and still \
couldn't confirm it.

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
                    "application_url",
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
            canvas_made = await _try_canvas(
                context.user_token,
                prospect,
                response_text,
                logger,
                # Canvases attach to channels, not DMs — use the war room.
                canvas_channel=prospect.get("grant_channel_id"),
            )
            if canvas_made:
                await client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=(
                        f":page_facing_up: I've drafted the application for "
                        f"*{prospect['name']}* into the canvas of "
                        f"<#{prospect['grant_channel_id']}> — open the channel "
                        "canvas to edit it together."
                    ),
                )
            else:
                await client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=f"Application help for {prospect['name']}",
                    blocks=build_agent_message_blocks(response_text),
                )
    except Exception as e:
        logger.exception(f"Failed to draft application: {e}")


async def _try_canvas(
    user_token: str | None,
    prospect: dict,
    outline: str,
    logger: Logger,
    canvas_channel: str | None,
) -> bool:
    """Write the application draft into the war room's channel canvas — a
    living doc the team edits together. Requires the OAuth user token
    (canvases:write is a user scope) and a war-room channel; returns False
    on any miss so the caller falls back to posting the text in chat."""
    if not user_token or not canvas_channel:
        return False
    try:
        user_client = AsyncWebClient(
            token=user_token,
            base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api/"),
        )
        markdown = f"# Application draft — {prospect['name']}\n\n{outline}"
        await user_client.conversations_canvases_create(
            channel_id=canvas_channel,
            document_content={"type": "markdown", "markdown": markdown},
        )
        return True
    except SlackApiError as e:
        logger.warning(
            f"Canvas draft failed ({e.response.get('error')}); falling back to chat"
        )
        return False
    except Exception as e:
        logger.warning(f"Canvas draft failed ({e}); falling back to chat")
        return False
