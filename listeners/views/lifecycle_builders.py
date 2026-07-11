import json

DEADLINE_CALLBACK_ID = "clew_deadline_modal"
AWARDED_CALLBACK_ID = "clew_awarded_modal"
DECLINED_CALLBACK_ID = "clew_declined_modal"


def build_deadline_modal(prospect_id: int) -> dict:
    return {
        "type": "modal",
        "callback_id": DEADLINE_CALLBACK_ID,
        "private_metadata": json.dumps({"prospect_id": prospect_id}),
        "title": {"type": "plain_text", "text": "Set Deadline"},
        "submit": {"type": "plain_text", "text": "Save"},
        "close": {"type": "plain_text", "text": "Skip"},
        "blocks": [
            {
                "type": "input",
                "block_id": "deadline_date",
                "optional": True,
                "label": {"type": "plain_text", "text": "📅 Application deadline"},
                "hint": {
                    "type": "plain_text",
                    "text": "Clew will flag it on your board when it's a week out.",
                },
                "element": {"type": "datepicker", "action_id": "value"},
            }
        ],
    }


def _retro_block(warm_path_hint: str | None) -> list[dict]:
    blocks = []
    if warm_path_hint:
        blocks.append(
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": warm_path_hint}],
            }
        )
    blocks.append(
        {
            "type": "input",
            "block_id": "retro_note",
            "optional": True,
            "label": {
                "type": "plain_text",
                "text": "Why did we win/lose? What should we remember next time?",
            },
            "element": {
                "type": "plain_text_input",
                "action_id": "value",
                "multiline": True,
            },
        }
    )
    return blocks


def build_awarded_modal(prospect_id: int, warm_path_hint: str | None = None) -> dict:
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "\U0001f389 *Congratulations!* When's the first report due (if any)?",
            },
        },
        {
            "type": "input",
            "block_id": "report_due_date",
            "optional": True,
            "label": {"type": "plain_text", "text": "Report due date"},
            "element": {"type": "datepicker", "action_id": "value"},
        },
        *_retro_block(warm_path_hint),
    ]
    return {
        "type": "modal",
        "callback_id": AWARDED_CALLBACK_ID,
        "private_metadata": json.dumps({"prospect_id": prospect_id}),
        "title": {"type": "plain_text", "text": "Awarded"},
        "submit": {"type": "plain_text", "text": "Save"},
        "close": {"type": "plain_text", "text": "Skip"},
        "blocks": blocks,
    }


def build_declined_modal(prospect_id: int, warm_path_hint: str | None = None) -> dict:
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Not this time — capture the lesson so the next "
                    "application is stronger."
                ),
            },
        },
        *_retro_block(warm_path_hint),
    ]
    return {
        "type": "modal",
        "callback_id": DECLINED_CALLBACK_ID,
        "private_metadata": json.dumps({"prospect_id": prospect_id}),
        "title": {"type": "plain_text", "text": "Org Learning"},
        "submit": {"type": "plain_text", "text": "Save"},
        "close": {"type": "plain_text", "text": "Skip"},
        "blocks": blocks,
    }
