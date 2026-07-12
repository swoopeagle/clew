"""Render an agent free-text reply for a button-triggered post.

Button handlers (Find Grants, Help me apply) post the agent's reply via
``chat_postMessage(text=...)``, which does NOT render markdown — so ``**bold**``,
``##`` headings and ``-`` bullets showed as literal characters. Wrapping the reply
in a Slack ``markdown`` block renders it properly. (DM/@mention replies already
render fine because they stream via ``say_stream(markdown_text=...)``.)"""

from listeners.views.feedback_builder import build_feedback_blocks

_MAX_MARKDOWN = 11900  # Slack 'markdown' block text cap is ~12000 chars


def build_agent_message_blocks(text: str) -> list:
    """A markdown block carrying the agent's reply, followed by feedback buttons."""
    body = text if len(text) <= _MAX_MARKDOWN else text[: _MAX_MARKDOWN - 1] + "…"
    return [{"type": "markdown", "text": body}, *build_feedback_blocks()]
