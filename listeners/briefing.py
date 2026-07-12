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

from storage import get_prospects_grouped_by_stage, list_briefing_targets

BRIEFING_PHRASES = {"clew briefing", "briefing", "/briefing"}
_BRIEFING_TZ = ZoneInfo("America/Los_Angeles")
_BRIEFING_HOUR = 9


def is_briefing_request(text: str) -> bool:
    return text.strip().lower() in BRIEFING_PHRASES


def _days_until(iso: str | None) -> int | None:
    try:
        return (date.fromisoformat(iso) - date.today()).days
    except (ValueError, TypeError):
        return None


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
                except Exception as e:
                    logger.warning(f"Briefing failed for {target['org_id']}: {e}")
        except asyncio.CancelledError:
            raise
        except Exception as e:
            logger.exception(f"Briefing loop error (continuing): {e}")
            await asyncio.sleep(300)
