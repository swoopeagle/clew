"""Fetch the org's own website so the agent can draft the profile from it."""

import re
from html.parser import HTMLParser
from urllib.parse import urlparse

import aiohttp

from claude_agent_sdk import tool

MAX_BYTES = 200_000
MAX_TEXT_CHARS = 6_000
TIMEOUT = aiohttp.ClientTimeout(total=10)

_SKIP_TAGS = {"script", "style", "noscript", "svg", "head"}


class _TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts: list[str] = []
        self.title = ""
        self.meta_description = ""
        self._skip_depth = 0
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        if tag in _SKIP_TAGS and tag != "head":
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            attrs = dict(attrs)
            if attrs.get("name", "").lower() == "description":
                self.meta_description = attrs.get("content", "")

    def handle_endtag(self, tag):
        if tag in _SKIP_TAGS and tag != "head" and self._skip_depth:
            self._skip_depth -= 1
        if tag == "title":
            self._in_title = False

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        elif not self._skip_depth and data.strip():
            self.parts.append(data.strip())


def _extract_text(html: str) -> tuple[str, str, str]:
    parser = _TextExtractor()
    try:
        parser.feed(html)
    except Exception:
        pass
    text = re.sub(r"\s+", " ", " ".join(parser.parts))
    return parser.title.strip(), parser.meta_description.strip(), text


@tool(
    name="fetch_org_website",
    description=(
        "Fetch the organization's own website and return its text content, so "
        "you can draft the org profile from it. Only call this with a URL the "
        "user themselves shared. Always show the drafted profile to the user "
        "for confirmation before calling save_org_profile."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The website URL the user shared (http/https).",
            }
        },
        "required": ["url"],
    },
)
async def fetch_org_website_tool(args):
    url = args["url"].strip()
    if not urlparse(url).scheme:
        url = "https://" + url
    if urlparse(url).scheme not in ("http", "https"):
        return {
            "content": [{"type": "text", "text": "Only http(s) URLs can be fetched."}]
        }

    try:
        async with aiohttp.ClientSession(timeout=TIMEOUT) as session:
            async with session.get(
                url, headers={"User-Agent": "Clew grant assistant"}
            ) as resp:
                if resp.status != 200:
                    return {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Could not fetch {url} (HTTP {resp.status}).",
                            }
                        ]
                    }
                raw = await resp.content.read(MAX_BYTES)
                html = raw.decode(resp.charset or "utf-8", errors="replace")
    except Exception as e:
        return {"content": [{"type": "text", "text": f"Could not fetch {url} ({e})."}]}

    title, description, text = _extract_text(html)
    summary_bits = []
    if title:
        summary_bits.append(f"TITLE: {title}")
    if description:
        summary_bits.append(f"META DESCRIPTION: {description}")
    summary_bits.append(f"PAGE TEXT:\n{text[:MAX_TEXT_CHARS]}")

    return {"content": [{"type": "text", "text": "\n".join(summary_bits)}]}
