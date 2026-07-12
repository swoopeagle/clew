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


def test_org_wide_task_queries():
    from storage import (
        count_tasks_by_prospect,
        list_open_tasks_by_org,
        update_prospect,
    )

    pid = _prospect(org_id="Torg")
    update_prospect(pid, grant_channel_id="C_ROOM")
    other_org = _prospect(org_id="Tother", name="Elsewhere Fund")

    t1 = create_task(org_id="Torg", prospect_id=pid, description="Unowned work")
    t2 = create_task(
        org_id="Torg", prospect_id=pid, description="Owned work",
        assignee_user_id="U1",
    )
    done = create_task(org_id="Torg", prospect_id=pid, description="Finished")
    complete_task(done)
    create_task(org_id="Tother", prospect_id=other_org, description="Not ours")

    open_tasks = list_open_tasks_by_org("Torg")
    assert {t["id"] for t in open_tasks} == {t1, t2}
    assert all(t["prospect_name"] == "Acme Fund" for t in open_tasks)
    assert all(t["grant_channel_id"] == "C_ROOM" for t in open_tasks)

    counts = count_tasks_by_prospect("Torg")
    assert counts[pid] == {"open": 2, "done": 1}


def test_briefing_includes_task_rollup():
    from listeners.briefing import build_briefing_blocks
    from storage import update_prospect

    pid = _prospect(org_id="Trollup")
    update_prospect(pid, grant_channel_id="C_NUDGE")
    create_task(org_id="Trollup", prospect_id=pid, description="Get financials")
    create_task(
        org_id="Trollup", prospect_id=pid, description="Draft budget",
        assignee_user_id="U9",
    )

    text = str(build_briefing_blocks("Trollup"))
    assert "C_NUDGE" in text
    assert "2 tasks open" in text
    assert "1 unassigned" in text


def test_war_room_nudges_deadline_and_unassigned():
    from datetime import date, timedelta

    from listeners.briefing import build_war_room_nudges
    from storage import update_prospect

    soon = (date.today() + timedelta(days=2)).isoformat()
    pid = _prospect(org_id="Tnudge")
    update_prospect(
        pid, stage="approved", grant_channel_id="C_WAR", deadline_date=soon
    )
    create_task(org_id="Tnudge", prospect_id=pid, description="Collect 990s")
    create_task(
        org_id="Tnudge", prospect_id=pid, description="Write narrative",
        assignee_user_id="U7",
    )

    nudges = build_war_room_nudges("Tnudge")
    assert len(nudges) == 1
    channel, message = nudges[0]
    assert channel == "C_WAR"
    assert "2 day" in message
    assert "Collect 990s" in message
    assert "<@U7>" in message

    # Far deadline + fully assigned tasks -> no nudge.
    far = (date.today() + timedelta(days=30)).isoformat()
    pid2 = _prospect(org_id="Tquiet", name="Quiet Fund")
    update_prospect(
        pid2, stage="approved", grant_channel_id="C_QUIET", deadline_date=far
    )
    create_task(
        org_id="Tquiet", prospect_id=pid2, description="Owned",
        assignee_user_id="U1",
    )
    assert build_war_room_nudges("Tquiet") == []


def test_home_tasks_in_flight_line():
    from listeners.views.app_home_builder import _tasks_in_flight

    assert _tasks_in_flight([]) is None
    line = _tasks_in_flight(
        [
            {"prospect_id": 1, "grant_channel_id": "C1", "assignee_user_id": None},
            {"prospect_id": 1, "grant_channel_id": "C1", "assignee_user_id": "U1"},
            {"prospect_id": 2, "grant_channel_id": "C2", "assignee_user_id": None},
        ]
    )
    assert "3 tasks in flight" in line
    assert "2 war rooms" in line
    assert "2 unassigned" in line
