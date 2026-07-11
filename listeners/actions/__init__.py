from slack_bolt.async_app import AsyncApp

from .draft_application_action import handle_draft_application
from .feedback_buttons import handle_feedback_button
from .find_grants_action import handle_find_grants
from .org_profile_actions import handle_ai_draft_profile, handle_open_org_profile
from .saved_grants_action import handle_show_saved
from .prospect_actions import (
    handle_approve_prospect,
    handle_mark_applied,
    handle_mark_awarded,
    handle_mark_declined,
    handle_mark_reported,
    handle_mark_submitted,
    handle_pass_prospect,
    handle_refresh_home,
)


def register(app: AsyncApp):
    app.action("feedback")(handle_feedback_button)
    app.action("clew_open_org_profile")(handle_open_org_profile)
    app.action("clew_ai_draft_profile")(handle_ai_draft_profile)
    app.action("clew_show_saved")(handle_show_saved)
    app.action("clew_draft_application")(handle_draft_application)
    app.action("clew_find_grants")(handle_find_grants)
    app.action("clew_approve_prospect")(handle_approve_prospect)
    app.action("clew_pass_prospect")(handle_pass_prospect)
    app.action("clew_mark_applied")(handle_mark_applied)
    app.action("clew_mark_submitted")(handle_mark_submitted)
    app.action("clew_mark_awarded")(handle_mark_awarded)
    app.action("clew_mark_declined")(handle_mark_declined)
    app.action("clew_mark_reported")(handle_mark_reported)
    app.action("clew_refresh_home")(handle_refresh_home)
