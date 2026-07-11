STAGE_LABELS = {
    "qualified": "Qualified — awaiting your review",
    "approved": "Approved — not yet applied",
    "applied": "Applied — drafting/in progress",
    "submitted": "Submitted — awaiting funder decision",
    "awarded": "Awarded \U0001f389",
    "declined": "Declined",
    "passed": "Passed",
}

# (stage, button label, action_id) — one forward transition per actionable stage.
ADVANCE_ACTIONS = {
    "approved": [("Mark Applied", "clew_mark_applied")],
    "applied": [("Mark Submitted", "clew_mark_submitted")],
    "submitted": [
        ("Mark Awarded", "clew_mark_awarded"),
        ("Mark Declined", "clew_mark_declined"),
    ],
}


def build_board_blocks(grouped: dict[str, list[dict]]) -> list[dict]:
    """Render the submission status board: every prospect grouped by stage,
    with a forward-transition button where one applies. This is the same
    `prospects` table as the shortlist cards — just a different view."""
    blocks: list[dict] = [
        {"type": "divider"},
        {"type": "header", "text": {"type": "plain_text", "text": "Grant Board"}},
    ]

    any_rows = False
    for stage in (
        "qualified",
        "approved",
        "applied",
        "submitted",
        "awarded",
        "declined",
        "passed",
    ):
        rows = grouped.get(stage, [])
        if not rows:
            continue
        any_rows = True
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{STAGE_LABELS[stage]}*"},
            }
        )

        for row in rows:
            line = f"• {row['name']}"
            if stage == "approved" and row.get("deadline_date"):
                line += f"  _(due {row['deadline_date']})_"
            if stage == "awarded" and row.get("report_due_date"):
                report_status = (
                    "reported"
                    if row.get("reported_at")
                    else f"report due {row['report_due_date']}"
                )
                line += f"  _({report_status})_"

            actions = ADVANCE_ACTIONS.get(stage, [])
            if actions:
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": line},
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": actions[0][0]},
                            "action_id": actions[0][1],
                            "value": str(row["id"]),
                        },
                    }
                )
                # Submitted has two possible transitions — add the second as its own row.
                if len(actions) > 1:
                    blocks.append(
                        {
                            "type": "section",
                            "text": {"type": "mrkdwn", "text": " "},
                            "accessory": {
                                "type": "button",
                                "text": {"type": "plain_text", "text": actions[1][0]},
                                "action_id": actions[1][1],
                                "value": str(row["id"]),
                                "style": "danger",
                            },
                        }
                    )
            elif (
                stage == "awarded"
                and not row.get("reported_at")
                and row.get("report_due_date")
            ):
                blocks.append(
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": line},
                        "accessory": {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Mark Reported"},
                            "action_id": "clew_mark_reported",
                            "value": str(row["id"]),
                        },
                    }
                )
            else:
                blocks.append(
                    {"type": "section", "text": {"type": "mrkdwn", "text": line}}
                )

    if not any_rows:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "No prospects yet — click *Find Grants* above to get started.",
                    }
                ],
            }
        )

    return blocks
