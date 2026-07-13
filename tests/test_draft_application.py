from unittest.mock import AsyncMock, Mock, patch

import pytest
from slack_sdk.errors import SlackApiError
from slack_sdk.web.async_client import AsyncWebClient

from listeners.actions.draft_application_action import _resolve_or_create_canvas

DOC = {"type": "markdown", "markdown": "# Application draft — X\n\nbody"}


@pytest.mark.asyncio
async def test_redraft_edits_existing_canvas_in_place():
    """A re-draft must edit the tracked canvas, never spawn a second one."""
    client = Mock(AsyncWebClient)
    user_client = Mock(AsyncWebClient)
    user_client.canvases_edit = AsyncMock()
    user_client.conversations_canvases_create = AsyncMock()
    prospect = {"id": 7, "name": "X", "canvas_id": "F_EXISTING"}

    with patch("listeners.actions.draft_application_action.update_prospect") as up:
        canvas_id = await _resolve_or_create_canvas(
            client, user_client, prospect, "C1", DOC
        )

    assert canvas_id == "F_EXISTING"
    user_client.canvases_edit.assert_awaited_once()
    user_client.conversations_canvases_create.assert_not_called()
    up.assert_not_called()


@pytest.mark.asyncio
async def test_first_draft_creates_and_persists_canvas_id():
    client = Mock(AsyncWebClient)
    user_client = Mock(AsyncWebClient)
    user_client.canvases_edit = AsyncMock()
    user_client.conversations_canvases_create = AsyncMock(
        return_value={"canvas_id": "F_NEW"}
    )
    prospect = {"id": 9, "name": "X", "canvas_id": None}

    with patch("listeners.actions.draft_application_action.update_prospect") as up:
        canvas_id = await _resolve_or_create_canvas(
            client, user_client, prospect, "C1", DOC
        )

    assert canvas_id == "F_NEW"
    user_client.conversations_canvases_create.assert_awaited_once()
    up.assert_called_once_with(9, canvas_id="F_NEW")


@pytest.mark.asyncio
async def test_deleted_stored_canvas_falls_back_to_create():
    """If the tracked canvas was deleted, mint a fresh one and re-persist."""
    client = Mock(AsyncWebClient)
    user_client = Mock(AsyncWebClient)
    user_client.canvases_edit = AsyncMock(
        side_effect=SlackApiError(
            "canvas_not_found", {"ok": False, "error": "canvas_not_found"}
        )
    )
    user_client.conversations_canvases_create = AsyncMock(
        return_value={"canvas_id": "F_FRESH"}
    )
    prospect = {"id": 3, "name": "X", "canvas_id": "F_GONE"}

    with patch("listeners.actions.draft_application_action.update_prospect") as up:
        canvas_id = await _resolve_or_create_canvas(
            client, user_client, prospect, "C1", DOC
        )

    assert canvas_id == "F_FRESH"
    user_client.conversations_canvases_create.assert_awaited_once()
    up.assert_called_once_with(3, canvas_id="F_FRESH")


@pytest.mark.asyncio
async def test_channel_canvas_already_exists_edits_and_persists():
    """When Slack DOES report an existing channel canvas, adopt and track it."""
    client = Mock(AsyncWebClient)
    client.conversations_info = AsyncMock(
        return_value={
            "channel": {"properties": {"canvas": {"file_id": "F_CHAN"}}}
        }
    )
    user_client = Mock(AsyncWebClient)
    user_client.canvases_edit = AsyncMock()
    user_client.conversations_canvases_create = AsyncMock(
        side_effect=SlackApiError(
            "exists", {"ok": False, "error": "channel_canvas_already_exists"}
        )
    )
    prospect = {"id": 5, "name": "X", "canvas_id": None}

    with patch("listeners.actions.draft_application_action.update_prospect") as up:
        canvas_id = await _resolve_or_create_canvas(
            client, user_client, prospect, "C1", DOC
        )

    assert canvas_id == "F_CHAN"
    user_client.canvases_edit.assert_awaited_once()
    up.assert_called_once_with(5, canvas_id="F_CHAN")
