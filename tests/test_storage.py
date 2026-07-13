from storage import (
    claim_prospect_stage,
    get_org_profile,
    get_prospect,
    get_prospects_grouped_by_stage,
    insert_prospect,
    update_prospect,
    upsert_org_profile,
)


def test_claim_prospect_stage_is_single_winner():
    """A double-clicked Approve must only fire once: the first claim wins, the
    second sees the row already past 'qualified' and returns False."""
    prospect_id = insert_prospect(
        org_id="T1",
        name="Acme Foundation",
        source="propublica",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://projects.propublica.org/nonprofits/organizations/1"],
    )

    assert claim_prospect_stage(prospect_id, "qualified", "approved") is True
    assert get_prospect(prospect_id)["stage"] == "approved"
    # Second click: already approved, so no re-claim (no duplicate war room).
    assert claim_prospect_stage(prospect_id, "qualified", "approved") is False


def test_org_profile_roundtrip():
    assert get_org_profile("T1") is None

    upsert_org_profile(
        org_id="T1",
        mission="Serve local youth",
        geography="Bay Area",
        program_areas="education",
        grant_size_min=5000,
        grant_size_max=50000,
        exclusions=None,
    )
    profile = get_org_profile("T1")
    assert profile["mission"] == "Serve local youth"
    assert profile["grant_size_max"] == 50000

    # Upsert again should update, not duplicate.
    upsert_org_profile(
        org_id="T1",
        mission="Serve local youth and families",
        geography="Bay Area",
        program_areas="education",
        grant_size_min=5000,
        grant_size_max=50000,
        exclusions=None,
    )
    assert get_org_profile("T1")["mission"] == "Serve local youth and families"


def test_insert_and_advance_prospect_stage():
    prospect_id = insert_prospect(
        org_id="T1",
        name="Acme Foundation",
        source="propublica",
        source_ref="12-3456789",
        program_area="education",
        geography="CA",
        grant_size="$10,000-$25,000",
        fit_rationale="Funds youth education in the Bay Area per its 990 filings.",
        fit_sources=[
            "https://projects.propublica.org/nonprofits/organizations/123456789"
        ],
    )
    prospect = get_prospect(prospect_id)
    assert prospect["stage"] == "qualified"
    assert (
        prospect["fit_sources"]
        == '["https://projects.propublica.org/nonprofits/organizations/123456789"]'
    )

    update_prospect(prospect_id, stage="approved", deadline_date="2026-08-01")
    prospect = get_prospect(prospect_id)
    assert prospect["stage"] == "approved"
    assert prospect["deadline_date"] == "2026-08-01"


def test_get_prospects_grouped_by_stage():
    insert_prospect(
        org_id="T1",
        name="A",
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://example.com"],
    )
    p2 = insert_prospect(
        org_id="T1",
        name="B",
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://example.com"],
    )
    update_prospect(p2, stage="passed")

    grouped = get_prospects_grouped_by_stage("T1")
    assert len(grouped["qualified"]) == 1
    assert len(grouped["passed"]) == 1
    assert grouped["qualified"][0]["name"] == "A"


def test_prospects_scoped_by_org():
    insert_prospect(
        org_id="T1",
        name="A",
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=[],
    )
    insert_prospect(
        org_id="T2",
        name="B",
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=[],
    )
    t1_board = get_prospects_grouped_by_stage("T1")
    assert len(t1_board["qualified"]) == 1
    assert t1_board["qualified"][0]["name"] == "A"


def test_insert_prospect_captures_deadline_and_application_url():
    prospect_id = insert_prospect(
        org_id="T1",
        name="Rural Health Grant",
        source="grants_gov",
        source_ref="OPP-123",
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://www.grants.gov/search-results-detail/123"],
        deadline_date="2026-09-30",
        application_url="https://www.grants.gov/search-results-detail/123",
    )
    prospect = get_prospect(prospect_id)
    assert prospect["deadline_date"] == "2026-09-30"
    assert (
        prospect["application_url"]
        == "https://www.grants.gov/search-results-detail/123"
    )

    # Both stay optional — the pre-existing call shape must keep working.
    bare_id = insert_prospect(
        org_id="T1",
        name="No Deadline Fund",
        source="propublica",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="fits",
        fit_sources=["https://projects.propublica.org/nonprofits/organizations/9"],
    )
    bare = get_prospect(bare_id)
    assert bare["deadline_date"] is None
    assert bare["application_url"] is None


def test_iso_date_normalizes_grants_gov_format():
    from agent.tools.qualify import _iso_date

    assert _iso_date("2026-01-31") == "2026-01-31"
    assert _iso_date("01/31/2026") == "2026-01-31"
    assert _iso_date("  09/05/2026 ") == "2026-09-05"
    assert _iso_date("Fall 2026") is None
    assert _iso_date("") is None
    assert _iso_date(None) is None


def test_brief_deadline_backfill_accepts_only_real_dates():
    from listeners.grant_channel import _valid_iso_date

    assert _valid_iso_date("2026-08-01") == "2026-08-01"
    assert _valid_iso_date(" 2026-08-01 ") == "2026-08-01"
    assert _valid_iso_date(None) is None
    assert _valid_iso_date("Verify on the funder's site") is None
    assert _valid_iso_date(20260801) is None


def test_reset_org_wipes_profile_and_prospects():
    from storage import (
        get_org_profile,
        get_prospects_grouped_by_stage,
        insert_prospect,
        reset_org,
        update_prospect,
        upsert_org_profile,
    )

    upsert_org_profile(
        org_id="Treset",
        mission="m",
        geography="g",
        program_areas="a",
        grant_size_min=None,
        grant_size_max=None,
        exclusions=None,
    )
    pid = insert_prospect(
        org_id="Treset",
        name="Wipe Me Fund",
        source="grants_gov",
        source_ref=None,
        program_area=None,
        geography=None,
        grant_size=None,
        fit_rationale="r",
        fit_sources=["https://www.grants.gov/x"],
    )
    update_prospect(pid, grant_channel_id="C_WARROOM")

    result = reset_org("Treset")
    assert result["prospect_count"] == 1
    assert result["grant_channel_ids"] == ["C_WARROOM"]
    assert get_org_profile("Treset") is None
    grouped = get_prospects_grouped_by_stage("Treset")
    assert all(not rows for rows in grouped.values())


def test_agent_sessions_persist_and_expire():
    from storage import get_agent_session, set_agent_session

    set_agent_session("D123", "111.222", "sess-abc")
    assert get_agent_session("D123", "111.222", ttl_seconds=3600) == "sess-abc"
    assert get_agent_session("D123", "999.000", ttl_seconds=3600) is None

    # Upsert replaces.
    set_agent_session("D123", "111.222", "sess-def")
    assert get_agent_session("D123", "111.222", ttl_seconds=3600) == "sess-def"

    # TTL: a zero-second TTL treats everything as expired (and purges).
    assert get_agent_session("D123", "111.222", ttl_seconds=-1) is None
    assert get_agent_session("D123", "111.222", ttl_seconds=3600) is None


def test_session_store_survives_process_restart():
    """The bug Ian hit: in-memory sessions were wiped by every deploy. The
    store is now DB-backed, so a brand-new instance (a 'new process') sees
    sessions written by the old one."""
    from thread_context.store import SessionStore

    old_process = SessionStore()
    old_process.set_session("D42", "123.456", "sess-live")

    new_process = SessionStore()  # fresh cache, same database
    assert new_process.get_session("D42", "123.456") == "sess-live"
    assert new_process.get_session("D42", "does-not-exist") is None
