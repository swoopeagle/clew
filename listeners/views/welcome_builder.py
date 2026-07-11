from listeners.views.setup_prompt_builder import build_profile_setup_blocks


def build_welcome_blocks() -> list[dict]:
    """First-contact welcome: what Clew does, the trust promise, and the
    one-click setup path."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    ":thread: *Hi, I'm Clew — grant prospecting for small "
                    "nonprofit teams.*\nI find real, currently-available "
                    "grants and foundations that fit your org, screen each "
                    "one for fit, and hand you a short, evidence-backed "
                    "shortlist to approve or pass on."
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        ":lock: Every prospect comes with real citations — "
                        "I never invent a funder, grant size, or deadline."
                    ),
                }
            ],
        },
        *build_profile_setup_blocks(),
    ]
