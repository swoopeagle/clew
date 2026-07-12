"""The task board for one grant: every action item as a row whose control
matches its state — unassigned tasks carry an "Assign to…" people picker,
assigned tasks a ✅ Done button, finished tasks a strikethrough. The board is
always rebuilt from the database, so any posted copy self-heals on touch."""

import json
import re


def parse_tasks_json(text: str) -> list[str] | None:
    """Pull a JSON array of task descriptions out of the agent's reply
    (tolerant of code fences or prose around it). Returns None if there's
    nothing parseable."""
    if not text:
        return None
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        return None
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
    if not isinstance(data, list):
        return None
    tasks = [str(t).strip() for t in data if str(t).strip()]
    return tasks or None


def _task_block(task: dict) -> dict:
    desc = task["description"]
    if task["status"] == "done":
        who = f" — <@{task['assignee_user_id']}>" if task.get("assignee_user_id") else ""
        return {
            "type": "section",
            "block_id": f"clew_task_{task['id']}",
            "text": {"type": "mrkdwn", "text": f":white_check_mark: ~{desc}~{who}"},
        }
    if task.get("assignee_user_id"):
        return {
            "type": "section",
            "block_id": f"clew_task_{task['id']}",
            "text": {
                "type": "mrkdwn",
                "text": f":black_square_button: {desc} — <@{task['assignee_user_id']}>",
            },
            "accessory": {
                "type": "button",
                "action_id": "clew_task_done",
                "text": {"type": "plain_text", "text": "✅ Done"},
                "value": str(task["id"]),
            },
        }
    return {
        "type": "section",
        "block_id": f"clew_task_{task['id']}",
        "text": {"type": "mrkdwn", "text": f":black_square_button: {desc}"},
        "accessory": {
            "type": "users_select",
            "action_id": "clew_assign_task",
            "placeholder": {"type": "plain_text", "text": "Assign to…"},
        },
    }


def build_task_board_blocks(prospect_name: str, tasks: list[dict]) -> list[dict]:
    open_count = sum(1 for t in tasks if t["status"] == "open")
    blocks: list[dict] = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":jigsaw: *Tasks — {prospect_name}*",
            },
        }
    ]
    if not tasks:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "🧶 No tasks yet — click *🧩 Designate Tasks* and I'll "
                        "propose them from the application requirements."
                    ),
                },
            }
        )
        return blocks

    blocks.extend(_task_block(t) for t in tasks)
    blocks.append(
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        f"{open_count} open · {len(tasks) - open_count} done — "
                        "pick a person on a task to hand it off."
                    ),
                }
            ],
        }
    )
    return blocks
