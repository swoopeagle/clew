"""Render a grant brief (agent-produced JSON) into a scannable Block Kit layout:
the two facts a grant lead scans for — amount and deadline — sit side by side at
the top, and the no-fabrication discipline shows as a Confirmed / Verify split
rather than buried prose. Falls back to a plain-text post if the JSON can't be
parsed, so a brief always lands."""

import json
import re


def parse_brief_json(text: str) -> dict | None:
    """Pull the JSON object out of the agent's reply (tolerant of code fences or
    stray prose around it). Returns None if there's nothing parseable."""
    if not text:
        return None
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        return None


def _bullets(items: list, limit: int) -> str:
    return "\n".join(f"• {str(i).strip()}" for i in items[:limit] if str(i).strip())


def build_grant_brief_blocks(data: dict, fallback_name: str = "") -> list[dict]:
    """Block Kit for a grant brief. Expects keys: funder, fit, amount, deadline,
    confirmed[], verify[], next_steps[], sources[{label,url}]. All optional —
    missing sections are simply omitted."""
    funder = (data.get("funder") or fallback_name or "Grant brief").strip()
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"📋 {funder}"[:150], "emoji": True},
        }
    ]

    if data.get("fit"):
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*Why it fits*\n{data['fit']}"},
            }
        )

    amount = str(data.get("amount") or "Verify on the funder's site").strip()
    deadline = str(data.get("deadline") or "Verify on the funder's site").strip()
    blocks.append(
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*:moneybag: Amount*\n{amount}"},
                {"type": "mrkdwn", "text": f"*:calendar: Deadline*\n{deadline}"},
            ],
        }
    )

    # The three things a grant lead actually needs in hand: where to apply,
    # what the rules are, who to email. Rendered only when research found them.
    def _url(key: str) -> str | None:
        v = data.get(key)
        return v.strip() if isinstance(v, str) and v.startswith("http") else None

    apply_url = _url("apply_url")
    criteria_url = _url("criteria_url")
    contact = data.get("contact")
    action_lines = []
    if apply_url:
        action_lines.append(f":link: *Apply here:* <{apply_url}|{apply_url}>")
    if criteria_url:
        action_lines.append(
            f":clipboard: *Criteria & guidelines:* <{criteria_url}|{criteria_url}>"
        )
    if isinstance(contact, str) and contact.strip():
        c = contact.strip()
        shown = f"<mailto:{c}|{c}>" if "@" in c and " " not in c else c
        action_lines.append(f":mailbox_with_mail: *Contact:* {shown}")
    if action_lines:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(action_lines)},
            }
        )

    if data.get("eligibility"):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*:busts_in_silhouette: Who's eligible*\n"
                        f"{_bullets(data['eligibility'], 5)}"
                    ),
                },
            }
        )
    analysis = data.get("eligibility_analysis")
    if isinstance(analysis, str) and analysis.strip():
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "*:robot_face: Are we eligible? — Clew's analysis*\n"
                        f"{analysis.strip()}"
                    ),
                },
            }
        )
    blocks.append({"type": "divider"})

    if data.get("confirmed"):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*:white_check_mark: Confirmed*\n{_bullets(data['confirmed'], 4)}",
                },
            }
        )
    if data.get("verify"):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*:warning: Verify before applying*\n{_bullets(data['verify'], 5)}",
                },
            }
        )
    if data.get("next_steps"):
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*:arrow_forward: Next steps*\n{_bullets(data['next_steps'], 3)}",
                },
            }
        )

    sources = data.get("sources") or []
    links = "  ·  ".join(
        f"<{s['url']}|{s.get('label') or 'source'}>"
        if isinstance(s, dict) and s.get("url")
        else str(s.get("label") if isinstance(s, dict) else s)
        for s in sources
    )
    if links:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f":paperclip: *Sources:* {links}"}
                ],
            }
        )

    return blocks
