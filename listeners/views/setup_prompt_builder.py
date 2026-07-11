def build_chat_nav_blocks() -> list[dict]:
    """Compact navigation row under agent replies once a profile exists."""
    return [
        {
            "type": "actions",
            "block_id": "clew_chat_nav_actions",
            "elements": [
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
            ],
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
