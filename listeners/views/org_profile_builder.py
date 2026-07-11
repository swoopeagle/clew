ORG_PROFILE_CALLBACK_ID = "clew_org_profile_modal"


def build_org_profile_modal(existing: dict | None = None) -> dict:
    existing = existing or {}

    def _val(key, default=""):
        v = existing.get(key)
        return str(v) if v not in (None, "") else default

    return {
        "type": "modal",
        "callback_id": ORG_PROFILE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "Org Profile"},
        "submit": {"type": "plain_text", "text": "Save"},
        "close": {"type": "plain_text", "text": "Cancel"},
        "blocks": [
            {
                "type": "input",
                "block_id": "mission",
                "label": {"type": "plain_text", "text": "Mission"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "multiline": True,
                    "initial_value": _val("mission"),
                },
            },
            {
                "type": "input",
                "block_id": "geography",
                "label": {"type": "plain_text", "text": "Geography served"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "initial_value": _val("geography"),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. San Francisco Bay Area",
                    },
                },
            },
            {
                "type": "input",
                "block_id": "program_areas",
                "label": {"type": "plain_text", "text": "Program areas"},
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "initial_value": _val("program_areas"),
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g. youth education, workforce development",
                    },
                },
            },
            {
                "type": "input",
                "block_id": "grant_size_min",
                "label": {"type": "plain_text", "text": "Minimum grant size ($)"},
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "initial_value": _val("grant_size_min"),
                    "placeholder": {"type": "plain_text", "text": "e.g. 5000"},
                },
            },
            {
                "type": "input",
                "block_id": "grant_size_max",
                "label": {"type": "plain_text", "text": "Maximum grant size ($)"},
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "initial_value": _val("grant_size_max"),
                    "placeholder": {"type": "plain_text", "text": "e.g. 50000"},
                },
            },
            {
                "type": "input",
                "block_id": "exclusions",
                "label": {
                    "type": "plain_text",
                    "text": "Exclusions (funders/sources to avoid)",
                },
                "optional": True,
                "element": {
                    "type": "plain_text_input",
                    "action_id": "value",
                    "multiline": True,
                    "initial_value": _val("exclusions"),
                },
            },
        ],
    }
