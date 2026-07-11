from urllib.parse import urlparse


def _source_label(url: str) -> str:
    netloc = urlparse(url).netloc
    return netloc.removeprefix("www.") or "source"


def build_prospect_card_blocks(prospect: dict, fit_sources: list[str]) -> list[dict]:
    """Build the Block Kit shortlist card for one qualified prospect.

    Shows the fit rationale with every source cited as a link, the grant
    size/program/geography at a glance, and Approve/Pass buttons that are
    the human-approval gate made visible as UI.
    """
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": prospect["name"][:150]},
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Why it fits*\n{prospect['fit_rationale']}",
            },
        },
    ]

    meta_fields = []
    if prospect.get("program_area"):
        meta_fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:dart: Program area*\n{prospect['program_area']}",
            }
        )
    if prospect.get("geography"):
        meta_fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:round_pushpin: Geography*\n{prospect['geography']}",
            }
        )
    if prospect.get("grant_size"):
        meta_fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:moneybag: Grant size*\n{prospect['grant_size']}",
            }
        )
    if meta_fields:
        blocks.append({"type": "section", "fields": meta_fields})

    if fit_sources:
        links = "\n".join(
            f"• <{s}|{_source_label(s)}>" if s.startswith("http") else f"• {s}"
            for s in fit_sources
        )
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn", "text": f":paperclip: *Cited evidence*\n{links}"}
                ],
            }
        )

    if prospect.get("warm_path_note"):
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":yarn: *Warm path:* {prospect['warm_path_note']}",
                    }
                ],
            }
        )

    blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "actions",
            "block_id": "clew_prospect_actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "action_id": "clew_approve_prospect",
                    "value": str(prospect["id"]),
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Pass"},
                    "action_id": "clew_pass_prospect",
                    "value": str(prospect["id"]),
                },
            ],
        }
    )

    return blocks


def build_decided_card_blocks(prospect: dict, decision_label: str) -> list[dict]:
    """Re-render a prospect card after Approve/Pass, with buttons replaced by a status line."""
    blocks: list[dict] = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": prospect["name"][:150]},
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": prospect["fit_rationale"]},
        },
        {
            "type": "context",
            "elements": [{"type": "mrkdwn", "text": decision_label}],
        },
    ]
    return blocks
