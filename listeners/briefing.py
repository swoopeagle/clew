"""Proactive morning briefing: Clew watches the pipeline and reports daily
without being asked — deadlines coming due, prospects awaiting review,
submissions awaiting a decision, reports owed.

On-demand: DM Clew `clew briefing` (also opts that DM in for the daily run).
Scheduled: 09:00 America/Los_Angeles, for every org that opted in."""

import asyncio
from datetime import date, datetime, timedelta
from logging import Logger
from zoneinfo import ZoneInfo

from slack_sdk.web.async_client import AsyncWebClient

from storage import (
    get_prospects_grouped_by_stage,
    list_briefing_targets,
    list_open_tasks_by_org,
)

BRIEFING_PHRASES = {"clew briefing", "briefing", "/briefing"}
_BRIEFING_TZ = ZoneInfo("America/Los_Angeles")
_BRIEFING_HOUR = 9


def is_briefing_request(text: str) -> bool:
    return text.strip().lower() in BRIEFING_PHRASES


def _days_until(iso: str | None) -> int | None:
    # Calendar-day difference measured in America/Los_Angeles so the countdown
    # matches the web board (which also anchors to LA time). Using date.today()
    # here would read the SERVER's local date (UTC on Railway), landing a day
    # off from the board late in the US evening.
    try:
        today = datetime.now(_BRIEFING_TZ).date()
        return (date.fromisoformat(iso) - today).days
    except (ValueError, TypeError):
        return None


def _tasks_by_prospect(team_id: str) -> dict[int, list[dict]]:
    grouped: dict[int, list[dict]] = {}
    for task in list_open_tasks_by_org(team_id):
        grouped.setdefault(task["prospect_id"], []).append(task)
    return grouped


def build_briefing_blocks(team_id: str) -> list[dict]:
    grouped = get_prospects_grouped_by_stage(team_id)
    lines: list[str] = []

    for stage in ("approved", "applied"):
        for row in grouped.get(stage, []):
            days = _days_until(row.get("deadline_date"))
            if days is None:
                continue
            room = (
                f" — work it in <#{row['grant_channel_id']}>"
                if row.get("grant_channel_id")
                else ""
            )
            if days < 0:
                lines.append(
                    f":rotating_light: *{row['name']}* deadline passed ({row['deadline_date']}){room}"
                )
            elif days <= 7:
                lines.append(
                    f":alarm_clock: *{row['name']}* due in *{days} day{'s' if days != 1 else ''}*{room}"
                )

    qualified = len(grouped.get("qualified", []))
    if qualified:
        lines.append(
            f":mag: *{qualified} prospect{'s' if qualified != 1 else ''}* still awaiting your review"
        )

    submitted = len(grouped.get("submitted", []))
    if submitted:
        lines.append(
            f":mailbox_with_mail: *{submitted}* submitted and awaiting the funder's decision"
        )

    for row in grouped.get("awarded", []):
        if row.get("report_due_date") and not row.get("reported_at"):
            days = _days_until(row.get("report_due_date"))
            if days is not None and days <= 14:
                lines.append(
                    f":page_facing_up: *{row['name']}* report due {row['report_due_date']}"
                )

    # Open task rollup — one line per grant that has work in flight.
    for tasks in _tasks_by_prospect(team_id).values():
        unassigned = sum(1 for t in tasks if not t.get("assignee_user_id"))
        where = (
            f"<#{tasks[0]['grant_channel_id']}>"
            if tasks[0].get("grant_channel_id")
            else f"*{tasks[0]['prospect_name']}*"
        )
        note = f", *{unassigned} unassigned*" if unassigned else ""
        lines.append(
            f":jigsaw: {where} — {len(tasks)} task{'s' if len(tasks) != 1 else ''} open{note}"
        )

    if not lines:
        body = (
            "No fires today — no deadlines within a week, nothing waiting on "
            "you. A good morning to run *Find Grants*. :seedling:"
        )
    else:
        body = "\n".join(lines)

    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":sunrise: *Your morning grant briefing*\n{body}",
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": ":thread: Clew checks your pipeline every morning — ask `clew briefing` anytime.",
                }
            ],
        },
    ]


async def post_briefing(client: AsyncWebClient, channel_id: str, team_id: str) -> None:
    blocks = await asyncio.to_thread(build_briefing_blocks, team_id)
    await client.chat_postMessage(
        channel=channel_id, text="Your morning grant briefing", blocks=blocks
    )


def build_war_room_nudges(team_id: str) -> list[tuple[str, str]]:
    """(channel_id, message) pairs for war rooms that need a push today:
    a deadline within 3 days, or open tasks nobody owns. Channel mentions
    ping people — the DM briefing can't."""
    grouped = get_prospects_grouped_by_stage(team_id)
    tasks_by_prospect = _tasks_by_prospect(team_id)
    nudges: list[tuple[str, str]] = []

    for stage in ("approved", "applied"):
        for row in grouped.get(stage, []):
            channel = row.get("grant_channel_id")
            if not channel:
                continue
            parts: list[str] = []

            days = _days_until(row.get("deadline_date"))
            if days is not None and 0 <= days <= 3:
                parts.append(
                    f":alarm_clock: *{days} day{'s' if days != 1 else ''}* to the "
                    f"*{row['name']}* deadline ({row['deadline_date']})."
                )

            tasks = tasks_by_prospect.get(row["id"], [])
            unassigned = [t for t in tasks if not t.get("assignee_user_id")]
            assigned = [t for t in tasks if t.get("assignee_user_id")]
            if unassigned:
                items = "  ·  ".join(t["description"] for t in unassigned[:3])
                parts.append(
                    f":jigsaw: *{len(unassigned)} task{'s' if len(unassigned) != 1 else ''} "
                    f"still unassigned:* {items} — click :clipboard: *Tasks* to hand them off."
                )
            if parts and assigned:
                owners = "  ·  ".join(
                    f"<@{t['assignee_user_id']}> — {t['description']}"
                    for t in assigned[:3]
                )
                parts.append(f":black_square_button: Still open: {owners}")

            if parts:
                nudges.append((channel, "\n".join(parts)))

    return nudges


async def post_war_room_nudges(
    client: AsyncWebClient, team_id: str, logger: Logger | None = None
) -> None:
    nudges = await asyncio.to_thread(build_war_room_nudges, team_id)
    for channel_id, message in nudges:
        try:
            await client.chat_postMessage(
                channel=channel_id,
                text=message,
                blocks=[
                    {
                        "type": "section",
                        "text": {"type": "mrkdwn", "text": message},
                    }
                ],
            )
        except Exception as e:
            if logger:
                logger.warning(f"Nudge failed for {channel_id}: {e}")


def _seconds_until_next_briefing() -> float:
    now = datetime.now(_BRIEFING_TZ)
    target = now.replace(hour=_BRIEFING_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def briefing_loop(client: AsyncWebClient, logger: Logger) -> None:
    """Daily 9am PT briefing to every opted-in org. Never dies."""
    while True:
        try:
            await asyncio.sleep(_seconds_until_next_briefing())
            targets = await asyncio.to_thread(list_briefing_targets)
            for target in targets:
                try:
                    await post_briefing(
                        client, target["briefing_channel_id"], target["org_id"]
                    )
                    await post_war_room_nudges(client, target["org_id"], logger)
                except Exception as e:
                    logger.warning(f"Briefing failed for {target['org_id']}: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"Briefing loop error (continuing): {e}")
            await asyncio.sleep(300)
