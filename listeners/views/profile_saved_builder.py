from listeners.views.app_home_builder import _profile_summary_block


def build_profile_saved_blocks(profile: dict) -> list[dict]:
    """Confirmation card posted in chat after the org profile is saved,
    with the next action one click away."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": ":white_check_mark: *Org profile saved!* Here's what "
                "Clew will screen every grant against:",
            },
        },
        _profile_summary_block(profile),
        {
            "type": "actions",
            "block_id": "clew_profile_saved_actions",
            "elements": [
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Find Grants"},
                    "action_id": "clew_find_grants",
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit Org Profile"},
                    "action_id": "clew_open_org_profile",
                },
            ],
        },
    ]
