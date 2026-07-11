import asyncio
from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_bolt.context.say.async_say import AsyncSay
from slack_bolt.context.say_stream.async_say_stream import AsyncSayStream
from slack_bolt.context.set_status.async_set_status import AsyncSetStatus
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from thread_context import session_store
from listeners.events.tool_status import status_for
from listeners.views.feedback_builder import build_feedback_blocks
from listeners.views.setup_prompt_builder import build_profile_setup_blocks
from storage import get_org_profile


async def handle_message(
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    event: dict,
    logger: Logger,
    say: AsyncSay,
    say_stream: AsyncSayStream,
    set_status: AsyncSetStatus,
):
    """Handle messages sent to the agent via DM or in threads the bot is part of."""
    # Skip message subtypes (edits, deletes, etc.) and bot messages.
    if event.get("subtype"):
        return
    if event.get("bot_id"):
        return

    is_dm = event.get("channel_type") == "im"
    is_thread_reply = event.get("thread_ts") is not None

    if is_dm:
        pass
    elif is_thread_reply:
        # Channel thread replies are handled only if the bot is already engaged
        session = session_store.get_session(context.channel_id, event["thread_ts"])
        if session is None:
            return
    else:
        # Top-level channel messages are handled by app_mentioned
        return

    try:
        channel_id = context.channel_id
        text = event.get("text", "")
        thread_ts = event.get("thread_ts") or event["ts"]

        # Get session ID for conversation context
        existing_session_id = session_store.get_session(channel_id, thread_ts)

        # Set assistant thread status with loading messages
        await set_status(
            status="Thinking...",
            loading_messages=[
                "Teaching the hamsters to type faster…",
                "Untangling the internet cables…",
                "Consulting the office goldfish…",
                "Polishing up the response just for you…",
                "Convincing the AI to stop overthinking…",
            ],
        )

        # Run the agent with deps for tool access
        user_id = context.user_id
        team_id = context.team_id or "default"
        deps = AgentDeps(
            client=client,
            user_id=user_id,
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

        prompt_text = await prepend_org_profile(text, team_id)
        response_text, new_session_id = await run_agent(
            prompt_text,
            session_id=existing_session_id,
            deps=deps,
            on_tool_use=_tool_status,
        )

        # Stream response in thread with feedback buttons; when no org
        # profile exists yet, add a one-click setup button under the reply.
        streamer = await say_stream()
        await streamer.append(markdown_text=response_text)
        trailing_blocks = list(build_feedback_blocks())
        if not await asyncio.to_thread(get_org_profile, team_id):
            trailing_blocks = build_profile_setup_blocks() + trailing_blocks
        await streamer.stop(blocks=trailing_blocks)

        # Store session ID for future context
        if new_session_id:
            session_store.set_session(channel_id, thread_ts, new_session_id)

    except Exception as e:
        logger.exception(f"Failed to handle message: {e}")
        await say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event.get("ts"),
        )
