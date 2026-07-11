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
            "text": {"type": "mrkdwn", "text": prospect["fit_rationale"]},
        },
    ]

    meta_bits = []
    if prospect.get("program_area"):
        meta_bits.append(f"*Program area:* {prospect['program_area']}")
    if prospect.get("geography"):
        meta_bits.append(f"*Geography:* {prospect['geography']}")
    if prospect.get("grant_size"):
        meta_bits.append(f"*Grant size:* {prospect['grant_size']}")
    if meta_bits:
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(meta_bits)},
            }
        )

    if fit_sources:
        links = "\n".join(
            f"• <{s}|Source>" if s.startswith("http") else f"• {s}" for s in fit_sources
        )
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"*Cited evidence:*\n{links}"}],
            }
        )

    if prospect.get("warm_path_note"):
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f":large_yellow_circle: *Warm path:* {prospect['warm_path_note']}",
                    }
                ],
            }
        )

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
