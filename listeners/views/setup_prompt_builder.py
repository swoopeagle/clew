import json


def build_grant_nav_blocks(prospect: dict) -> list[dict]:
    """Navigation row for a grant war room: every button acts on THIS grant.
    Org-wide actions (Find Grants, Saved Grants, Edit Profile) stay out —
    those belong to the DM and general channels."""
    pid = str(prospect["id"])
    elements = [
        {
            "type": "button",
            "style": "primary",
            "text": {"type": "plain_text", "text": ":writing_hand: Draft Application"},
            "action_id": "clew_draft_application",
            "value": pid,
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": ":jigsaw: Designate Tasks"},
            "action_id": "clew_designate_tasks",
            "value": pid,
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": ":clipboard: Tasks"},
            "action_id": "clew_show_tasks",
            "value": pid,
        },
    ]

    grant_url = prospect.get("application_url")
    if not grant_url:
        try:
            sources = json.loads(prospect.get("fit_sources") or "[]")
            grant_url = sources[0] if sources else None
        except (ValueError, TypeError):
            grant_url = None
    if grant_url:
        elements.append(
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": ":globe_with_meridians: Grant Website",
                },
                "action_id": "clew_open_grant_link",
                "url": grant_url,
            }
        )

    if not prospect.get("deadline_date"):
        elements.append(
            {
                "type": "button",
                "text": {"type": "plain_text", "text": ":calendar: Set Deadline"},
                "action_id": "clew_set_deadline",
                "value": pid,
            }
        )

    return [
        {
            "type": "actions",
            "block_id": "clew_grant_nav_actions",
            "elements": elements,
        }
    ]


def build_chat_nav_blocks(team_id: str | None = None) -> list[dict]:
    """Compact navigation row under agent replies once a profile exists."""
    elements = [
        {
            "type": "button",
            "text": {"type": "plain_text", "text": ":mag: Find Grants"},
            "action_id": "clew_find_grants",
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": ":clipboard: Saved Grants"},
            "action_id": "clew_show_saved",
        },
        {
            "type": "button",
            "text": {"type": "plain_text", "text": "Edit Org Profile"},
            "action_id": "clew_open_org_profile",
        },
    ]
    if team_id:
        from webapi import board_link

        elements.append(
            {
                "type": "button",
                "text": {
                    "type": "plain_text",
                    "text": ":globe_with_meridians: Web Board",
                },
                "action_id": "clew_open_web_board",
                "url": board_link(team_id),
            }
        )
    return [
        {
            "type": "actions",
            "block_id": "clew_chat_nav_actions",
            "elements": elements,
        }
    ]


def build_profile_setup_blocks() -> list[dict]:
    """A chat-surface nudge with a one-click path to the org-profile modal.

    Message buttons carry a trigger_id, so the existing
    ``clew_open_org_profile`` action opens the same modal from here —
    no App Home navigation required.
    """
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    ":thread: *Let's set up your org profile* — it takes two "
                    "minutes, and Clew screens every grant against it. Or "
                    "skip the form: paste your website link here and I'll "
                    "draft it for you, or just tell me about your org."
                ),
            },
        },
        {
            "type": "actions",
            "block_id": "clew_chat_setup_actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Set Up Org Profile"},
                    "action_id": "clew_open_org_profile",
                }
            ],
        },
    ]
