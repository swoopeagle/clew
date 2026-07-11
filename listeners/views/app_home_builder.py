from listeners.views.board_builder import build_board_blocks


def build_app_home_view(
    org_profile: dict | None = None,
    board: dict[str, list[dict]] | None = None,
    install_url: str | None = None,
    is_connected: bool = False,
) -> dict:
    """Build the App Home Block Kit view: mission header, org profile status,
    Find Grants entry point, and the live grant board underneath.

    Args:
        org_profile: The org's saved profile row, or None if not set up yet.
        board: Prospects grouped by stage (see storage.get_prospects_grouped_by_stage).
        install_url: OAuth install URL. When provided, the user has not
            connected and will see a link to install (unlocks Real-Time Search).
        is_connected: When ``True``, the user is connected and the MCP
            status section shows as connected.
    """
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":thread: Clew — grant prospecting for small teams",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Clew finds real, sourced grant prospects for your org, screens them for fit, "
                    "and posts a shortlist for you to approve or pass on."
                ),
            },
        },
    ]

    if org_profile:
        summary_bits = [f"*Mission:* {org_profile.get('mission') or 'n/a'}"]
        if org_profile.get("program_areas"):
            summary_bits.append(f"*Program areas:* {org_profile['program_areas']}")
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "\n".join(summary_bits)},
            }
        )
        profile_button_text = "Edit Org Profile"
    else:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": ":large_yellow_circle: *No org profile set up yet.*",
                },
            }
        )
        profile_button_text = "Set Up Org Profile"

    blocks.append(
        {
            "type": "actions",
            "block_id": "clew_home_actions",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": profile_button_text},
                    "action_id": "clew_open_org_profile",
                },
                {
                    "type": "button",
                    "style": "primary",
                    "text": {"type": "plain_text", "text": "Find Grants"},
                    "action_id": "clew_find_grants",
                },
            ],
        }
    )

    blocks.append({"type": "divider"})

    if is_connected:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": "\U0001f7e2 Real-time workspace search connected (warm-path detection enabled).",
                    }
                ],
            }
        )
    elif install_url:
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"⚪ <{install_url}|Connect workspace search> to enable warm-path detection.",
                    }
                ],
            }
        )

    blocks.extend(build_board_blocks(board or {}))

    return {"type": "home", "blocks": blocks}
