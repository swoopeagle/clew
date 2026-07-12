"""Human-readable live-progress labels for the agent's tool calls."""

TOOL_STATUS = {
    "search_grants_gov": "🔍 Searching Grants.gov…",
    "search_propublica_orgs": "📚 Checking ProPublica 990s…",
    "get_990_filings": "📚 Reading foundation 990 filings…",
    "search_usaspending": "🏛️ Scanning USAspending awards…",
    "get_org_award_history": "🏛️ Pulling your federal award history…",
    "search_workspace": "🧵 Checking your workspace for warm paths…",
    "fetch_org_website": "🌐 Reading your website…",
    "fetch_webpage": "🌐 Reading the funder's site…",
    "save_org_profile": "💾 Saving your org profile…",
    "save_qualified_prospect": "✅ Posting a qualified prospect…",
    "assign_grant_task": "🧩 Designating a task…",
}


def status_for(tool_name: str) -> str | None:
    """Map a (possibly MCP-namespaced) tool name to a status label."""
    return TOOL_STATUS.get(tool_name.rsplit("__", 1)[-1])
