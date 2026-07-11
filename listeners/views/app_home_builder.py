from listeners.views.board_builder import build_board_blocks

_PIPELINE_SEGMENTS = [
    ("qualified", "{n} to review"),
    ("approved", "{n} approved"),
    ("applied", "{n} in progress"),
    ("submitted", "{n} awaiting decision"),
    ("awarded", ":trophy: {n} awarded"),
]

_ONBOARDING_STEPS = (
    "*Get set up in three steps:*\n"
    "1️⃣  *Tell Clew about your org* — mission, geography, and grant size "
    "(2 minutes).\n"
    "2️⃣  *Click Find Grants* — Clew researches real funders and cites every "
    "source.\n"
    "3️⃣  *Approve or pass* — approved grants land on your board and Clew "
    "tracks them to award."
)


def _truncate(s: str, limit: int = 150) -> str:
    return s if len(s) <= limit else s[: limit - 1] + "…"


def _grant_range(org_profile: dict) -> str | None:
    lo, hi = org_profile.get("grant_size_min"), org_profile.get("grant_size_max")
    if lo is None and hi is None:
        return None
    if lo is not None and hi is not None:
        return f"${lo:,} – ${hi:,}"
    return f"${lo:,}+" if lo is not None else f"up to ${hi:,}"


def _profile_summary_block(org_profile: dict) -> dict:
    fields = []
    if org_profile.get("geography"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:round_pushpin: Geography*\n{_truncate(org_profile['geography'])}",
            }
        )
    if org_profile.get("program_areas"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:dart: Program areas*\n{_truncate(org_profile['program_areas'])}",
            }
        )
    grant_range = _grant_range(org_profile)
    if grant_range:
        fields.append(
            {"type": "mrkdwn", "text": f"*:moneybag: Grant range*\n{grant_range}"}
        )
    if org_profile.get("exclusions"):
        fields.append(
            {
                "type": "mrkdwn",
                "text": f"*:no_entry_sign: Exclusions*\n{_truncate(org_profile['exclusions'])}",
            }
        )

    block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*Your organization*\n_{_truncate(org_profile.get('mission') or 'n/a', 300)}_",
        },
    }
    if fields:
        block["fields"] = fields
    return block


def _pipeline_summary(board: dict[str, list[dict]]) -> str | None:
    segments = []
    for stage, template in _PIPELINE_SEGMENTS:
        n = len(board.get(stage, []))
        if n:
            segments.append(template.format(n=n))
    if not segments:
        return None
    return ":bar_chart: *Pipeline:*  " + "  ·  ".join(segments)


def build_app_home_view(
    org_profile: dict | None = None,
    board: dict[str, list[dict]] | None = None,
    install_url: str | None = None,
    is_connected: bool = False,
) -> dict:
    """Build the App Home Block Kit view: hero, org profile summary (or
    onboarding steps), action buttons, pipeline summary, and the grant board.

    Args:
        org_profile: The org's saved profile row, or None if not set up yet.
        board: Prospects grouped by stage (see storage.get_prospects_grouped_by_stage).
        install_url: OAuth install URL. When provided, the user has not
            connected and will see a link to install (unlocks Real-Time Search).
        is_connected: When ``True``, the user is connected and the MCP
            status section shows as connected.
    """
    board = board or {}
    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": ":thread: Clew — find your next grant",
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Clew finds *real, sourced grant prospects* for your org, "
                    "screens them for fit, and posts a shortlist for you to "
                    "approve or pass on."
                ),
            },
        },
    ]

    if org_profile:
        blocks.append(_profile_summary_block(org_profile))
        profile_button_text = "Edit Org Profile"
        primary_action = "clew_find_grants"
    else:
        blocks.append(
            {"type": "section", "text": {"type": "mrkdwn", "text": _ONBOARDING_STEPS}}
        )
        profile_button_text = "Set Up Org Profile"
        primary_action = "clew_open_org_profile"

    profile_button = {
        "type": "button",
        "text": {"type": "plain_text", "text": profile_button_text},
        "action_id": "clew_open_org_profile",
    }
    find_button = {
        "type": "button",
        "text": {"type": "plain_text", "text": "Find Grants"},
        "action_id": "clew_find_grants",
    }
    for button in (profile_button, find_button):
        if button["action_id"] == primary_action:
            button["style"] = "primary"

    blocks.append(
        {
            "type": "actions",
            "block_id": "clew_home_actions",
            "elements": [
                profile_button,
                find_button,
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": ":arrows_counterclockwise: Refresh",
                    },
                    "action_id": "clew_refresh_home",
                },
            ],
        }
    )

    blocks.append({"type": "divider"})

    pipeline = _pipeline_summary(board)
    if pipeline:
        blocks.append(
            {"type": "context", "elements": [{"type": "mrkdwn", "text": pipeline}]}
        )

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

    blocks.extend(build_board_blocks(board))

    blocks.append({"type": "divider"})
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        ":thread: Every prospect cited — Clew never fabricates "
                        "a funder."
                    ),
                }
            ],
        }
    )

    return {"type": "home", "blocks": blocks}
