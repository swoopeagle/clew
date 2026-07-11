import asyncio
import logging
import os

from dotenv import load_dotenv
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.web.async_client import AsyncWebClient

from listeners import register_listeners
from storage import init_db
from webapi import start_web_api

load_dotenv(dotenv_path=".env", override=False)

logging.basicConfig(level=logging.DEBUG)

init_db()

app = AsyncApp(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    client=AsyncWebClient(
        base_url=os.environ.get("SLACK_API_URL", "https://slack.com/api"),
        token=os.environ.get("SLACK_BOT_TOKEN"),
    ),
)

register_listeners(app)


async def main():
    await start_web_api()  # read-only board API for the Clew web app
    handler = AsyncSocketModeHandler(app, os.environ.get("SLACK_APP_TOKEN"))
    await handler.start_async()


if __name__ == "__main__":
    asyncio.run(main())
