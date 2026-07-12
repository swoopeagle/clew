from dataclasses import dataclass, field

from slack_sdk.web.async_client import AsyncWebClient


@dataclass
class AgentDeps:
    client: AsyncWebClient
    user_id: str
    channel_id: str
    thread_ts: str
    message_ts: str
    user_token: str | None = None
    team_id: str = "default"
    app_id: str | None = None
    # Every citable URL the search tools actually returned during this run.
    # save_qualified_prospect checks fit_sources against this set, so the
    # trust boundary rejects a well-formed-but-never-returned citation (a
    # hallucinated grants.gov detail link), not just an off-domain one.
    emitted_urls: set[str] = field(default_factory=set)
