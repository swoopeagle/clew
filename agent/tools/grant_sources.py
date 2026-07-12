"""Tools that query free, keyless grant-data APIs.

Every tool returns a compact JSON blob (as text) that the agent is instructed
to cite verbatim when qualifying a prospect — never paraphrase a fact that
isn't actually in one of these payloads.
"""

import asyncio
import json
from datetime import date, timedelta

import aiohttp
from claude_agent_sdk import tool

GRANTS_GOV_SEARCH_URL = "https://api.grants.gov/v1/api/search2"
PROPUBLICA_SEARCH_URL = "https://projects.propublica.org/nonprofits/api/v2/search.json"
PROPUBLICA_ORG_URL = (
    "https://projects.propublica.org/nonprofits/api/v2/organizations/{ein}.json"
)
USASPENDING_SEARCH_URL = "https://api.usaspending.gov/api/v2/search/spending_by_award/"

# One slow government API must never freeze a live search. Bound every call.
_TIMEOUT = aiohttp.ClientTimeout(total=15)
_NETWORK_ERRORS = (aiohttp.ClientError, asyncio.TimeoutError, ValueError)


def _text_result(payload: dict) -> dict:
    return {"content": [{"type": "text", "text": json.dumps(payload, indent=2)}]}


@tool(
    name="search_grants_gov",
    description=(
        "Search Grants.gov for open federal funding opportunities. Returns real, "
        "currently posted opportunities with a citable URL for each — cite the "
        "'id', 'title', 'agency', and 'url' fields verbatim when referencing a result."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Search keywords, e.g. 'youth education'.",
            },
            "agency": {
                "type": "string",
                "description": "Optional agency code filter, e.g. 'HHS-NIH11'.",
            },
        },
        "required": ["keywords"],
    },
)
async def search_grants_gov_tool(args):
    body = {
        "keyword": args["keywords"],
        "rows": 10,
        "oppStatuses": "posted",
    }
    if args.get("agency"):
        body["agencies"] = args["agency"]

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.post(GRANTS_GOV_SEARCH_URL, json=body) as resp:
                data = await resp.json(content_type=None)
    except _NETWORK_ERRORS as e:
        return _text_result(
            {"source": "grants_gov", "error": f"Grants.gov unavailable: {e}"}
        )

    hits = data.get("data", {}).get("oppHits", [])
    results = [
        {
            "id": hit.get("id"),
            "number": hit.get("number"),
            "title": hit.get("title"),
            "agency": hit.get("agency"),
            "open_date": hit.get("openDate"),
            "close_date": hit.get("closeDate"),
            "cfda_list": hit.get("cfdaList"),
            "url": f"https://www.grants.gov/search-results-detail/{hit.get('id')}",
        }
        for hit in hits
    ]
    return _text_result(
        {
            "source": "grants_gov",
            "hit_count": data.get("data", {}).get("hitCount", 0),
            "results": results,
        }
    )


@tool(
    name="search_propublica_orgs",
    description=(
        "Search ProPublica's Nonprofit Explorer (IRS 990 data) for foundations/nonprofits by "
        "name and optional state. Returns each org's EIN and a citable profile URL — cite "
        "'ein', 'name', and 'url' verbatim. Use get_990_filings for a specific org's financials."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Organization name or partial name to search.",
            },
            "state": {
                "type": "string",
                "description": "Optional two-letter US state code.",
            },
        },
        "required": ["name"],
    },
)
async def search_propublica_orgs_tool(args):
    params = {"q": args["name"]}
    if args.get("state"):
        params["state[id]"] = args["state"]

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.get(PROPUBLICA_SEARCH_URL, params=params) as resp:
                data = await resp.json(content_type=None)
    except _NETWORK_ERRORS as e:
        return _text_result(
            {"source": "propublica", "error": f"ProPublica search unavailable: {e}"}
        )

    orgs = data.get("organizations", [])
    results = [
        {
            "ein": org.get("ein"),
            "name": org.get("name"),
            "city": org.get("city"),
            "state": org.get("state"),
            "ntee_code": org.get("ntee_code"),
            "url": f"https://projects.propublica.org/nonprofits/organizations/{org.get('ein')}",
        }
        for org in orgs
    ]
    return _text_result(
        {
            "source": "propublica",
            "total_results": data.get("total_results", 0),
            "results": results,
        }
    )


@tool(
    name="get_990_filings",
    description=(
        "Get IRS 990 filing history (revenue, expenses, assets by tax year) for a specific "
        "organization by EIN, from ProPublica's Nonprofit Explorer. Use this to check whether "
        "a foundation's giving scale plausibly matches the org's target grant size. Cite the "
        "'tax_prd_yr', 'totrevenue', and 'url' fields verbatim."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "ein": {
                "type": "string",
                "description": "The organization's EIN (with or without the dash).",
            },
        },
        "required": ["ein"],
    },
)
async def get_990_filings_tool(args):
    ein = args["ein"].replace("-", "")
    url = PROPUBLICA_ORG_URL.format(ein=ein)

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return _text_result(
                        {
                            "source": "propublica",
                            "error": f"No filings found for EIN {ein}",
                        }
                    )
                data = await resp.json(content_type=None)
    except _NETWORK_ERRORS as e:
        return _text_result(
            {"source": "propublica", "error": f"ProPublica filings unavailable: {e}"}
        )

    org = data.get("organization", {})
    filings = data.get("filings_with_data", [])[:5]
    results = [
        {
            "tax_prd_yr": f.get("tax_prd_yr"),
            "totrevenue": f.get("totrevenue"),
            "totfuncexpns": f.get("totfuncexpns"),
            "totassetsend": f.get("totassetsend"),
        }
        for f in filings
    ]
    return _text_result(
        {
            "source": "propublica",
            "ein": ein,
            "name": org.get("name"),
            "subsection_code": org.get("subsection_code"),
            "url": f"https://projects.propublica.org/nonprofits/organizations/{ein}",
            "recent_filings": results,
        }
    )


@tool(
    name="search_usaspending",
    description=(
        "Search USAspending.gov for real, historical grant AWARDS (not open opportunities) — "
        "useful for evidence that smaller/local organizations actually win grants in a given "
        "state or program area. Returns a citable award URL — cite 'award_id', 'recipient_name', "
        "'award_amount', and 'url' verbatim."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "keywords": {
                "type": "string",
                "description": "Search keywords, e.g. 'youth education'.",
            },
            "state": {
                "type": "string",
                "description": "Optional two-letter US recipient state code.",
            },
        },
        "required": ["keywords"],
    },
)
async def search_usaspending_tool(args):
    filters = {
        "award_type_codes": ["02", "03", "04", "05"],
        "time_period": [
            {
                "start_date": (date.today() - timedelta(days=730)).isoformat(),
                "end_date": date.today().isoformat(),
            }
        ],
        "keywords": [args["keywords"]],
    }
    if args.get("state"):
        filters["recipient_locations"] = [{"country": "USA", "state": args["state"]}]

    body = {
        "filters": filters,
        "fields": [
            "Award ID",
            "Recipient Name",
            "Award Amount",
            "Awarding Agency",
            "Start Date",
            "End Date",
            "Description",
        ],
        "page": 1,
        "limit": 10,
        "sort": "Award Amount",
        "order": "desc",
    }

    try:
        async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
            async with session.post(USASPENDING_SEARCH_URL, json=body) as resp:
                data = await resp.json(content_type=None)
    except _NETWORK_ERRORS as e:
        return _text_result(
            {"source": "usaspending", "error": f"USAspending unavailable: {e}"}
        )

    results = [
        {
            "award_id": r.get("Award ID"),
            "recipient_name": r.get("Recipient Name"),
            "award_amount": r.get("Award Amount"),
            "awarding_agency": r.get("Awarding Agency"),
            "start_date": r.get("Start Date"),
            "end_date": r.get("End Date"),
            "url": f"https://www.usaspending.gov/award/{r.get('generated_internal_id')}",
        }
        for r in data.get("results", [])
    ]
    return _text_result({"source": "usaspending", "results": results})
