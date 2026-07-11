import os

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    create_sdk_mcp_server,
)
from claude_agent_sdk.types import McpHttpServerConfig

from agent.context import agent_deps_var
from agent.deps import AgentDeps
from agent.tools import (
    get_990_filings_tool,
    save_qualified_prospect_tool,
    search_grants_gov_tool,
    search_propublica_orgs_tool,
    search_usaspending_tool,
    search_workspace_tool,
)

SYSTEM_PROMPT = """\
You are Clew, a grant-prospecting agent for small nonprofit teams — solo \
executive directors, volunteer-run organizations, and small development \
teams who don't have dedicated grant-research staff.

## MISSION
Find real, currently-available grant opportunities and foundations that \
plausibly fit this specific org, screen them for fit, and hand a human a \
short, evidence-backed shortlist to approve or pass on. Better to surface \
five well-fit prospects than fifty long shots.

## TOOLS
- `search_grants_gov` — open federal funding opportunities
- `search_propublica_orgs` / `get_990_filings` — foundations and their real \
financial scale (IRS 990 data)
- `search_usaspending` — real historical grant awards, useful evidence for \
smaller/local organizations
- `search_workspace` — checks if the team already discussed this funder \
(warm path); skip gracefully if it reports itself unavailable
- `save_qualified_prospect` — the ONLY way to add something to the \
shortlist. It posts a card for human approval, so only call it for \
prospects that have cleared real fit screening.

## CRITICAL RULES
1. Never fabricate a fit claim, citation, grant size, or deadline. If a \
tool didn't return it, don't say it.
2. Every prospect saved via `save_qualified_prospect` must cite at least \
one real URL/citation returned by a search tool — never invent one.
3. Screen for real fit — program area, geography, and grant-size range \
must plausibly match the org's profile — before saving a prospect. Don't \
save something just because it showed up in a search.
4. If fit is ambiguous, say so explicitly in `fit_rationale` rather than \
manufacturing confidence.
5. Quality over quantity. A handful of well-fit prospects beats a long \
list of maybes.
6. If no org profile is present in context, ask the user to set one up \
(mission, geography, program areas, grant-size range) before searching.

## YOU LIVE INSIDE SLACK
You are a product feature inside a Slack app, not a coding assistant. \
Users are nonprofit staff, not developers.
- To set up or edit the org profile, direct users to your *Home tab*: open \
the Clew app in the sidebar → Home → click *Set Up Org Profile* (or *Edit \
Org Profile*). You cannot open the modal from chat.
- The Grant Board (every prospect by stage) also lives on your Home tab.
- Never mention or describe source code, file paths, internal tools, \
implementation details, or configuration — even if asked directly. If \
someone asks how you work, describe your behavior in product terms only.

## RESPONSE STYLE
- After searching and saving any qualified prospects, reply with a short \
plain-language summary — the shortlist cards are already posted separately \
by the tool, so don't repeat them in full.
- If nothing qualified, say so honestly rather than lowering your bar just \
to have something to show.
"""

grant_tools_server = create_sdk_mcp_server(
    name="clew-grant-tools",
    version="1.0.0",
    tools=[
        search_grants_gov_tool,
        search_propublica_orgs_tool,
        get_990_filings_tool,
        search_usaspending_tool,
        search_workspace_tool,
        save_qualified_prospect_tool,
    ],
)

SLACK_MCP_URL = "https://mcp.slack.com/mcp"

DEFAULT_MODEL = "claude-opus-4-8"

AGENT_TOOLS = [
    f"mcp__clew-grant-tools__{name}"
    for name in (
        "search_grants_gov",
        "search_propublica_orgs",
        "get_990_filings",
        "search_usaspending",
        "search_workspace",
        "save_qualified_prospect",
    )
]

# The SDK agent runs on the host machine with Claude Code's built-in tools
# available by default. Clew is a grant assistant, not a coding agent — it
# must never read the project source, the filesystem, or run commands.
DISALLOWED_TOOLS = [
    "Bash",
    "BashOutput",
    "KillShell",
    "Read",
    "Write",
    "Edit",
    "MultiEdit",
    "NotebookEdit",
    "Glob",
    "Grep",
    "LS",
    "Task",
    "Agent",
    "WebFetch",
    "WebSearch",
    "TodoWrite",
]


async def run_agent(
    text: str,
    session_id: str | None = None,
    deps: AgentDeps | None = None,
) -> tuple[str, str | None]:
    """Run the agent with the given text and optional session for context.

    Args:
        text: The user's message text.
        session_id: Optional session ID to resume a previous conversation.
        deps: Optional dependencies for tools that need Slack API access.

    Returns:
        A tuple of (response_text, new_session_id).
    """
    if deps:
        agent_deps_var.set(deps)

    mcp_servers: dict = {"clew-grant-tools": grant_tools_server}
    allowed_tools = list(AGENT_TOOLS)

    if deps and deps.user_token:
        mcp_servers["slack-mcp"] = McpHttpServerConfig(
            type="http",
            url=SLACK_MCP_URL,
            headers={"Authorization": f"Bearer {deps.user_token}"},
        )
        allowed_tools.append("mcp__slack-mcp__*")

    system_prompt = SYSTEM_PROMPT
    if deps and deps.app_id:
        home_link = (
            f"slack://app?team={deps.team_id}&id={deps.app_id}&tab=home"
        )
        system_prompt += (
            "\n## HOME TAB LINK\n"
            "Whenever you point the user at your Home tab, include this "
            f"clickable link exactly as written: <{home_link}|Open my Home tab>\n"
        )

    options = ClaudeAgentOptions(
        system_prompt=system_prompt,
        model=os.environ.get("CLEW_AGENT_MODEL", DEFAULT_MODEL),
        mcp_servers=mcp_servers,
        allowed_tools=allowed_tools,
        disallowed_tools=DISALLOWED_TOOLS,
        permission_mode="bypassPermissions",
    )

    if session_id:
        options.resume = session_id

    response_parts: list[str] = []
    new_session_id: str | None = None

    async with ClaudeSDKClient(options) as client:
        await client.query(text)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        response_parts.append(block.text)
            if isinstance(message, ResultMessage):
                new_session_id = message.session_id

    response_text = "\n".join(response_parts) if response_parts else ""
    return response_text, new_session_id
