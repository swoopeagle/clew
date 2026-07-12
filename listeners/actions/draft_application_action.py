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
Help us apply for this approved grant prospect. RESEARCH FIRST — run your \
FUNDER RESEARCH LOOP: WebSearch the funder if you don't have their site, \
fetch_webpage the prospect's application_url and/or the funder's own \
website, and follow the grants/apply links in the fetch output to find the \
actual application portal, current deadline, and stated requirements — do \
NOT skip this step. Then produce your \
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
            canvas_url = await _try_canvas(
                client,
                context.user_token,
                prospect,
                response_text,
                logger,
                # Canvases attach to channels, not DMs — use the war room.
                canvas_channel=prospect.get("grant_channel_id"),
                team_id=team_id,
            )
            if canvas_url is not None:
                link = (
                    f" — <{canvas_url}|*open the draft*>." if canvas_url else "."
                )
                await client.chat_postMessage(
                    channel=channel_id,
                    thread_ts=thread_ts,
                    text=(
                        f":page_facing_up: I've drafted the application for "
                        f"*{prospect['name']}* into the canvas of "
                        f"<#{prospect['grant_channel_id']}>{link} It also "
                        "lives under the canvas icon at the top of that "
                        "channel — edit it together there."
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


def _channel_canvas_id(channel: dict) -> str | None:
    """The channel's existing canvas file id, from conversations_info data.
    Slack exposes it either as a canvas-type tab or a canvas property."""
    props = channel.get("properties") or {}
    for tab in props.get("tabs") or []:
        if tab.get("type") == "canvas":
            file_id = (tab.get("data") or {}).get("file_id")
            if file_id:
                return file_id
    return (props.get("canvas") or {}).get("file_id")


async def _try_canvas(
    client: AsyncWebClient,
    user_token: str | None,
    prospect: dict,
    outline: str,
    logger: Logger,
    canvas_channel: str | None,
    team_id: str,
) -> str | None:
    """Write the application draft into the war room's channel canvas — a
    living doc the team edits together. A channel has at most ONE canvas, so
    a re-draft replaces the existing canvas's content instead of failing.
    Returns the canvas URL ("" when the workspace URL is unknown) on success,
    or None on any miss so the caller falls back to posting the text in chat.
    Requires the OAuth user token (canvases:write is a user scope)."""
    if not user_token or not canvas_channel:
        return None
    document_content = {
        "type": "markdown",
        "markdown": f"# Application draft — {prospect['name']}\n\n{outline}",
    }
    try:
        user_client = AsyncWebClient(
            token=user_token,
            base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api/"),
        )
        try:
            created = await user_client.conversations_canvases_create(
                channel_id=canvas_channel,
                document_content=document_content,
            )
            canvas_id = created.get("canvas_id")
        except SlackApiError as e:
            if e.response.get("error") != "channel_canvas_already_exists":
                raise
            info = await client.conversations_info(channel=canvas_channel)
            canvas_id = _channel_canvas_id(info.get("channel") or {})
            if not canvas_id:
                raise
            await user_client.canvases_edit(
                canvas_id=canvas_id,
                changes=[
                    {
                        "operation": "replace",
                        "document_content": document_content,
                    }
                ],
            )

        # Deep link straight to the doc — "open the channel canvas" sent
        # people hunting; a clickable link doesn't.
        from listeners.views.home_refresh import _get_workspace_url

        base = await _get_workspace_url(client)
        if base and canvas_id:
            return f"{base.rstrip('/')}/docs/{team_id}/{canvas_id}"
        return ""
    except SlackApiError as e:
        logger.warning(
            f"Canvas draft failed ({e.response.get('error')}); falling back to chat"
        )
        return None
    except Exception as e:
        logger.warning(f"Canvas draft failed ({e}); falling back to chat")
        return None
