from slack_sdk.web.async_client import AsyncWebClient


async def resolve_origin(
    client: AsyncWebClient, body: dict
) -> tuple[str, str | None]:
    """Where a button click should be answered: the channel (and thread)
    it was clicked in, falling back to the user's DM for surfaces without
    a channel (e.g. App Home)."""
    channel_id = (body.get("channel") or {}).get("id")
    if channel_id:
        container = body.get("container") or {}
        thread_ts = container.get("thread_ts") or container.get("message_ts")
        return channel_id, thread_ts
    dm = await client.conversations_open(users=body["user"]["id"])
    return dm["channel"]["id"], None
