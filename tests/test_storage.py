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
