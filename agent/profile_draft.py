"""One-shot LLM draft of the org profile from a website and/or user notes.

Powers the "✨ Draft with AI" button inside the org-profile modal. No tools,
no MCP — a single constrained completion that must return JSON."""

import json
import os
import re

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    TextBlock,
    query,
)

from agent.agent import DEFAULT_MODEL
from agent.tools.website import fetch_website_text

DRAFT_SYSTEM_PROMPT = """\
You draft a nonprofit organization's grant-screening profile from provided \
material. Return ONLY a JSON object — no prose, no code fences — with keys:
- "mission": string, 1-2 sentences in plain language
- "geography": string, where the org serves
- "program_areas": string, comma-separated focus areas
- "grant_size_min": integer or null
- "grant_size_max": integer or null
- "exclusions": string or null

Use only facts supported by the provided material. Use null for anything the \
material doesn't support — never invent grant sizes or geography.
"""


def _parse_draft_json(text: str) -> dict | None:
    """Pull the first JSON object out of a model reply, tolerating fences."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict) or not data.get("mission"):
        return None
    fields = {}
    for key in ("mission", "geography", "program_areas", "exclusions"):
        value = data.get(key)
        if value:
            fields[key] = str(value)
    for key in ("grant_size_min", "grant_size_max"):
        value = data.get(key)
        if isinstance(value, int):
            fields[key] = value
    return fields


async def draft_org_profile(website_url: str, notes: str) -> dict | None:
    """Draft profile fields from a website and/or free-text notes.

    Returns a dict shaped like an org_profile row (missing keys allowed),
    or None if drafting failed.
    """
    material = []
    if website_url.strip():
        material.append("WEBSITE CONTENT:\n" + await fetch_website_text(website_url))
    if notes.strip():
        material.append("NOTES FROM THE USER:\n" + notes.strip())
    if not material:
        return None

    options = ClaudeAgentOptions(
        system_prompt=DRAFT_SYSTEM_PROMPT,
        model=os.environ.get("CLEW_AGENT_MODEL", DEFAULT_MODEL),
        max_turns=1,
    )

    reply_parts: list[str] = []
    try:
        async for message in query(prompt="\n\n".join(material), options=options):
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        reply_parts.append(block.text)
    except Exception:
        return None

    return _parse_draft_json("".join(reply_parts))
