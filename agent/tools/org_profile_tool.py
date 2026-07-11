"""Conversational org-profile setup: lets the agent save the profile from
chat instead of requiring the user to find the App Home modal."""

import asyncio

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from storage import upsert_org_profile


@tool(
    name="save_org_profile",
    description=(
        "Save or update the organization's profile (mission, geography, program "
        "areas, grant-size range, exclusions) that Clew screens every grant "
        "against. Call this after the user has told you about their org and you "
        "have confirmed the summary back to them. Only include what the user "
        "actually said — never invent profile details."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "mission": {
                "type": "string",
                "description": "The org's mission, 1-2 sentences, in the user's words.",
            },
            "geography": {
                "type": "string",
                "description": 'Where the org serves, e.g. "Oakland / SF Bay Area" or "National".',
            },
            "program_areas": {
                "type": "string",
                "description": 'Comma-separated program areas, e.g. "youth education, STEM".',
            },
            "grant_size_min": {
                "type": "integer",
                "description": "Optional: smallest grant worth pursuing, in dollars.",
            },
            "grant_size_max": {
                "type": "integer",
                "description": "Optional: largest grant the org can manage, in dollars.",
            },
            "exclusions": {
                "type": "string",
                "description": "Optional: funders or sources to always skip.",
            },
        },
        "required": ["mission", "geography", "program_areas"],
    },
)
async def save_org_profile_tool(args):
    deps = agent_deps_var.get()

    await asyncio.to_thread(
        upsert_org_profile,
        org_id=deps.team_id,
        mission=args["mission"],
        geography=args["geography"],
        program_areas=args["program_areas"],
        grant_size_min=args.get("grant_size_min"),
        grant_size_max=args.get("grant_size_max"),
        exclusions=args.get("exclusions"),
    )

    # Refresh the user's App Home so the board/profile summary match.
    # Imported lazily to avoid the agent<->listeners import cycle.
    try:
        from listeners.views.home_refresh import publish_home

        await publish_home(deps.client, deps.user_id, deps.team_id, deps.user_token)
    except Exception:
        pass  # home refresh is best-effort; the profile itself is saved

    return {
        "content": [
            {
                "type": "text",
                "text": (
                    "Org profile saved. You can now search for grants that fit it."
                ),
            }
        ]
    }
