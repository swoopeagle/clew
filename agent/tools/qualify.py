"""The tool that turns an LLM fit judgment into a persisted, human-reviewable card.

This is the trust boundary of Clew: the agent may only add a prospect to the
shortlist by calling this tool, and every call requires a rationale plus the
literal source URLs/citations backing it. Nothing reaches a human as a
qualified prospect without a citation attached.
"""

import asyncio
from datetime import date, datetime

from claude_agent_sdk import tool

from agent.context import agent_deps_var
from agent.tools.citations import normalize_citation_url
from storage import find_prospect_by_identity, insert_prospect, update_prospect


def _accepted_citations(fit_sources, emitted_urls: set[str]) -> list[str]:
    """Filter fit_sources down to citations that clear the trust boundary: a
    valid http(s) URL on a source domain we query AND — when the run actually
    returned any citable URLs — one the search tools genuinely emitted. The
    provenance check is what stops a well-formed but never-returned link (a
    hallucinated grants.gov detail URL) from backing a prospect; it falls back
    to the domain check alone if nothing was emitted, so a legitimate save
    can't be blocked just because provenance tracking has no data."""
    accepted = []
    for url in fit_sources or []:
        normalized = normalize_citation_url(url)
        if normalized is None:
            continue  # not a valid URL on a source domain we query
        if emitted_urls and normalized not in emitted_urls:
            continue  # well-formed, but no search tool actually returned it
        accepted.append(url)
    return accepted


def _iso_date(raw: str | None) -> str | None:
    """Normalize a deadline to ISO YYYY-MM-DD, or None if it isn't a date.
    grants.gov emits MM/DD/YYYY; the board/briefing due-soon checks parse
    with date.fromisoformat, so anything unparseable is dropped rather than
    stored dirty."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        return date.fromisoformat(raw).isoformat()
    except ValueError:
        pass
    try:
        return datetime.strptime(raw, "%m/%d/%Y").date().isoformat()
    except ValueError:
        return None


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
            "deadline_date": {
                "type": "string",
                "description": "Application deadline as YYYY-MM-DD when the source states one (convert grants.gov close_date, e.g. 01/31/2026 -> 2026-01-31). Omit if unknown — never guess.",
            },
            "application_url": {
                "type": "string",
                "description": "The URL where the org actually applies or reads the full opportunity (e.g. the grants.gov detail url from the search result). Must be a URL a search tool returned.",
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
    # shortlisted with a real citation a search tool actually returned. Drop
    # anything that isn't such a URL; refuse if none remain.
    citations = _accepted_citations(args.get("fit_sources"), deps.emitted_urls)
    if not citations:
        return _rejection(
            "REJECTED: save_qualified_prospect needs at least one real citation URL "
            "returned by a search tool (a grants.gov, propublica.org, or "
            "usaspending.gov link from an actual tool result). Do not shortlist a "
            "prospect you cannot cite — re-run the search tools and cite a result "
            "they returned, or skip this prospect."
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

    # application_url passes through the same trust gate as citations — a
    # hallucinated link must never become the card's Apply button.
    application_url = args.get("application_url")
    if application_url and not _accepted_citations(
        [application_url], deps.emitted_urls
    ):
        application_url = None

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
        deadline_date=_iso_date(args.get("deadline_date")),
        application_url=application_url,
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

    # Keep the App Home board current — Slack never refreshes it on its own,
    # so without this a fresh Find Grants run leaves "No prospects yet" on
    # the dashboard until someone clicks Refresh. Best-effort.
    try:
        from listeners.views.home_refresh import publish_home

        await publish_home(deps.client, deps.user_id, deps.team_id, deps.user_token)
    except Exception:
        pass

    return {
        "content": [
            {
                "type": "text",
                "text": f"Saved and posted prospect #{prospect_id} ({args['name']}) for human approval.",
            }
        ]
    }
