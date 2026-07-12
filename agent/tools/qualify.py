"""The tool that turns an LLM fit judgment into a persisted, human-reviewable card.

This is the trust boundary of Clew: the agent may only add a prospect to the
shortlist by calling this tool, and every call requires a rationale plus the
literal source URLs/citations backing it. Nothing reaches a human as a
qualified prospect without a citation attached.
"""

import asyncio
from urllib.parse import urlparse

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from storage import find_prospect_by_identity, insert_prospect, update_prospect

# The only hosts our search tools actually emit. A citation on any other host
# didn't come from a tool result — so it can't back a qualified prospect.
_ALLOWED_CITATION_HOSTS = ("grants.gov", "propublica.org", "usaspending.gov")


def _valid_citation(url: object) -> bool:
    if not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    host = parsed.netloc.lower().split(":")[0]
    return any(host == h or host.endswith("." + h) for h in _ALLOWED_CITATION_HOSTS)


def _rejection(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


@tool(
    name="save_qualified_prospect",
    description=(
        "Save a grant/funder prospect that has cleared fit screening and post it to the "
        "team's shortlist for human approval. Only call this for prospects you have real "
        "screened evidence for — every fit_sources entry must be an actual URL or citation "
        "returned by one of the search tools, never invented. If fit is uncertain, say so "
        "in fit_rationale rather than fabricating confidence."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the funder or grant opportunity.",
            },
            "source": {
                "type": "string",
                "enum": ["grants_gov", "propublica", "usaspending"],
                "description": "Which tool this prospect came from.",
            },
            "source_ref": {
                "type": "string",
                "description": "The source's own ID (opportunity id, EIN, award id).",
            },
            "program_area": {
                "type": "string",
                "description": "Program area this prospect funds.",
            },
            "geography": {
                "type": "string",
                "description": "Geography this prospect funds.",
            },
            "grant_size": {
                "type": "string",
                "description": "Typical or stated grant size/range.",
            },
            "fit_rationale": {
                "type": "string",
                "description": "Why this is (or might be) a fit for the org, in 1-3 sentences. Flag uncertainty explicitly rather than asserting confidence you don't have.",
            },
            "fit_sources": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 1,
                "description": "Real URLs/citations from search tool results backing the rationale. Never invent one.",
            },
            "warm_path_note": {
                "type": "string",
                "description": "Optional: if workspace search found a prior mention of this funder, summarize it here.",
            },
        },
        "required": ["name", "source", "fit_rationale", "fit_sources"],
    },
)
async def save_qualified_prospect_tool(args):
    # Imported lazily inside the handler to avoid an import cycle: the agent
    # layer builds a Slack view here, but the listeners layer imports the
    # agent. Deferring keeps import order independent of entry point.
    from listeners.views.prospect_card_builder import build_prospect_card_blocks

    deps = agent_deps_var.get()

    # Trust boundary, enforced (not just requested): a prospect can only be
    # shortlisted with a real citation from a search tool. Drop anything that
    # isn't a URL on a source domain we actually query; refuse if none remain.
    citations = [s for s in (args.get("fit_sources") or []) if _valid_citation(s)]
    if not citations:
        return _rejection(
            "REJECTED: save_qualified_prospect needs at least one real citation URL "
            "from a search tool (a grants.gov, propublica.org, or usaspending.gov "
            "link). Do not shortlist a prospect you cannot cite — re-run the search "
            "tools and cite an actual result, or skip this prospect."
        )

    # Don't shortlist the same funder twice (e.g. Find Grants run more than once).
    existing = await asyncio.to_thread(
        find_prospect_by_identity, deps.team_id, args["name"], args.get("source_ref")
    )
    if existing:
        return _rejection(
            f"'{args['name']}' is already on the shortlist (prospect #{existing['id']}, "
            f"stage: {existing['stage']}). Not adding a duplicate."
        )

    prospect_id = await asyncio.to_thread(
        insert_prospect,
        org_id=deps.team_id,
        name=args["name"],
        source=args["source"],
        source_ref=args.get("source_ref"),
        program_area=args.get("program_area"),
        geography=args.get("geography"),
        grant_size=args.get("grant_size"),
        fit_rationale=args["fit_rationale"],
        fit_sources=citations,
        warm_path_note=args.get("warm_path_note"),
    )

    prospect = {
        "id": prospect_id,
        "name": args["name"],
        **{
            k: args.get(k)
            for k in (
                "program_area",
                "geography",
                "grant_size",
                "fit_rationale",
                "warm_path_note",
            )
        },
    }
    blocks = build_prospect_card_blocks(prospect, citations)

    posted = await deps.client.chat_postMessage(
        channel=deps.channel_id,
        thread_ts=deps.thread_ts,
        text=f"Qualified prospect: {args['name']}",
        blocks=blocks,
    )

    await asyncio.to_thread(
        update_prospect,
        prospect_id,
        slack_channel_id=deps.channel_id,
        slack_message_ts=posted["ts"],
    )

    return {
        "content": [
            {
                "type": "text",
                "text": f"Saved and posted prospect #{prospect_id} ({args['name']}) for human approval.",
            }
        ]
    }
