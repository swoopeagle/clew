"""The enforced trust boundary: a prospect can only be shortlisted with a
citation a search tool actually returned."""

from unittest.mock import AsyncMock

import pytest

from agent.context import agent_deps_var
from agent.deps import AgentDeps
from agent.tools.citations import (
    normalize_citation_url,
    register_emitted_urls,
)
from agent.tools.qualify import save_qualified_prospect_tool
from storage import get_prospects_grouped_by_stage

save_prospect = save_qualified_prospect_tool.handler


def test_normalize_accepts_source_domains_and_rejects_others():
    # Real source hosts (and their subdomains) normalize to host+path.
    assert (
        normalize_citation_url("https://www.grants.gov/search-results-detail/1")
        == "www.grants.gov/search-results-detail/1"
    )
    assert (
        normalize_citation_url(
            "https://projects.propublica.org/nonprofits/organizations/1/"
        )
        == "projects.propublica.org/nonprofits/organizations/1"
    )
    # Trailing slash is insensitive, so a verbatim citation still matches.
    assert normalize_citation_url(
        "https://www.usaspending.gov/award/X/"
    ) == normalize_citation_url("https://www.usaspending.gov/award/X")

    # Off-domain, look-alike, and non-URL inputs are all rejected.
    assert normalize_citation_url("https://grants.gov.evil.com/x") is None
    assert normalize_citation_url("https://example.com/x") is None
    assert normalize_citation_url("not a url") is None
    assert normalize_citation_url(None) is None


def test_register_emitted_urls_is_noop_without_deps():
    # Called from a tool unit-tested in isolation (no agent run in context).
    register_emitted_urls(["https://www.grants.gov/search-results-detail/1"])


def _deps() -> AgentDeps:
    return AgentDeps(
        client=AsyncMock(),
        user_id="U1",
        channel_id="C1",
        thread_ts="1",
        message_ts="1",
        team_id="T1",
    )


@pytest.mark.asyncio
async def test_save_rejects_uncited_prospect():
    agent_deps_var.set(_deps())
    result = await save_prospect(
        {
            "name": "Ghost Foundation",
            "source": "propublica",
            "fit_rationale": "Looks like a fit.",
            "fit_sources": ["https://example.com/made-up"],
        }
    )
    assert "REJECTED" in result["content"][0]["text"]
    assert get_prospects_grouped_by_stage("T1")["qualified"] == []


@pytest.mark.asyncio
async def test_save_rejects_well_formed_but_never_returned_citation():
    """A hallucinated grants.gov detail URL is well-formed and on an allowed
    host, but no tool returned it — provenance must reject it."""
    deps = _deps()
    deps.emitted_urls.add("www.grants.gov/search-results-detail/111")  # what we found
    agent_deps_var.set(deps)

    result = await save_prospect(
        {
            "name": "Invented Opportunity",
            "source": "grants_gov",
            "fit_rationale": "Cites a real-looking but never-returned URL.",
            "fit_sources": ["https://www.grants.gov/search-results-detail/999999"],
        }
    )
    assert "REJECTED" in result["content"][0]["text"]
    assert get_prospects_grouped_by_stage("T1")["qualified"] == []


@pytest.mark.asyncio
async def test_save_accepts_a_returned_citation():
    deps = _deps()
    deps.client.chat_postMessage = AsyncMock(return_value={"ts": "123.456"})
    deps.emitted_urls.add("www.grants.gov/search-results-detail/111")
    agent_deps_var.set(deps)

    result = await save_prospect(
        {
            "name": "Real Opportunity",
            "source": "grants_gov",
            "fit_rationale": "Cites a URL a search tool actually returned.",
            # Verbatim, with a trailing slash — provenance is slash-insensitive.
            "fit_sources": ["https://www.grants.gov/search-results-detail/111/"],
        }
    )
    assert "Saved and posted" in result["content"][0]["text"]
    qualified = get_prospects_grouped_by_stage("T1")["qualified"]
    assert len(qualified) == 1
    assert qualified[0]["name"] == "Real Opportunity"
    deps.client.chat_postMessage.assert_awaited_once()
