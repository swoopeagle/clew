import asyncio

from storage import get_org_profile


async def prepend_org_profile(text: str, org_id: str) -> str:
    """Prepend the org's profile (if set up) to a user message so the agent
    has mission/geography/program-area/grant-size context without the user
    repeating it every time."""
    profile = await asyncio.to_thread(get_org_profile, org_id)
    if not profile:
        return text

    grant_range = ""
    if profile.get("grant_size_min") or profile.get("grant_size_max"):
        grant_range = f"${profile.get('grant_size_min') or 0:,}-${profile.get('grant_size_max') or 0:,}"

    profile_block = (
        "[ORG PROFILE — use this to screen fit]\n"
        f"Mission: {profile.get('mission') or 'n/a'}\n"
        f"Geography: {profile.get('geography') or 'n/a'}\n"
        f"Program areas: {profile.get('program_areas') or 'n/a'}\n"
        f"Grant size range: {grant_range or 'n/a'}\n"
        f"Exclusions: {profile.get('exclusions') or 'none'}\n"
        "[END ORG PROFILE]\n\n"
    )
    return profile_block + text
