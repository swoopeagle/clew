from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from agent import AgentDeps, run_agent
from agent.org_context import prepend_org_profile
from listeners.views.feedback_builder import build_feedback_blocks

FIND_GRANTS_PROMPT = (
    "Find grants and foundations that fit our org profile and post any qualified "
    "prospects for review."
)


async def handle_find_grants(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        user_id = body["user"]["id"]
        team_id = context.team_id or "default"

        dm = await client.conversations_open(users=user_id)
        channel_id = dm["channel"]["id"]

        initial = await client.chat_postMessage(
            channel=channel_id,
            text="Looking for grants that fit your org profile...",
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
        prompt_text = await prepend_org_profile(FIND_GRANTS_PROMPT, team_id)
        response_text, _ = await run_agent(prompt_text, deps=deps)

        if response_text:
            await client.chat_postMessage(
                channel=channel_id,
                thread_ts=thread_ts,
                text=response_text,
                blocks=build_feedback_blocks(),
            )
    except Exception as e:
        logger.exception(f"Failed to run Find Grants: {e}")
