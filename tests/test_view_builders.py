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
    mission_block = next(b for b in modal["blocks"] if b.get("block_id") == "mission")
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


def test_build_decided_card_passed_has_no_actions():
    prospect = {
        "id": 42,
        "name": "Acme Foundation",
        "fit_rationale": "Funds youth education in CA.",
    }
    blocks = build_decided_card_blocks(prospect, ":x: *Passed*")
    assert all(b["type"] != "actions" for b in blocks)


def test_build_decided_card_approved_offers_application_help():
    prospect = {
        "id": 42,
        "name": "Acme Foundation",
        "fit_rationale": "Funds youth education in CA.",
    }
    blocks = build_decided_card_blocks(prospect, ":white_check_mark: *Approved*")
    actions_block = next(b for b in blocks if b["type"] == "actions")
    button = actions_block["elements"][0]
    assert button["action_id"] == "clew_draft_application"
    assert button["value"] == "42"


def test_channel_name_for_slugifies():
    from listeners.grant_channel import channel_name_for

    name = channel_name_for("Promise Neighborhoods (ED-GRANT-26-054 / 84.215N)")
    assert name.startswith("grant-promise-neighborhoods")
    assert len(name) <= 75
    import re

    assert re.fullmatch(r"[a-z0-9-]+", name)


def test_board_rows_link_war_room_channel():
    blocks = build_board_blocks(
        {"approved": [{"id": 1, "name": "Beta Fund", "grant_channel_id": "C123"}]}
    )
    texts = [b["text"]["text"] for b in blocks if b["type"] == "section"]
    assert any("Beta Fund" in t and "<#C123>" in t for t in texts)


def test_grant_nav_blocks_are_grant_scoped():
    from listeners.views.setup_prompt_builder import build_grant_nav_blocks

    prospect = {
        "id": 7,
        "name": "Acme Fund",
        "application_url": "https://www.grants.gov/search-results-detail/7",
        "fit_sources": '["https://example.org/source"]',
        "deadline_date": None,
    }
    blocks = build_grant_nav_blocks(prospect)
    elements = blocks[0]["elements"]
    by_action = {e["action_id"]: e for e in elements}

    # Grant-scoped buttons only — no org-wide actions in a war room.
    assert "clew_find_grants" not in by_action
    assert "clew_show_saved" not in by_action
    assert "clew_open_org_profile" not in by_action

    assert by_action["clew_draft_application"]["value"] == "7"
    assert by_action["clew_designate_tasks"]["value"] == "7"
    assert by_action["clew_show_tasks"]["value"] == "7"
    # application_url wins over fit_sources for the website button.
    assert (
        by_action["clew_open_grant_link"]["url"]
        == "https://www.grants.gov/search-results-detail/7"
    )
    # No deadline yet -> Set Deadline offered.
    assert by_action["clew_set_deadline"]["value"] == "7"


def test_grant_nav_blocks_url_fallback_and_deadline_conditional():
    from listeners.views.setup_prompt_builder import build_grant_nav_blocks

    prospect = {
        "id": 8,
        "name": "Beta Fund",
        "application_url": None,
        "fit_sources": '["https://example.org/fallback"]',
        "deadline_date": "2026-09-01",
    }
    by_action = {
        e["action_id"]: e for e in build_grant_nav_blocks(prospect)[0]["elements"]
    }
    assert by_action["clew_open_grant_link"]["url"] == "https://example.org/fallback"
    assert "clew_set_deadline" not in by_action

    # No URL anywhere and no deadline: website button omitted, deadline shown.
    bare = {"id": 9, "name": "C", "application_url": None, "fit_sources": None}
    by_action = {
        e["action_id"]: e for e in build_grant_nav_blocks(bare)[0]["elements"]
    }
    assert "clew_open_grant_link" not in by_action
    assert "clew_set_deadline" in by_action


def test_channel_canvas_id_extraction():
    from listeners.actions.draft_application_action import _channel_canvas_id

    tabs_form = {
        "properties": {
            "tabs": [
                {"type": "bookmarks", "id": "bookmarks"},
                {"type": "canvas", "data": {"file_id": "F123"}},
            ]
        }
    }
    assert _channel_canvas_id(tabs_form) == "F123"

    property_form = {"properties": {"canvas": {"file_id": "F456"}}}
    assert _channel_canvas_id(property_form) == "F456"

    assert _channel_canvas_id({"properties": {}}) is None
    assert _channel_canvas_id({}) is None


def test_channel_topic_truncates_long_grant_size():
    from listeners.grant_channel import channel_topic_for

    long_size = (
        "Not stated by source; annual revenue ~$9.8M-$39.3M (2019-2023) "
        "suggests capacity for grants across our $1,000-$500,000 range"
    )
    topic = channel_topic_for({"deadline_date": None, "grant_size": long_size})
    assert topic.startswith("📅 Due TBD · 💰 ")
    assert "…" in topic
    assert len(topic) < 100

    short = channel_topic_for(
        {"deadline_date": "2026-09-01", "grant_size": "$5k-$25k"}
    )
    assert short == "📅 Due 2026-09-01 · 💰 $5k-$25k · brief pinned"


def test_extract_text_lists_links_absolute_and_mailto():
    from agent.tools.website import _extract_text

    html = """
    <html><head><title>Bob Woodruff Foundation</title></head><body>
      <nav><a href="/our-partners/grants-for-organizations/">Grants for Organizations</a></nav>
      <p>We support <a href="https://example.org/veterans">veterans</a>.</p>
      <a href="mailto:grants@bobwoodrufffoundation.org">Email the grants team</a>
      <a href="#top">Back to top</a>
      <a href="javascript:void(0)">Menu</a>
      <script><a href="/never-seen">hidden</a></script>
    </body></html>
    """
    title, _desc, text, links = _extract_text(
        html, "https://bobwoodrufffoundation.org/home"
    )
    assert title == "Bob Woodruff Foundation"
    assert "veterans" in text
    joined = "\n".join(links)
    assert (
        "- Grants for Organizations: "
        "https://bobwoodrufffoundation.org/our-partners/grants-for-organizations/"
        in joined
    )
    assert "mailto:grants@bobwoodrufffoundation.org" in joined
    assert "#top" not in joined
    assert "javascript" not in joined
    assert "never-seen" not in joined


def test_grant_brief_renders_apply_criteria_contact_eligibility():
    from listeners.views.grant_brief_builder import build_grant_brief_blocks

    data = {
        "funder": "Bob Woodruff Foundation",
        "fit": "Direct veteran population match.",
        "amount": "$25k-$100k",
        "deadline": "Rolling",
        "apply_url": "https://bobwoodrufffoundation.my.site.com/s/",
        "criteria_url": "https://bobwoodrufffoundation.org/criteria/",
        "contact": "grants@bobwoodrufffoundation.org",
        "eligibility": ["501(c)(3) veteran-serving orgs", "National programs"],
        "eligibility_analysis": "You appear eligible: veteran-serving 501(c)(3).",
    }
    text = str(build_grant_brief_blocks(data))
    assert "https://bobwoodrufffoundation.my.site.com/s/" in text
    assert "Criteria & guidelines" in text
    assert "mailto:grants@bobwoodrufffoundation.org" in text
    assert "Who's eligible" in text
    assert "Are we eligible?" in text

    # All-optional: an old-format brief renders without the new sections.
    old = str(build_grant_brief_blocks({"funder": "X", "fit": "y"}))
    assert "Apply here" not in old
    assert "Are we eligible?" not in old


def test_grant_brief_ignores_non_http_apply_url():
    from listeners.views.grant_brief_builder import build_grant_brief_blocks

    text = str(
        build_grant_brief_blocks(
            {"funder": "X", "apply_url": "null", "criteria_url": None}
        )
    )
    assert "Apply here" not in text


def test_impact_block_computes_from_board():
    from listeners.views.app_home_builder import _impact_block

    board = {
        "qualified": [
            {"id": 1, "fit_sources": '["https://a", "https://b"]'},
        ],
        "approved": [
            {"id": 2, "fit_sources": '["https://c"]', "grant_channel_id": "C1"},
        ],
        "passed": [{"id": 3, "fit_sources": None}],
    }
    block = _impact_block(board, total_tasks=4)
    text = block["text"]["text"]
    assert "3 prospects" in text
    assert "3 citations" in text
    assert "1 war room" in text
    assert "4 tasks" in text
    assert "est." in text
    assert "~8 hours" in text  # 3 * 2.5 rounded

    assert _impact_block({"qualified": []}, total_tasks=0) is None


def test_cfemail_decode_and_extraction():
    from agent.tools.website import _decode_cfemail, _extract_text

    email = "grants@bobwoodrufffoundation.org"
    key = 0x42
    encoded = bytes([key] + [b ^ key for b in email.encode()]).hex()

    assert _decode_cfemail(encoded) == email
    assert _decode_cfemail("zz-not-hex") is None

    html = f"""
    <html><body>
      <p>Contact:
        <a href="/cdn-cgi/l/email-protection" class="__cf_email__"
           data-cfemail="{encoded}">[email&#160;protected]</a>
      </p>
    </body></html>
    """
    _t, _d, text, links = _extract_text(html, "https://example.org/")
    assert email in text
    assert f"mailto:{email}" in "\n".join(links)
    assert "email-protection" not in "\n".join(links)
