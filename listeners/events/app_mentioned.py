import asyncio
import re
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

        # Strip the bot mention from the text
        cleaned_text = re.sub(r"<@[A-Z0-9]+>", "", text).strip()

        if not cleaned_text:
            await say(
                text="Hey there! How can I help you? Ask me anything and I'll do my best.",
                thread_ts=thread_ts,
            )
            return

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
        logger.exception(f"Failed to handle app mention: {e}")
        await say(
            text=f":warning: Something went wrong! ({e})",
            thread_ts=event.get("thread_ts") or event["ts"],
        )
