"""Task designation for a grant war room: Clew proposes the action items from
the application requirements, and the team hands each one to a person with a
people picker — no forms, no separate tracker. Every interaction rebuilds the
board from the database, so a stale copy heals itself on touch."""

import asyncio
import json
from logging import Logger

from slack_bolt import Ack
from slack_bolt.context.async_context import AsyncBoltContext
from slack_sdk.web.async_client import AsyncWebClient

from agent import run_agent
from agent.org_context import prepend_org_profile
from listeners.actions.origin import resolve_origin
from listeners.views.task_board_builder import (
    build_task_board_blocks,
    parse_tasks_json,
)
from storage import (
    complete_task,
    create_task,
    get_prospect,
    get_task,
    list_tasks,
    set_task_assignee,
)

DESIGNATE_TASKS_PROMPT = """\
Propose the concrete action items our team must complete to apply for this \
approved grant — gathering documents (financials, 501(c)(3) letter, board \
list), drafting narrative sections, budget work, and submission logistics. \
Ground them in the prospect below and our org profile. Output ONLY a JSON \
array of 3-6 short imperative task descriptions (each under 12 words) and \
nothing else — no prose, no code fence, and do NOT call any tools.

PROSPECT:
{prospect_json}
"""


async def _post_board(
    client: AsyncWebClient, channel: str, prospect: dict
) -> None:
    tasks = await asyncio.to_thread(list_tasks, prospect["id"])
    await client.chat_postMessage(
        channel=channel,
        text=f"Tasks for {prospect['name']}",
        blocks=build_task_board_blocks(prospect["name"], tasks),
    )


async def handle_designate_tasks(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        prospect = await asyncio.to_thread(get_prospect, prospect_id)
        if not prospect:
            return
        channel, _ = await resolve_origin(client, body)

        # Idempotent: a re-click (or double-click) shows the current board
        # instead of generating a duplicate task list.
        existing = await asyncio.to_thread(list_tasks, prospect_id)
        if existing:
            await _post_board(client, channel, prospect)
            return

        placeholder = await client.chat_postMessage(
            channel=channel,
            text=f":jigsaw: Working out the action items for {prospect['name']}…",
        )

        prospect_json = json.dumps(
            {
                k: prospect.get(k)
                for k in (
                    "name",
                    "source",
                    "program_area",
                    "grant_size",
                    "fit_rationale",
                    "deadline_date",
                    "application_url",
                )
            },
            default=str,
        )
        team_id = context.team_id or "default"
        prompt_text = await prepend_org_profile(
            DESIGNATE_TASKS_PROMPT.format(prospect_json=prospect_json), team_id
        )
        response_text, _ = await run_agent(prompt_text)

        descriptions = parse_tasks_json(response_text)
        if not descriptions:
            await client.chat_update(
                channel=channel,
                ts=placeholder["ts"],
                text=(
                    ":warning: I couldn't put the task list together just now — "
                    "click 🧩 Designate Tasks again, or tell me the tasks and "
                    "I'll track them."
                ),
            )
            return

        for desc in descriptions[:6]:
            await asyncio.to_thread(
                create_task,
                org_id=team_id,
                prospect_id=prospect_id,
                description=desc,
            )

        tasks = await asyncio.to_thread(list_tasks, prospect_id)
        await client.chat_update(
            channel=channel,
            ts=placeholder["ts"],
            text=f"Tasks for {prospect['name']}",
            blocks=build_task_board_blocks(prospect["name"], tasks),
        )
    except Exception as e:
        logger.exception(f"Failed to designate tasks: {e}")


async def handle_show_tasks(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        prospect_id = int(body["actions"][0]["value"])
        prospect = await asyncio.to_thread(get_prospect, prospect_id)
        if not prospect:
            return
        channel, _ = await resolve_origin(client, body)
        await _post_board(client, channel, prospect)
    except Exception as e:
        logger.exception(f"Failed to show tasks: {e}")


async def _rebuild_board(client: AsyncWebClient, body: dict, task: dict) -> None:
    """chat_update the clicked board message from the database."""
    prospect = await asyncio.to_thread(get_prospect, task["prospect_id"])
    if not prospect:
        return
    tasks = await asyncio.to_thread(list_tasks, task["prospect_id"])
    container = body.get("container") or {}
    if container.get("channel_id") and container.get("message_ts"):
        await client.chat_update(
            channel=container["channel_id"],
            ts=container["message_ts"],
            text=f"Tasks for {prospect['name']}",
            blocks=build_task_board_blocks(prospect["name"], tasks),
        )


async def handle_assign_task(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        action = body["actions"][0]
        task_id = int(action["block_id"].rsplit("_", 1)[-1])
        assignee = action["selected_user"]

        await asyncio.to_thread(set_task_assignee, task_id, assignee)
        task = await asyncio.to_thread(get_task, task_id)
        if not task:
            return
        await _rebuild_board(client, body, task)

        # A chat_update mention doesn't notify — a threaded reply does.
        container = body.get("container") or {}
        if container.get("channel_id") and container.get("message_ts"):
            await client.chat_postMessage(
                channel=container["channel_id"],
                thread_ts=container["message_ts"],
                text=(
                    f":jigsaw: <@{assignee}> — you're on *{task['description']}* "
                    f"(handed off by <@{body['user']['id']}>)."
                ),
            )
    except Exception as e:
        logger.exception(f"Failed to assign task: {e}")


async def handle_task_done(
    ack: Ack,
    body: dict,
    client: AsyncWebClient,
    context: AsyncBoltContext,
    logger: Logger,
):
    await ack()
    try:
        task_id = int(body["actions"][0]["value"])
        await asyncio.to_thread(complete_task, task_id)
        task = await asyncio.to_thread(get_task, task_id)
        if not task:
            return
        await _rebuild_board(client, body, task)
    except Exception as e:
        logger.exception(f"Failed to complete task: {e}")
