import asyncio
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from listeners.actions.origin import resolve_origin
from listeners.events.tool_status import status_for
from listeners.views.agent_message import build_agent_message_blocks
from listeners.views.setup_prompt_builder import build_profile_setup_blocks
from storage import get_org_profile

FIND_GRANTS_PROMPT = (
    "Find grants and foundations that fit our org profile and post any qualified "
    "prospects for review. Run the complete sweep before replying: Grants.gov for "
    "each program area, ProPublica foundations for our geography and areas (with "
    "990 checks on promising ones), and USAspending for what similar orgs have "
    "won. Don't stop after one source or ask permission to continue."
)


async def handle_find_grants(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    # Tracked outside the try so the error path can replace the "Searching…"
    # placeholder instead of leaving it frozen forever (the exact failure mode
    # the per-source timeouts were meant to prevent).
    channel_id: str | None = None
    progress_ts: str | None = None
    try:
        user_id = body["user"]["id"]
        team_id = context.team_id or "default"

        # Answer where the button was clicked (channel thread), falling
        # back to the user's DM for App Home clicks.
        channel_id, origin_thread = await resolve_origin(client, body)

        # Without a profile the agent can only ask for one — skip the run
        # and offer the one-click setup path instead.
        if not await asyncio.to_thread(get_org_profile, team_id):
            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=origin_thread,
                text="Set up your org profile first so Clew can screen grants for fit.",
                blocks=build_profile_setup_blocks(),
            )
            return

        initial = await client.chat_postMessage(
            channel=channel_id,
            thread_ts=origin_thread,
            text="Looking for grants that fit your org profile...",
        )
        progress_ts = initial["ts"]
        thread_ts = origin_thread or progress_ts

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
                await client.chat_update(channel=channel_id, ts=progress_ts, text=label)

        prompt_text = await prepend_org_profile(FIND_GRANTS_PROMPT, team_id)
        response_text, _ = await run_agent(
            prompt_text, deps=deps, on_tool_use=_tool_status
        )

        if response_text:
            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text="Grant search summary",
                blocks=build_agent_message_blocks(response_text),
            )
    except Exception as e:
        logger.exception(f"Failed to run Find Grants: {e}")
        # Never leave the "Searching…" placeholder spinning. Turn it into a
        # plain, honest retry prompt.
        if channel_id and progress_ts:
            try:
                await client.chat_update(
                    channel=channel_id,
                    ts=progress_ts,
                    text=(
                        ":warning: The grant search hit a snag and didn't finish. "
                        "Please click *Find Grants* to try again."
                    ),
                )
            except Exception:
                pass
