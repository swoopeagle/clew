"""Citation provenance: the machinery behind Clew's enforced trust boundary.

The search tools call ``register_emitted_urls`` with every citable URL they
actually returned in this run; ``save_qualified_prospect`` then checks each
``fit_sources`` entry against that set. That turns "cite a real source" from a
host-name check into a provenance check — a citation must be a URL a tool
genuinely emitted, not merely a well-formed URL on an allowed domain.
"""

from urllib.parse import urlparse

from agent.context import agent_deps_var

# The only hosts our search tools emit. A citation on any other host didn't
# come from a tool result, so it can't back a qualified prospect.
ALLOWED_CITATION_HOSTS = ("grants.gov", "propublica.org", "usaspending.gov")


def normalize_citation_url(url: object) -> str | None:
    """Canonicalize a URL for provenance comparison, or None if it isn't a
    valid http(s) URL on an allowed host. Scheme- and trailing-slash-
    insensitive so a verbatim citation still matches what a tool emitted."""
    if not isinstance(url, str):
        return None
    parsed = urlparse(url.strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    host = parsed.netloc.lower().split(":")[0]
    if not any(host == h or host.endswith("." + h) for h in ALLOWED_CITATION_HOSTS):
        return None
    return f"{host}{parsed.path.rstrip('/')}"


def register_emitted_urls(urls) -> None:
    """Record the URLs a search tool just returned, so the save gate can later
    confirm a citation actually came from a tool. No-op when there's no agent
    deps in context (e.g. a tool unit-tested in isolation)."""
    try:
        deps = agent_deps_var.get()
    except LookupError:
        return
    for url in urls:
        normalized = normalize_citation_url(url)
        if normalized:
            deps.emitted_urls.add(normalized)
