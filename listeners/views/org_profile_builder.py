ORG_PROFILE_CALLBACK_ID = "clew_org_profile_modal"

CURATED_PROGRAM_AREAS = [
    "Education & Youth Development",
    "Health & Mental Health",
    "Housing & Homelessness",
    "Food Security & Hunger",
    "Arts & Culture",
    "Environment & Climate",
    "Workforce Development",
    "Economic Development",
    "Human Services",
    "Civil Rights & Advocacy",
    "Immigration & Refugee Services",
    "Seniors & Aging",
    "Disability Services",
    "Animal Welfare",
]


def _option(label: str) -> dict:
    return {"text": {"type": "plain_text", "text": label}, "value": label}


def split_program_areas(saved: str | None) -> tuple[list[str], list[str]]:
    """Split a saved comma-joined program_areas string into (curated matches,
    leftovers). Matching is case-insensitive; matches are returned as the
    curated spelling so initial_options byte-match the options list."""
    parts = [p.strip() for p in (saved or "").split(",") if p.strip()]
    by_lower = {c.lower(): c for c in CURATED_PROGRAM_AREAS}
    matched = [by_lower[p.lower()] for p in parts if p.lower() in by_lower]
    leftover = [p for p in parts if p.lower() not in by_lower]
    return matched, leftover


def build_org_profile_modal(existing: dict | None = None) -> dict:
    existing = existing or {}

    def _val(key, default=""):
        v = existing.get(key)
        return str(v) if v not in (None, "") else default

    def _text_input(key, placeholder=None, multiline=False):
        element = {"type": "plain_text_input", "action_id": "value"}
        if multiline:
            element["multiline"] = True
        # Slack rejects empty initial_value on some element types; only
        # include the key when there is a saved value.
        if _val(key):
            element["initial_value"] = _val(key)
        if placeholder:
            element["placeholder"] = {"type": "plain_text", "text": placeholder}
        return element

    def _number_input(key, placeholder):
        element = {
            "type": "number_input",
            "action_id": "value",
            "is_decimal_allowed": False,
            "min_value": "0",
            "placeholder": {"type": "plain_text", "text": placeholder},
        }
        if _val(key):
            element["initial_value"] = _val(key)
        return element

    matched_areas, other_areas = split_program_areas(existing.get("program_areas"))

    areas_select = {
        "type": "multi_static_select",
        "action_id": "value",
        "placeholder": {"type": "plain_text", "text": "Pick all that apply"},
        "options": [_option(a) for a in CURATED_PROGRAM_AREAS],
    }
    if matched_areas:
        areas_select["initial_options"] = [_option(a) for a in matched_areas]

    areas_other = {
        "type": "plain_text_input",
        "action_id": "value",
        "placeholder": {
            "type": "plain_text",
            "text": "e.g. digital literacy, financial coaching",
        },
    }
    if other_areas:
        areas_other["initial_value"] = ", ".join(other_areas)

    # Offer AI drafting only on first-time setup — the edit modal stays clean.
    ai_draft_blocks = []
    if not _val("mission"):
        ai_draft_blocks = [
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            ":sparkles: *Let AI draft this for you* — add your "
                            "website and/or a few notes, then click Draft. "
                            "You'll review everything before saving."
                        ),
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "ai_website",
                "optional": True,
                "label": {"type": "plain_text", "text": "Your website"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "placeholder": {"type": "plain_text", "text": "yourorg.org"},
                },
            },
            {
                "type": "input",
                "block_id": "ai_notes",
                "optional": True,
                "label": {"type": "plain_text", "text": "Anything else?"},
                "hint": {
                    "type": "plain_text",
                    "text": "Things your site doesn't say — grant-size range, exclusions…",
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "multiline": True,
                },
            },
            {
                "type": "actions",
                "block_id": "clew_ai_draft_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": ":sparkles: Draft with AI",
                        },
                        "action_id": "clew_ai_draft_profile",
                    }
                ],
            },
            {"type": "divider"},
        ]

    return {
        "type": "modal",
        "callback_id": ORG_PROFILE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Your Org Profile"},
        "submit": {"type": "plain_text", "text": "Save Profile"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            *ai_draft_blocks,
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            ":thread: *Clew screens every grant against this "
                            "profile.* Two minutes here means better matches "
                            "forever — you can edit it anytime."
                        ),
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "mission",
                "label": {"type": "plain_text", "text": "What's your mission?"},
                "hint": {
                    "type": "plain_text",
                    "text": "One or two sentences is plenty.",
                },
                "element": _text_input(
                    "mission",
                    placeholder=(
                        "e.g. We help Bay Area youth launch careers in technology."
                    ),
                    multiline=True,
                ),
            },
            {
                "type": "input",
                "block_id": "geography",
                "label": {"type": "plain_text", "text": "Where do you serve?"},
                "hint": {
                    "type": "plain_text",
                    "text": 'City, region, state, or "National".',
                },
                "element": _text_input(
                    "geography", placeholder="e.g. San Francisco Bay Area"
                ),
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": ":dart: *What you do*"}],
            },
            {
                "type": "input",
                "block_id": "program_areas",
                "optional": True,
                "label": {"type": "plain_text", "text": "Program areas"},
                "element": areas_select,
            },
            {
                "type": "input",
                "block_id": "program_areas_other",
                "optional": True,
                "label": {"type": "plain_text", "text": "Other program areas"},
                "hint": {
                    "type": "plain_text",
                    "text": "Comma-separated — anything not in the list above.",
                },
                "element": areas_other,
            },
            {"type": "divider"},
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": (
                            ":moneybag: *Grant size sweet spot* — leave blank "
                            "to see grants of every size."
                        ),
                    }
                ],
            },
            {
                "type": "input",
                "block_id": "grant_size_min",
                "optional": True,
                "label": {
                    "type": "plain_text",
                    "text": "Smallest grant worth pursuing ($)",
                },
                "element": _number_input("grant_size_min", "5000"),
            },
            {
                "type": "input",
                "block_id": "grant_size_max",
                "optional": True,
                "label": {
                    "type": "plain_text",
                    "text": "Largest grant you can manage ($)",
                },
                "element": _number_input("grant_size_max", "50000"),
            },
            {
                "type": "input",
                "block_id": "exclusions",
                "optional": True,
                "label": {"type": "plain_text", "text": "Anything to avoid?"},
                "hint": {
                    "type": "plain_text",
                    "text": "Funders or sources Clew should always skip.",
                },
                "element": _text_input(
                    "exclusions",
                    placeholder=(
                        "e.g. no faith-based funders; avoid the XYZ Foundation"
                    ),
                    multiline=True,
                ),
            },
        ],
    }
