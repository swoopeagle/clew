"""Conversational task designation inside a grant war room: 'have @sam pull
our audited financials' becomes a tracked task, owned by a real person. The
prospect is resolved from the channel, so the agent never has to name it."""

import asyncio

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from storage import create_task, get_prospect_by_grant_channel


def _clean_user_id(raw: str | None) -> str | None:
    """Accept 'U0123ABC' or the raw mention form '<@U0123ABC>'."""
    if not raw:
        return None
    cleaned = raw.strip().lstrip("<@").split("|")[0].rstrip(">")
    if cleaned and cleaned[0] in ("U", "W") and cleaned.isalnum():
        return cleaned
    return None


@tool(
    name="assign_grant_task",
    description=(
        "Designate an action item for the grant this war-room channel is "
        "dedicated to — e.g. gathering financial statements, drafting a budget, "
        "collecting board documents. Optionally assign it to a teammate: pass "
        "their Slack user ID exactly as it appeared in a <@U…> mention in the "
        "conversation — NEVER invent or guess a user ID. Only works inside a "
        "grant war-room channel."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "The task, as one short imperative sentence.",
            },
            "assignee_user_id": {
                "type": "string",
                "description": (
                    "Optional Slack user ID (U…) from a mention in the "
                    "conversation. Omit when nobody was named."
                ),
            },
        },
        "required": ["description"],
    },
)
async def assign_grant_task_tool(args):
    deps = agent_deps_var.get()

    prospect = await asyncio.to_thread(
        get_prospect_by_grant_channel, deps.channel_id
    )
    if not prospect:
        return {
            "content": [
                {
                    "type": "text",
                    "text": (
                        "REJECTED: task designation only works inside a grant "
                        "war-room channel. Tell the user to ask in the grant's "
                        "own #grant-… channel."
                    ),
                }
            ]
        }

    assignee = _clean_user_id(args.get("assignee_user_id"))
    task_id = await asyncio.to_thread(
        create_task,
        org_id=deps.team_id,
        prospect_id=prospect["id"],
        description=args["description"].strip(),
        assignee_user_id=assignee,
    )

    # Post the designation in-channel — the <@user> mention is the notification.
    try:
        who = f" — <@{assignee}>" if assignee else " — unassigned"
        await deps.client.chat_postMessage(
            channel=deps.channel_id,
            text=f":jigsaw: Task designated: *{args['description'].strip()}*{who}",
        )
    except Exception:
        pass  # the task row exists either way; the board shows it

    owner = f"assigned to <@{assignee}>" if assignee else "unassigned"
    return {
        "content": [
            {
                "type": "text",
                "text": (
                    f"Task #{task_id} created ({owner}). The 📋 Tasks button in "
                    "this channel shows the full list."
                ),
            }
        ]
    }
