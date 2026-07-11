"""Real-Time Search API tool: checks the live workspace for prior mentions of a funder.

Requires a user token (only available when the app is installed via OAuth,
see app_oauth.py). Degrades gracefully when unavailable — the agent is told
to skip the warm-path check rather than fabricate a "no prior mentions" claim.
"""

from claude_agent_sdk import tool
from slack_sdk.web.async_client import AsyncWebClient

from agent.context import agent_deps_var


@tool(
    name="search_workspace",
    description=(
        "Search this Slack workspace's message history for prior mentions of a funder or "
        "grant name, to detect a 'warm path' (a board member or staffer already discussed "
        "them) before qualifying a prospect. Only available when the app is installed via "
        "OAuth with a user token — if unavailable, say so and skip the warm-path note rather "
        "than guessing."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Funder or grant name to search for.",
            },
        },
        "required": ["query"],
    },
)
async def search_workspace_tool(args):
    deps = agent_deps_var.get()

    if not deps.user_token:
        return {
            "content": [
                {
                    "type": "text",
                    "text": "Workspace search unavailable (no user token — app not installed via OAuth). Skip the warm-path check for this prospect.",
                }
            ]
        }

    user_client = AsyncWebClient(token=deps.user_token)
    resp = await user_client.search_messages(query=args["query"], count=5)
    matches = resp.get("messages", {}).get("matches", [])

    if not matches:
        return {
            "content": [
                {
                    "type": "text",
                    "text": f"No prior workspace mentions of '{args['query']}' found.",
                }
            ]
        }

    results = [
        {
            "channel": m.get("channel", {}).get("name"),
            "user": m.get("username"),
            "text": m.get("text"),
            "permalink": m.get("permalink"),
        }
        for m in matches
    ]
    return {
        "content": [
            {
                "type": "text",
                "text": f"Found {len(results)} prior mention(s): {results}",
            }
        ]
    }
