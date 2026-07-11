from listeners.views.app_home_builder import build_app_home_view
from listeners.views.board_builder import build_board_blocks
from listeners.views.org_profile_builder import build_org_profile_modal
from listeners.views.prospect_card_builder import (
    build_decided_card_blocks,
    build_prospect_card_blocks,
)
from listeners.views.feedback_builder import build_feedback_blocks


def test_build_feedback_blocks():
    blocks = build_feedback_blocks()

    assert len(blocks) > 0
    # The block should contain a feedback action
    block_dict = blocks[0].to_dict()
    action_ids = [e["action_id"] for e in block_dict["elements"]]
    assert "feedback" in action_ids


def test_build_app_home_view_no_profile():
    """No org profile yet — shows the setup prompt and a Set Up button."""
    view = build_app_home_view()

    assert view["type"] == "home"
    block_types = [b["type"] for b in view["blocks"]]
    assert "header" in block_types
    assert "actions" in block_types

    actions_block = next(b for b in view["blocks"] if b["type"] == "actions")
    button_texts = [e["text"]["text"] for e in actions_block["elements"]]
    assert "Set Up Org Profile" in button_texts
    assert "Find Grants" in button_texts


def test_build_app_home_view_with_profile():
    """Existing org profile — shows a mission summary and an Edit button instead."""
    view = build_app_home_view(
        org_profile={"mission": "Serve local youth", "program_areas": "education"}
    )

    section_texts = [
        b["text"]["text"] for b in view["blocks"] if b["type"] == "section"
    ]
    assert any("Serve local youth" in t for t in section_texts)

    actions_block = next(b for b in view["blocks"] if b["type"] == "actions")
    button_texts = [e["text"]["text"] for e in actions_block["elements"]]
    assert "Edit Org Profile" in button_texts


def test_build_app_home_view_connected_shows_search_status():
    connected_view = build_app_home_view(is_connected=True)
    connected_text = " ".join(
        el["text"]
        for b in connected_view["blocks"]
        if b["type"] == "context"
        for el in b["elements"]
    )
    assert "connected" in connected_text.lower()

    install_view = build_app_home_view(install_url="https://example.com/slack/install")
    install_text = " ".join(
        el["text"]
        for b in install_view["blocks"]
        if b["type"] == "context"
        for el in b["elements"]
    )
    assert "https://example.com/slack/install" in install_text


def test_build_board_blocks_empty():
    blocks = build_board_blocks({})
    context_texts = [
        el["text"] for b in blocks if b["type"] == "context" for el in b["elements"]
    ]
    assert any("No prospects yet" in t for t in context_texts)


def test_build_board_blocks_groups_by_stage():
    grouped = {
        "qualified": [{"id": 1, "name": "Acme Foundation"}],
        "approved": [{"id": 2, "name": "Beta Fund", "deadline_date": "2026-08-01"}],
    }
    blocks = build_board_blocks(grouped)
    section_texts = [b["text"]["text"] for b in blocks if b["type"] == "section"]
    assert any("Acme Foundation" in t for t in section_texts)
    assert any("Beta Fund" in t and "2026-08-01" in t for t in section_texts)


def test_build_org_profile_modal_prefills_existing_values():
    modal = build_org_profile_modal(
        {"mission": "Serve local youth", "grant_size_min": 5000}
    )
    mission_block = next(
        b for b in modal["blocks"] if b.get("block_id") == "mission"
    )
    assert mission_block["element"]["initial_value"] == "Serve local youth"
    min_block = next(
        b for b in modal["blocks"] if b.get("block_id") == "grant_size_min"
    )
    assert min_block["element"]["initial_value"] == "5000"


def test_build_prospect_card_blocks_has_approve_and_pass():
    prospect = {
        "id": 42,
        "name": "Acme Foundation",
        "fit_rationale": "Funds youth education in CA.",
    }
    blocks = build_prospect_card_blocks(prospect, ["https://example.com/source"])

    actions_block = next(b for b in blocks if b["type"] == "actions")
    action_ids = [e["action_id"] for e in actions_block["elements"]]
    assert "clew_approve_prospect" in action_ids
    assert "clew_pass_prospect" in action_ids
    values = [e["value"] for e in actions_block["elements"]]
    assert values == ["42", "42"]


def test_build_decided_card_blocks_has_no_actions():
    prospect = {
        "id": 42,
        "name": "Acme Foundation",
        "fit_rationale": "Funds youth education in CA.",
    }
    blocks = build_decided_card_blocks(prospect, ":white_check_mark: *Approved*")
    assert all(b["type"] != "actions" for b in blocks)
