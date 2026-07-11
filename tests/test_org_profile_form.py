from datetime import date, timedelta

from listeners.views.board_builder import build_board_blocks
from listeners.views.org_profile_builder import (
    build_org_profile_modal,
    split_program_areas,
)
from listeners.views.org_profile_submission import parse_org_profile_values


def _state_values(
    selected=(),
    other="",
    grant_min="",
    grant_max="",
    mission="Serve local youth",
    geography="Oakland",
    exclusions="",
):
    return {
        "mission": {"value": {"type": "plain_text_input", "value": mission}},
        "geography": {"value": {"type": "plain_text_input", "value": geography}},
        "program_areas": {
            "value": {
                "type": "multi_static_select",
                "selected_options": [
                    {"text": {"type": "plain_text", "text": s}, "value": s}
                    for s in selected
                ],
            }
        },
        "program_areas_other": {"value": {"type": "plain_text_input", "value": other}},
        "grant_size_min": {"value": {"type": "number_input", "value": grant_min}},
        "grant_size_max": {"value": {"type": "number_input", "value": grant_max}},
        "exclusions": {"value": {"type": "plain_text_input", "value": exclusions}},
    }


def test_parse_serializes_selected_and_other_program_areas():
    fields, errors = parse_org_profile_values(
        _state_values(
            selected=["Education & Youth Development", "Arts & Culture"],
            other="digital literacy, arts & culture",
        )
    )
    assert errors == {}
    # dedupes case-insensitively against selected options
    assert fields["program_areas"] == (
        "Education & Youth Development, Arts & Culture, digital literacy"
    )


def test_parse_min_greater_than_max_returns_error():
    fields, errors = parse_org_profile_values(
        _state_values(selected=["Arts & Culture"], grant_min="50000", grant_max="5000")
    )
    assert "grant_size_max" in errors


def test_parse_requires_at_least_one_program_area():
    fields, errors = parse_org_profile_values(_state_values())
    assert "program_areas" in errors


def test_parse_grant_sizes_to_ints():
    fields, errors = parse_org_profile_values(
        _state_values(selected=["Arts & Culture"], grant_min="5000", grant_max="50000")
    )
    assert errors == {}
    assert fields["grant_size_min"] == 5000
    assert fields["grant_size_max"] == 50000


def test_split_program_areas_curated_vs_other():
    matched, leftover = split_program_areas("workforce development, youth education")
    assert matched == ["Workforce Development"]  # case-insensitive, curated spelling
    assert leftover == ["youth education"]


def test_modal_prefill_splits_curated_and_other():
    modal = build_org_profile_modal(
        {"program_areas": "Workforce Development, youth education"}
    )
    select_block = next(
        b for b in modal["blocks"] if b.get("block_id") == "program_areas"
    )
    initial = select_block["element"]["initial_options"]
    assert [o["value"] for o in initial] == ["Workforce Development"]
    other_block = next(
        b for b in modal["blocks"] if b.get("block_id") == "program_areas_other"
    )
    assert other_block["element"]["initial_value"] == "youth education"


def test_empty_profile_omits_initial_values():
    """Slack's views.open rejects empty initial_value on number_input and
    initial_options=[] on multi_static_select — the keys must be absent."""
    modal = build_org_profile_modal(None)
    for block_id in ("mission", "grant_size_min", "grant_size_max"):
        block = next(b for b in modal["blocks"] if b.get("block_id") == block_id)
        assert "initial_value" not in block["element"]
    select_block = next(
        b for b in modal["blocks"] if b.get("block_id") == "program_areas"
    )
    assert "initial_options" not in select_block["element"]


def test_board_flags_deadlines_due_within_a_week():
    soon = (date.today() + timedelta(days=3)).isoformat()
    later = (date.today() + timedelta(days=30)).isoformat()
    blocks = build_board_blocks(
        {
            "approved": [
                {"id": 1, "name": "Soon Fund", "deadline_date": soon},
                {"id": 2, "name": "Later Fund", "deadline_date": later},
            ]
        }
    )
    texts = [
        b["text"]["text"] for b in blocks if b["type"] == "section" and "text" in b
    ]
    assert any("Soon Fund" in t and "⏰" in t for t in texts)
    assert not any("Later Fund" in t and "⏰" in t for t in texts)


def test_ai_draft_group_only_on_first_setup():
    fresh = build_org_profile_modal(None)
    fresh_ids = [b.get("block_id") for b in fresh["blocks"]]
    assert "ai_website" in fresh_ids and "ai_notes" in fresh_ids

    editing = build_org_profile_modal({"mission": "Serve local youth"})
    editing_ids = [b.get("block_id") for b in editing["blocks"]]
    assert "ai_website" not in editing_ids and "ai_notes" not in editing_ids


def test_parse_draft_json_tolerates_fences_and_nulls():
    from agent.profile_draft import _parse_draft_json

    reply = """Here you go:
```json
{"mission": "We teach kids STEM.", "geography": "Oakland",
 "program_areas": "youth education, STEM",
 "grant_size_min": null, "grant_size_max": 50000, "exclusions": null}
```"""
    fields = _parse_draft_json(reply)
    assert fields["mission"] == "We teach kids STEM."
    assert fields["grant_size_max"] == 50000
    assert "grant_size_min" not in fields and "exclusions" not in fields


def test_parse_draft_json_rejects_missing_mission():
    from agent.profile_draft import _parse_draft_json

    assert _parse_draft_json('{"geography": "Oakland"}') is None
    assert _parse_draft_json("no json here") is None
