from datetime import date

STAGE_LABELS = {
    "qualified": ":mag: Qualified — awaiting your review",
    "approved": ":white_check_mark: Approved — up next",
    "applied": ":writing_hand: Applied — in progress",
    "submitted": ":mailbox_with_mail: Submitted — awaiting the funder",
    "awarded": ":trophy: Awarded \U0001f389",
    "declined": ":x: Declined",
    "passed": ":fast_forward: Passed",
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


def _due_soon(iso: str | None) -> bool:
    try:
        return 0 <= (date.fromisoformat(iso) - date.today()).days <= 7
    except (ValueError, TypeError):
        return False


def _row_name(row: dict, workspace_url: str | None) -> str:
    """The prospect name, linked to its original shortlist card when we
    know where that message lives."""
    channel, ts = row.get("slack_channel_id"), row.get("slack_message_ts")
    if workspace_url and channel and ts:
        permalink = f"{workspace_url.rstrip('/')}/archives/{channel}/p{str(ts).replace('.', '')}"
        return f"<{permalink}|{row['name']}>"
    return row["name"]


def build_board_blocks(
    grouped: dict[str, list[dict]], workspace_url: str | None = None
) -> list[dict]:
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
            line = f"• {_row_name(row, workspace_url)}"
            if row.get("grant_channel_id"):
                line += f"  <#{row['grant_channel_id']}>"
            if stage in ("approved", "applied") and row.get("deadline_date"):
                alarm = "⏰ " if _due_soon(row["deadline_date"]) else ""
                line += f"  {alarm}_(due {row['deadline_date']})_"
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
                        "text": (
                            ":yarn: No prospects yet — click *Find Grants* "
                            "above and Clew will pull the first thread."
                        ),
                    }
                ],
            }
        )

    return blocks
