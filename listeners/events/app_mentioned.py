import asyncio
import re
from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.say_stream.async_say_stream import AsyncSayStream
from slack_bolt.context.set_status.async_set_status import AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.channel_context import (
    prepend_channel_history,
    prepend_grant_channel_context,
)
from agent.org_context import prepend_org_profile
from thread_context import session_store
from listeners.events.tool_status import status_for
from listeners.views.feedback_builder import build_feedback_blocks
from listeners.views.setup_prompt_builder import (
    build_chat_nav_blocks,
    build_grant_nav_blocks,
    build_profile_setup_blocks,
)
from storage import get_org_profile, get_prospect_by_grant_channel


async def handle_app_mentioned(
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
    say: AsyncSay,
    say_stream: AsyncSayStream,
    set_status: AsyncSetStatus,
):
    """Handle @mentions in channels."""
    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        # Strip ONLY the bot's own mention — teammate mentions must survive
        # (e.g. "have <@U123> pull the financials" drives task assignment).
        bot_user_id = context.bot_user_id or ""
        cleaned_text = re.sub(rf"<@{re.escape(bot_user_id)}(\|[^>]*)?>", "", text).strip()

        if not cleaned_text:
            from listeners.views.welcome_builder import build_welcome_blocks

            await say(
                text="Hi, I'm Clew — grant prospecting for small nonprofit teams.",
                blocks=build_welcome_blocks(),
                thread_ts=thread_ts,
            )
            return

        # Set assistant thread status with loading messages
        await set_status(
            status="Thinking...",
            loading_messages=[
                "Pulling the thread…",
                "Cross-checking funders against your profile…",
                "Screening for fit…",
                "Lining up the evidence…",
                "Verifying every citation…",
            ],
        )

        # Get session ID for conversation context
        existing_session_id = session_store.get_session(channel_id, thread_ts)

        # Run the agent with deps for tool access
        team_id = context.team_id or "default"
        deps = AgentDeps(
            client=client,
            user_id=context.user_id,
            channel_id=channel_id,
            thread_ts=thread_ts,
            message_ts=event["ts"],
            user_token=context.user_token,
            team_id=team_id,
            app_id=body.get("api_app_id"),
        )

        async def _tool_status(tool_name: str):
            label = status_for(tool_name)
            if label:
                await set_status(status=label)

        prompt_text = await prepend_org_profile(cleaned_text, team_id)
        prompt_text = await prepend_grant_channel_context(prompt_text, channel_id)
        prompt_text = await prepend_channel_history(prompt_text, channel_id, client)
        response_text, new_session_id = await run_agent(
            prompt_text,
            session_id=existing_session_id,
            deps=deps,
            on_tool_use=_tool_status,
        )

        # Stream response with trailing buttons scoped to the surface: a war
        # room gets THIS grant's actions, elsewhere the org-wide nav (or the
        # setup nudge when no profile exists yet).
        streamer = await say_stream()
        await streamer.append(markdown_text=response_text)
        trailing_blocks = list(build_feedback_blocks())
        war_room = await asyncio.to_thread(get_prospect_by_grant_channel, channel_id)
        if war_room:
            trailing_blocks = build_grant_nav_blocks(war_room) + trailing_blocks
        elif await asyncio.to_thread(get_org_profile, team_id):
            trailing_blocks = build_chat_nav_blocks(team_id) + trailing_blocks
        else:
            trailing_blocks = build_profile_setup_blocks() + trailing_blocks
        await streamer.stop(blocks=trailing_blocks)

        # Store session ID for future context
        if new_session_id:
            session_store.set_session(channel_id, thread_ts, new_session_id)

    except Exception as e:
        logger.exception(f"Failed to handle app mention: {e}")
        await say(
            text=":warning: Something went wrong on my end — please try again in a moment.",
            thread_ts=event.get("thread_ts") or event["ts"],
        )
