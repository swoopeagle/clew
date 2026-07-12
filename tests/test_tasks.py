"""Task designation engine: storage lifecycle, the state-driven board
builder, and the tolerant JSON parse for agent-proposed task lists."""

from listeners.views.task_board_builder import (
    build_task_board_blocks,
    parse_tasks_json,
)
from storage import (
    complete_task,
    create_task,
    get_task,
    insert_prospect,
    list_tasks,
    set_task_assignee,
)


def _prospect(org_id="T1", name="Acme Fund") -> int:
    return insert_prospect(
        org_id=org_id,
        name=name,
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://www.grants.gov/search-results-detail/1"],
    )


def test_task_lifecycle_create_assign_done():
    pid = _prospect()
    task_id = create_task(
        org_id="T1", prospect_id=pid, description="Gather audited financials"
    )
    task = get_task(task_id)
    assert task["status"] == "open"
    assert task["assignee_user_id"] is None

    set_task_assignee(task_id, "U123ABC")
    assert get_task(task_id)["assignee_user_id"] == "U123ABC"

    complete_task(task_id)
    assert get_task(task_id)["status"] == "done"


def test_list_tasks_scoped_to_prospect_open_first():
    pid = _prospect()
    other = _prospect(name="Other Fund")
    done_id = create_task(org_id="T1", prospect_id=pid, description="Old task")
    complete_task(done_id)
    create_task(org_id="T1", prospect_id=pid, description="New task")
    create_task(org_id="T1", prospect_id=other, description="Elsewhere")

    tasks = list_tasks(pid)
    assert [t["description"] for t in tasks] == ["New task", "Old task"]


def test_task_board_blocks_state_machine():
    tasks = [
        {"id": 1, "description": "Unassigned", "assignee_user_id": None, "status": "open"},
        {"id": 2, "description": "Assigned", "assignee_user_id": "U9", "status": "open"},
        {"id": 3, "description": "Finished", "assignee_user_id": "U9", "status": "done"},
    ]
    blocks = build_task_board_blocks("Acme Fund", tasks)
    by_id = {b.get("block_id"): b for b in blocks if b.get("block_id")}

    picker = by_id["clew_task_1"]["accessory"]
    assert picker["type"] == "users_select"
    assert picker["action_id"] == "clew_assign_task"

    done_btn = by_id["clew_task_2"]["accessory"]
    assert done_btn["action_id"] == "clew_task_done"
    assert done_btn["value"] == "2"

    finished = by_id["clew_task_3"]
    assert "~Finished~" in finished["text"]["text"]
    assert "accessory" not in finished


def test_task_board_empty_state():
    blocks = build_task_board_blocks("Acme Fund", [])
    assert any("No tasks yet" in str(b) for b in blocks)


def test_parse_tasks_json_tolerates_fences_and_prose():
    assert parse_tasks_json('["Draft budget", "Get 501c3 letter"]') == [
        "Draft budget",
        "Get 501c3 letter",
    ]
    assert parse_tasks_json(
        'Here you go:\n```json\n["Draft budget"]\n```\nDone!'
    ) == ["Draft budget"]
    assert parse_tasks_json("no list here") is None
    assert parse_tasks_json("") is None
    assert parse_tasks_json('["  ", ""]') is None


def test_clean_user_id_accepts_mention_forms():
    from agent.tools.tasks import _clean_user_id

    assert _clean_user_id("U0123ABC") == "U0123ABC"
    assert _clean_user_id("<@U0123ABC>") == "U0123ABC"
    assert _clean_user_id("<@U0123ABC|jay>") == "U0123ABC"
    assert _clean_user_id("not-a-user") is None
    assert _clean_user_id(None) is None
