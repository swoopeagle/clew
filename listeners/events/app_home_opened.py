from logging import Logger

from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from listeners.views.home_refresh import publish_home

SUGGESTED_PROMPTS = [
    {"title": "Find grants for us", "message": "Find grants for us"},
    {"title": "Set up our org profile", "message": "Help me set up our org profile"},
]


async def handle_app_home_opened(
    client: AsyncWebClient, event: dict, context: AsyncBoltContext, logger: Logger
):
    """Handle app_home_opened events.

    Under agent_view, this event fires for both the Home tab and the Messages
    tab (the agent DM). Branch on ``event["tab"]``:
        * ``"messages"`` -- pin suggested prompts to the top of the DM.
        * ``"home"``     -- publish the App Home Block Kit view (org profile
          status, Find Grants entry point, and the live grant board).
    """
    try:
        if event.get("tab") == "messages":
            await client.assistant_threads_setSuggestedPrompts(
                channel_id=event["channel"],
                title="How can I help you today?",
                prompts=SUGGESTED_PROMPTS,
            )
            return

        team_id = context.team_id or "default"
        await publish_home(client, context.user_id, team_id, context.user_token)
    except Exception as e:
        logger.exception(f"Failed to handle app_home_opened: {e}")
